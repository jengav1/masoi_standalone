# games/masoi_activity/engine.py
"""
Engine State Machine xử lý chu kỳ ngày đêm, thu thập hành động, giải quyết chuỗi chết và điều kiện thắng (Mục 6, 11).
"""
import asyncio
import random
import time
from typing import Dict, Any, List, Optional, Set, Tuple
from .roles import ROLE_REGISTRY, get_role_def
from .rules import WinEvaluator, DEFAULT_PRESETS, validate_deck

class WerewolfGameEngine:
    def __init__(self, room_id: str, host_uid: int, channel_id: int, guild_id: int, on_state_change=None):
        self.room_id = room_id
        self.host_id = host_uid
        self.channel_id = channel_id
        self.guild_id = guild_id
        self.on_state_change = on_state_change # callback thông báo broadcast

        self.phase = "LOBBY" # LOBBY, ROLE_REVEAL, NIGHT, DAY_DISCUSSION, DAY_VOTE, MAYOR_ELECTION, HUNTER_REACTION, FINISHED
        self.night_subphase = "" # SEER, GUARD, WEREWOLF, WITCH
        self.day_number = 1
        self.round_id = 1
        self.deadline_at = 0
        self.game_over = False
        self.winner_team = None
        self.mayor_id: Optional[int] = None

        self.players: Dict[int, Dict[str, Any]] = {} # uid -> player state
        self.deck: List[str] = DEFAULT_PRESETS.get(8, [])
        self.settings = {
            "discussion_time": 90,
            "vote_time": 45,
            "night_action_time": 30,
            "hide_role_on_death": True
        }

        # Lưu trữ hành động tạm thời trong đêm
        self.night_protected_uid: Optional[int] = None
        self.wolf_votes: Dict[int, int] = {} # wolf_uid -> target_uid
        self.night_victim_id: Optional[int] = None
        self.witch_healed = False
        self.witch_poisoned_uid: Optional[int] = None

        # Lưu trữ phiếu ban ngày
        self.votes: Dict[int, Optional[int]] = {} # voter_uid -> target_uid (None = phiếu trắng)
        
        self.chat_messages: List[Dict[str, Any]] = []
        self.recap_events: List[str] = []
        self.timer_task: Optional[asyncio.Task] = None
        self.action_lock = asyncio.Lock()

    def add_player(self, uid: int, name: str, avatar_url: str) -> bool:
        if self.phase != "LOBBY":
            return False # Đang chơi thì vào làm khán giả
        if uid in self.players:
            return True
        if len(self.players) >= 12:
            return False

        seat_index = len(self.players)
        self.players[uid] = {
            "uid": uid,
            "name": name,
            "avatar_url": avatar_url,
            "seat_index": seat_index,
            "ready": (uid == self.host_id), # Host mặc định sẵn sàng
            "alive": True,
            "role_id": None,
            "team": None,
            "has_heal_potion": True,
            "has_poison_potion": True,
            "last_protected": None,
            "last_inspect": None,
            "hunter_fired": False,
            "death_reason": None
        }
        return True

    def remove_player(self, uid: int):
        if self.phase == "LOBBY" and uid in self.players:
            del self.players[uid]
            # Sắp xếp lại seat index
            for idx, p in enumerate(sorted(self.players.values(), key=lambda x: x["seat_index"])):
                p["seat_index"] = idx
            if uid == self.host_id and self.players:
                self.host_id = next(iter(self.players.keys()))

    def set_ready(self, uid: int, ready: bool):
        if self.phase == "LOBBY" and uid in self.players:
            self.players[uid]["ready"] = ready

    def start_game(self) -> bool:
        if self.phase != "LOBBY":
            return False
        n = len(self.players)
        if n < 2 or n > 12:
            return False
        
        # Lấy bộ bài tương ứng nếu chưa chỉnh
        if len(self.deck) != n:
            self.deck = list(DEFAULT_PRESETS.get(n, DEFAULT_PRESETS.get(4, [])))

        valid, _ = validate_deck(n, self.deck)
        if not valid:
            return False

        # Phân vai ngẫu nhiên
        shuffled_deck = list(self.deck)
        random.shuffle(shuffled_deck)
        
        for idx, p in enumerate(self.players.values()):
            r_id = shuffled_deck[idx]
            r_def = get_role_def(r_id)
            p["role_id"] = r_id
            p["team"] = r_def.team if r_def else "village"
            p["alive"] = True
            p["ready"] = True

        self.phase = "ROLE_REVEAL"
        self.day_number = 1
        self.game_over = False
        self.winner_team = None
        self.recap_events = [f"Ván chơi bắt đầu với {n} người tham gia."]
        self._set_timer(8, self._start_first_phase)
        return True

    def _set_timer(self, seconds: int, callback):
        if self.timer_task and not self.timer_task.done():
            self.timer_task.cancel()
        self.deadline_at = time.time() + seconds

        async def timer_coro():
            await asyncio.sleep(seconds)
            await callback()

        self.timer_task = asyncio.create_task(timer_coro())

    async def _start_first_phase(self):
        # Bắt đầu đêm 1
        await self._start_night()

    async def _start_night(self):
        self.phase = "NIGHT"
        self.night_protected_uid = None
        self.wolf_votes.clear()
        self.night_victim_id = None
        self.witch_healed = False
        self.witch_poisoned_uid = None

        self.recap_events.append(f"--- Đêm thứ {self.day_number} buông xuống ---")
        await self._next_night_subphase()

    async def _next_night_subphase(self):
        # Thứ tự các vai ban đêm: Seer -> Guard -> Werewolf -> Witch
        subphases = ["SEER", "GUARD", "WEREWOLF", "WITCH"]
        curr_idx = -1
        if self.night_subphase in subphases:
            curr_idx = subphases.index(self.night_subphase)

        next_idx = curr_idx + 1
        while next_idx < len(subphases):
            cand = subphases[next_idx]
            # Kiểm tra xem vai trò này còn ai sống không
            if self._has_active_role(cand):
                self.night_subphase = cand
                t = self.settings.get("night_action_time", 25)
                self._set_timer(t, self._on_night_subphase_timeout)
                if self.on_state_change:
                    await self.on_state_change(self)
                return
            next_idx += 1

        # Nếu đã hết các lượt ban đêm -> Giải quyết bình minh
        self.night_subphase = ""
        await self._resolve_dawn()

    def _has_active_role(self, subphase: str) -> bool:
        if subphase == "SEER":
            return any(p["alive"] and p["role_id"] == "seer" for p in self.players.values())
        elif subphase == "GUARD":
            return any(p["alive"] and p["role_id"] == "guard" for p in self.players.values())
        elif subphase == "WEREWOLF":
            return any(p["alive"] and p["team"] == "werewolf" for p in self.players.values())
        elif subphase == "WITCH":
            return any(p["alive"] and p["role_id"] == "witch" for p in self.players.values())
        return False

    async def _on_night_subphase_timeout(self):
        # Hết giờ cho lượt đêm hiện tại -> Chuyển sang lượt tiếp theo
        if self.night_subphase == "WEREWOLF":
            # Tally phiếu của Sói
            if self.wolf_votes:
                counts: Dict[int, int] = {}
                for tgt in self.wolf_votes.values():
                    counts[tgt] = counts.get(tgt, 0) + 1
                # Lấy người có nhiều phiếu nhất
                max_v = max(counts.values())
                cands = [tgt for tgt, v in counts.items() if v == max_v]
                self.night_victim_id = random.choice(cands)
            else:
                self.night_victim_id = None

        await self._next_night_subphase()

    async def _resolve_dawn(self):
        # Giải quyết các mục tiêu chết đêm qua
        dead_tonight: Set[int] = set()

        # 1. Nạn nhân của Sói
        if self.night_victim_id:
            # Kiểm tra xem có được Bảo vệ hay Cứu bởi Phù thủy không
            if self.night_victim_id == self.night_protected_uid:
                pass # Được bảo vệ
            elif self.witch_healed:
                pass # Được phù thủy cứu
            else:
                dead_tonight.add(self.night_victim_id)

        # 2. Thuốc độc của Phù thủy
        if self.witch_poisoned_uid:
            dead_tonight.add(self.witch_poisoned_uid)

        # Xử lý cái chết
        dead_names = []
        for uid in dead_tonight:
            if uid in self.players:
                self.players[uid]["alive"] = False
                self.players[uid]["death_reason"] = "Bị giết trong đêm"
                dead_names.append(self.players[uid]["name"])

        if dead_names:
            self.recap_events.append(f"Trời sáng. Đêm qua, {', '.join(dead_names)} đã qua đời!")
        else:
            self.recap_events.append("Trời sáng. Một đêm yên bình, không ai phải chết!")

        # Kiểm tra điều kiện thắng
        if await self._check_win_condition():
            return

        # Kiểm tra nếu Thợ Săn chết trong đêm
        hunter_dead = [p for p in self.players.values() if p["role_id"] == "hunter" and not p["alive"] and not p["hunter_fired"]]
        if hunter_dead:
            await self._trigger_hunter_reaction()
            return

        # Chuyển sang Ban Ngày Thảo Luận
        await self._start_day_discussion()

    async def _start_day_discussion(self):
        self.phase = "DAY_DISCUSSION"
        t = self.settings.get("discussion_time", 60)
        self._set_timer(t, self._start_day_vote)
        if self.on_state_change:
            await self.on_state_change(self)

    async def _start_day_vote(self):
        self.phase = "DAY_VOTE"
        self.votes.clear()
        t = self.settings.get("vote_time", 40)
        self._set_timer(t, self._resolve_day_vote)
        if self.on_state_change:
            await self.on_state_change(self)

    async def _resolve_day_vote(self):
        # Tally phiếu bầu treo cổ
        counts: Dict[Optional[int], int] = {}
        for voter_uid, tgt in self.votes.items():
            weight = 2 if voter_uid == self.mayor_id else 1
            counts[tgt] = counts.get(tgt, 0) + weight

        # Tìm người bị loại (loại bỏ phiếu trắng None)
        target_counts = {tgt: cnt for tgt, cnt in counts.items() if tgt is not None}

        if target_counts:
            max_v = max(target_counts.values())
            cands = [tgt for tgt, cnt in target_counts.items() if cnt == max_v]
            if len(cands) == 1:
                eliminated_uid = cands[0]
                self.players[eliminated_uid]["alive"] = False
                self.players[eliminated_uid]["death_reason"] = "Bị dân làng treo cổ"
                self.recap_events.append(f"Dân làng đã bỏ phiếu xử tử {self.players[eliminated_uid]['name']}!")

                # Kiểm tra Thợ Săn
                if self.players[eliminated_uid]["role_id"] == "hunter" and not self.players[eliminated_uid]["hunter_fired"]:
                    await self._trigger_hunter_reaction()
                    return
            else:
                self.recap_events.append("Số phiếu bị hòa! Không ai bị xử tử trong ngày hôm nay.")
        else:
            self.recap_events.append("Đa số phiếu trắng. Không ai bị xử tử hôm nay.")

        if await self._check_win_condition():
            return

        # Bắt đầu đêm tiếp theo
        self.day_number += 1
        await self._start_night()

    async def _trigger_hunter_reaction(self):
        self.phase = "HUNTER_REACTION"
        self._set_timer(20, self._on_hunter_timeout)
        if self.on_state_change:
            await self.on_state_change(self)

    async def _on_hunter_timeout(self):
        # Nếu thợ săn không bắn kịp thì tiếp tục
        for p in self.players.values():
            if p["role_id"] == "hunter" and not p["alive"]:
                p["hunter_fired"] = True
        
        if await self._check_win_condition():
            return
        
        if self.phase == "HUNTER_REACTION":
            self.day_number += 1
            await self._start_night()

    async def _check_win_condition(self) -> bool:
        alive_players = [p for p in self.players.values() if p["alive"]]
        over, team, reason = WinEvaluator.evaluate(alive_players)
        if over:
            self.game_over = True
            self.winner_team = team
            self.phase = "FINISHED"
            self.recap_events.append(f"KẾT THÚC: {reason}")
            if self.timer_task and not self.timer_task.done():
                self.timer_task.cancel()
            if self.on_state_change:
                await self.on_state_change(self)
            return True
        return False

    # Xử lý các hành động từ người chơi
    async def handle_action(self, uid: int, action: Dict[str, Any]) -> Tuple[bool, str]:
        async with self.action_lock:
            kind = action.get("kind")
            p = self.players.get(uid)
            if not p:
                return False, "Bạn không có trong phòng."

            if kind == "ready":
                if self.phase != "LOBBY":
                    return False, "Ván đã bắt đầu."
                self.set_ready(uid, bool(action.get("ready")))
                return True, "OK"

            if kind == "start":
                if uid != self.host_id:
                    return False, "Chỉ chủ phòng mới được bắt đầu."
                success = self.start_game()
                return (True, "OK") if success else (False, "Chưa đủ người hoặc bộ bài không hợp lệ.")

            if kind == "seer_inspect":
                if self.phase != "NIGHT" or self.night_subphase != "SEER":
                    return False, "Chưa đến lượt Tiên Tri."
                if p["role_id"] != "seer" or not p["alive"]:
                    return False, "Không có quyền Tiên Tri."
                target_uid = action.get("target_id")
                tgt = self.players.get(target_uid)
                if not tgt or not tgt["alive"]:
                    return False, "Mục tiêu không hợp lệ."
                p["last_inspect"] = {
                    "uid": target_uid,
                    "name": tgt["name"],
                    "role_id": tgt["role_id"]
                }
                self.recap_events.append("Tiên Tri đã thực hiện soi bài bí mật.")
                return True, "OK"

            if kind == "guard_protect":
                if self.phase != "NIGHT" or self.night_subphase != "GUARD":
                    return False, "Chưa đến lượt Bảo Vệ."
                if p["role_id"] != "guard" or not p["alive"]:
                    return False, "Không có quyền Bảo Vệ."
                target_uid = action.get("target_id")
                if target_uid == p.get("last_protected"):
                    return False, "Không được bảo vệ 1 người 2 đêm liên tiếp."
                self.night_protected_uid = target_uid
                p["last_protected"] = target_uid
                return True, "OK"

            if kind == "wolf_vote":
                if self.phase != "NIGHT" or self.night_subphase != "WEREWOLF":
                    return False, "Chưa đến lượt Ma Sói."
                if p["team"] != "werewolf" or not p["alive"]:
                    return False, "Không phải Ma Sói."
                target_uid = action.get("target_id")
                self.wolf_votes[uid] = target_uid
                return True, "OK"

            if kind == "witch_action":
                if self.phase != "NIGHT" or self.night_subphase != "WITCH":
                    return False, "Chưa đến lượt Phù Thủy."
                if p["role_id"] != "witch" or not p["alive"]:
                    return False, "Không phải Phù Thủy."
                if action.get("heal") and p.get("has_heal_potion"):
                    self.witch_healed = True
                    p["has_heal_potion"] = False
                if action.get("poison_target") and p.get("has_poison_potion"):
                    self.witch_poisoned_uid = action.get("poison_target")
                    p["has_poison_potion"] = False
                return True, "OK"

            if kind == "vote":
                if self.phase not in ("DAY_VOTE", "MAYOR_ELECTION"):
                    return False, "Chưa tới giờ bỏ phiếu."
                if not p["alive"]:
                    return False, "Người chết không được bỏ phiếu."
                target_uid = action.get("target_id") # None là phiếu trắng
                self.votes[uid] = target_uid
                return True, "OK"

            if kind == "hunter_shoot":
                if self.phase != "HUNTER_REACTION" or p["role_id"] != "hunter" or p.get("hunter_fired"):
                    return False, "Không có quyền bắn."
                target_uid = action.get("target_id")
                tgt = self.players.get(target_uid)
                if not tgt or not tgt["alive"]:
                    return False, "Mục tiêu không hợp lệ."
                p["hunter_fired"] = True
                tgt["alive"] = False
                tgt["death_reason"] = f"Bị Thợ Săn {p['name']} bắn hạ trước khi chết"
                self.recap_events.append(f"Thợ Săn {p['name']} nổ súng bắn hạ {tgt['name']}!")
                await self._check_win_condition()
                return True, "OK"

            if kind == "chat":
                text = str(action.get("text", "")).strip()
                channel = action.get("channel", "village")
                if not text:
                    return False, "Nội dung trống."
                # Kiểm tra quyền kênh chat
                if channel == "wolves" and p["team"] != "werewolf":
                    return False, "Không có quyền gửi vào Hang Sói."
                if channel == "village" and not p["alive"]:
                    return False, "Người chết không được nói chuyện với làng."
                
                msg = {
                    "sender_uid": uid,
                    "sender_name": p["name"],
                    "sender_avatar": p["avatar_url"],
                    "channel": channel,
                    "text": text[:160],
                    "time": time.time()
                }
                self.chat_messages.append(msg)
                return True, "OK"

            return False, "Hành động không xác định."
