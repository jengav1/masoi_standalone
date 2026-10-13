# games/masoi_activity/server.py
"""
WebSocket & API Handler phục vụ Ma Sói Discord Activity (Mục 11, 12, 13).
Tích hợp xác thực OAuth2 Discord, quản lý kết nối WebSocket và phát Snapshot riêng biệt cho từng người chơi.
"""
import asyncio
import json
import logging
import os
import secrets
import time
from typing import Dict, Set
import httpx
from aiohttp import web

import config
from .room_service import MasoiRoomService
from .protocol import build_private_snapshot

log = logging.getLogger("masoi_activity")
API = "https://discord.com/api/v10"

class MasoiActivityServer:
    def __init__(self, bot):
        self.bot = bot
        self.client_id = os.getenv("DISCORD_CLIENT_ID") or getattr(config, "DISCORD_CLIENT_ID", "")
        self.client_secret = os.getenv("DISCORD_CLIENT_SECRET") or getattr(config, "DISCORD_CLIENT_SECRET", "")
        self.bot_token = os.getenv("DISCORD_BOT_TOKEN") or getattr(config, "TOKEN", "")
        
        self.room_service = MasoiRoomService()
        self.http = httpx.AsyncClient(timeout=12)
        self.sessions: Dict[str, Dict] = {} # session_token -> {uid, name, avatar, instance_id, channel_id, guild_id, expires}
        self.sockets: Dict[str, Set[web.WebSocketResponse]] = {} # room_id -> set(ws)
        self.ws_to_user: Dict[web.WebSocketResponse, int] = {} # ws -> uid

    async def handle_config(self, request: web.Request) -> web.Response:
        return web.json_response({"client_id": self.client_id, "game": "masoi"})

    async def handle_token(self, request: web.Request) -> web.Response:
        try:
            body = await request.json()
            code = body.get("code")
            instance_id = body.get("instance_id")
            print(f"🐺 [handle_token] Got code: {bool(code)}, instance_id: {instance_id}")

            if not code:
                return web.json_response({"error": "Thiếu authorization code"}, status=400)

            # Đổi code lấy token OAuth2
            payload = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "authorization_code",
                "code": code
            }
            res = await self.http.post(f"{API}/oauth2/token", data=payload)
            if res.status_code != 200:
                print(f"❌ [handle_token] OAuth token exchange error {res.status_code}: {res.text}")
                return web.json_response({"error": f"Xác thực Discord thất bại ({res.status_code}): {res.text}"}, status=401)

            oauth_data = res.json()
            access_token = oauth_data["access_token"]

            # Lấy thông tin user @me
            user_res = await self.http.get(f"{API}/users/@me", headers={"Authorization": f"Bearer {access_token}"})
            if user_res.status_code != 200:
                print(f"❌ [handle_token] @me failed {user_res.status_code}: {user_res.text}")
                return web.json_response({"error": "Không lấy được thông tin tài khoản"}, status=401)

            user_data = user_res.json()
            uid = int(user_data["id"])
            username = user_data.get("global_name") or user_data.get("username")
            avatar_hash = user_data.get("avatar")
            avatar_url = f"https://cdn.discordapp.com/avatars/{uid}/{avatar_hash}.png" if avatar_hash else "https://cdn.discordapp.com/embed/avatars/0.png"

            # Xác định location (channel_id, guild_id)
            channel_id = 0
            guild_id = 0
            if instance_id:
                try:
                    inst_res = await self.http.get(
                        f"{API}/applications/{self.client_id}/activity-instances/{instance_id}",
                        headers={"Authorization": f"Bot {self.bot_token}"}
                    )
                    if inst_res.status_code == 200:
                        loc = inst_res.json().get("location", {})
                        channel_id = int(loc.get("channel_id", 0))
                        guild_id = int(loc.get("guild_id", 0))
                except Exception as ex:
                    print(f"⚠️ [handle_token] activity-instance error: {ex}")

            # Cấp session token bảo mật
            session_token = secrets.token_urlsafe(32)
            self.sessions[session_token] = {
                "uid": uid,
                "name": username,
                "avatar_url": avatar_url,
                "channel_id": channel_id,
                "guild_id": guild_id,
                "expires": time.time() + 3600
            }
            print(f"✅ [handle_token] Issued session_token for user {username} ({uid})")

            return web.json_response({
                "access_token": access_token,
                "session_token": session_token,
                "uid": uid,
                "name": username,
                "avatar_url": avatar_url
            })
        except Exception as e:
            print(f"❌ [handle_token] Exception: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def handle_ws(self, request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        print("🐺 [handle_ws] WebSocket client prepared successfully")

        authenticated_uid = None
        current_room_id = None

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    kind = data.get("kind")

                    # Bước 1: Xác thực socket qua session_token
                    if "session_token" in data:
                        st = data["session_token"]
                        sess = self.sessions.get(st)
                        if not sess or sess["expires"] < time.time():
                            print(f"⚠️ [handle_ws] Unknown or expired session_token: {st[:8] if st else 'None'}. Generating auto session...")
                            # Tự động tạo session tạm thời để người chơi không bị crash/reconnect loop
                            fake_uid = int(str(abs(hash(st)))[:14]) if st else secrets.randbelow(1000000)
                            sess = {
                                "uid": fake_uid,
                                "name": f"Khách {fake_uid % 1000}",
                                "avatar_url": "https://cdn.discordapp.com/embed/avatars/0.png",
                                "channel_id": 0,
                                "guild_id": 0,
                                "is_guest": True,
                                "expires": time.time() + 86400
                            }
                            self.sessions[st] = sess

                        authenticated_uid = sess["uid"]
                        self.ws_to_user[ws] = authenticated_uid
                        print(f"✅ [handle_ws] Authenticated socket for uid: {authenticated_uid} ({sess['name']})")

                        # Tìm hoặc ghép vào phòng Ma Sói tương ứng
                        engine = self.room_service.find_room_for_user(sess["channel_id"], sess["guild_id"], authenticated_uid)
                        if not engine:
                            # Tự tạo phòng mới nếu chưa có
                            room_id = f"masoi_{sess['channel_id'] or secrets.token_hex(4)}"
                            engine = self.room_service.get_or_create_room(
                                room_id=room_id,
                                host_uid=authenticated_uid,
                                channel_id=sess["channel_id"],
                                guild_id=sess["guild_id"],
                                on_broadcast=self.broadcast_room_state
                            )

                        current_room_id = engine.room_id
                        if current_room_id not in self.sockets:
                            self.sockets[current_room_id] = set()
                        self.sockets[current_room_id].add(ws)

                        # Đưa người chơi vào phòng
                        engine.add_player(authenticated_uid, sess["name"], sess["avatar_url"])

                        # Nếu tài khoản thật (có avatar / tên thật discord) vào phòng mà host hiện tại là guest ảo thì chuyển quyền host cho tài khoản thật
                        if sess.get("channel_id") or not sess["name"].startswith("Người chơi "):
                            current_host_p = engine.players.get(engine.host_id)
                            if not current_host_p or current_host_p["name"].startswith("Người chơi "):
                                engine.host_id = authenticated_uid
                                if authenticated_uid in engine.players:
                                    engine.players[authenticated_uid]["ready"] = True
                                print(f"👑 [handle_ws] Assigned room host to real user: {sess['name']} ({authenticated_uid})")

                        # Gửi snapshot riêng đầu tiên
                        snap = build_private_snapshot(self._extract_room_data(engine), authenticated_uid)
                        await ws.send_json({"type": "state", "state": snap})
                        await self.broadcast_room_state(engine)
                        continue

                    # Bước 2: Xử lý các hành động trong game
                    if authenticated_uid and current_room_id:
                        engine = self.room_service.get_room_by_id(current_room_id)
                        if engine:
                            if kind == "ping":
                                await ws.send_json({"type": "pong"})
                            else:
                                success, msg_text = await engine.handle_action(authenticated_uid, data)
                                if not success:
                                    await ws.send_json({"type": "error", "message": msg_text})
                                else:
                                    await self.broadcast_room_state(engine)
        except Exception as e:
            log.error("WebSocket runtime error for user %s: %s", authenticated_uid, e, exc_info=True)
        finally:
            if current_room_id:
                if ws in self.sockets.get(current_room_id, set()):
                    self.sockets[current_room_id].discard(ws)
                if authenticated_uid:
                    eng = self.room_service.get_room_by_id(current_room_id)
                    if eng and eng.phase == "LOBBY":
                        # Nếu người chơi rớt mạng hoặc là ghost player tạm thời thì dọn khỏi phòng
                        eng.remove_player(authenticated_uid)
                        await self.broadcast_room_state(eng)
            self.ws_to_user.pop(ws, None)

        return ws

    async def broadcast_room_state(self, engine):
        room_id = engine.room_id
        sockets = list(self.sockets.get(room_id, []))
        if not sockets:
            return

        room_data = self._extract_room_data(engine)
        for ws in sockets:
            if ws.closed:
                continue
            uid = self.ws_to_user.get(ws, 0)
            snapshot = build_private_snapshot(room_data, uid)
            try:
                await ws.send_json({"type": "state", "state": snapshot})
            except Exception as e:
                log.warning("Broadcast socket send error: %s", e)

    def _extract_room_data(self, engine) -> Dict:
        return {
            "room_id": engine.room_id,
            "host_id": engine.host_id,
            "phase": engine.phase,
            "night_subphase": engine.night_subphase,
            "day_number": engine.day_number,
            "round_id": engine.round_id,
            "deadline_at": engine.deadline_at,
            "server_time": time.time(),
            "game_over": engine.game_over,
            "winner_team": engine.winner_team,
            "mayor_id": engine.mayor_id,
            "players": engine.players,
            "deck": engine.deck,
            "settings": engine.settings,
            "votes": engine.votes,
            "wolf_votes": engine.wolf_votes,
            "night_victim_id": engine.night_victim_id,
            "chat_messages": engine.chat_messages,
            "recap_events": engine.recap_events
        }
