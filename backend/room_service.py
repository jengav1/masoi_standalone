# games/masoi_activity/room_service.py
"""
Room Service quản lý các phòng Ma Sói (Mục 11, 12, 14).
Mỗi phòng độc lập theo guild_id / channel_id.
"""
from typing import Dict, Optional, List
import time
from .engine import WerewolfGameEngine

class MasoiRoomService:
    def __init__(self):
        self.rooms: Dict[str, WerewolfGameEngine] = {}

    def get_or_create_room(self, room_id: str, host_uid: int, channel_id: int, guild_id: int, on_broadcast=None) -> WerewolfGameEngine:
        if room_id in self.rooms:
            engine = self.rooms[room_id]
            # Nếu phòng cũ đã kết thúc thì có thể tái khởi động hoặc cấp phòng mới
            return engine

        engine = WerewolfGameEngine(
            room_id=room_id,
            host_uid=host_uid,
            channel_id=channel_id,
            guild_id=guild_id,
            on_state_change=on_broadcast
        )
        self.rooms[room_id] = engine
        return engine

    def get_room_by_id(self, room_id: str) -> Optional[WerewolfGameEngine]:
        return self.rooms.get(room_id)

    def find_room_for_user(self, channel_id: int, guild_id: int, uid: int) -> Optional[WerewolfGameEngine]:
        # 1. Tìm phòng trong cùng voice channel mà user đã vào
        for r in self.rooms.values():
            if r.channel_id == channel_id and r.guild_id == guild_id and uid in r.players:
                return r
        # 2. Tìm phòng đang mở trong cùng voice channel
        for r in self.rooms.values():
            if r.channel_id == channel_id and r.guild_id == guild_id and not r.game_over:
                return r
        # 3. Fallback: phòng đang mở gần nhất
        active = [r for r in self.rooms.values() if not r.game_over]
        return active[0] if active else None

    def clean_empty_rooms(self):
        now = time.time()
        to_del = []
        for rid, r in self.rooms.items():
            if r.game_over and r.deadline_at and (now - r.deadline_at > 3600):
                to_del.append(rid)
        for rid in to_del:
            self.rooms.pop(rid, None)
