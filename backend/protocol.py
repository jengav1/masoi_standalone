# games/masoi_activity/protocol.py
"""
Lọc và sinh snapshot bảo mật riêng biệt theo viewer (Mục 13.2).
Đảm bảo:
- Người xem chỉ nhận thông tin vai trò của chính mình hoặc đồng đội theo luật.
- Dân Làng không nhận tin chat/mục tiêu của Sói.
- Phe khác không thấy kết quả soi của Tiên tri hoặc mục tiêu bảo vệ của Bảo vệ.
- Khi người chơi bị loại (chết), vai trò chỉ hiện nếu cài đặt cho phép (mặc định ẩn vai khi chết).
"""
from typing import Dict, Any, List, Optional
from .roles import ROLE_REGISTRY

def build_private_snapshot(room_data: Dict[str, Any], viewer_uid: int) -> Dict[str, Any]:
    phase = room_data.get("phase", "LOBBY")
    round_id = room_data.get("round_id", 1)
    day_number = room_data.get("day_number", 1)
    night_subphase = room_data.get("night_subphase", "")
    deadline_at = room_data.get("deadline_at", 0)
    server_time = room_data.get("server_time", 0)
    mayor_id = room_data.get("mayor_id")
    host_id = room_data.get("host_id")
    winner_team = room_data.get("winner_team")
    game_over = room_data.get("game_over", False)
    hide_role_on_death = room_data.get("settings", {}).get("hide_role_on_death", True)

    players = room_data.get("players", {})
    viewer = players.get(viewer_uid, {})
    viewer_role = viewer.get("role_id")
    viewer_alive = viewer.get("alive", True)
    viewer_team = viewer.get("team")
    is_spectator = (viewer_uid not in players)

    # 1. Danh sách ghế công khai cho mọi người
    public_seats = []
    for uid, p in players.items():
        role_to_show = None
        # Chỉ hiển thị role công khai nếu game kết thúc HOẶC (người đó chết và không ẩn role)
        if game_over:
            role_to_show = p.get("role_id")
        elif not p.get("alive", True) and not hide_role_on_death:
            role_to_show = p.get("role_id")
        
        # Nếu viewer là Sói và người kia cũng là Sói (đồng đội)
        is_teammate = False
        if viewer_team == "werewolf" and p.get("team") == "werewolf":
            is_teammate = True
            if not role_to_show:
                role_to_show = p.get("role_id")

        seat_info = {
            "uid": uid,
            "name": p.get("name", "Người chơi"),
            "avatar_url": p.get("avatar_url"),
            "seat_index": p.get("seat_index", 0),
            "ready": p.get("ready", False),
            "alive": p.get("alive", True),
            "is_mayor": (uid == mayor_id),
            "is_host": (uid == host_id),
            "public_role": role_to_show,
            "is_teammate": is_teammate,
            "death_reason": p.get("death_reason") if not p.get("alive") else None,
        }
        public_seats.append(seat_info)

    # Sắp xếp theo seat_index
    public_seats.sort(key=lambda s: s["seat_index"])

    # 2. Thông tin riêng tư của người xem (My Role & Actions)
    my_info = {
        "uid": viewer_uid,
        "is_spectator": is_spectator,
        "is_host": (viewer_uid == host_id),
        "ready": viewer.get("ready", False),
        "alive": viewer_alive,
        "role_id": viewer_role,
        "team": viewer_team,
        "lover_id": viewer.get("lover_id"),
        "role_data": {},
        "available_actions": []
    }

    if viewer_role and viewer_role in ROLE_REGISTRY:
        r_def = ROLE_REGISTRY[viewer_role]
        my_info["role_name"] = r_def.name
        my_info["role_emoji"] = r_def.emoji
        my_info["role_desc"] = r_def.description

    # Cấp dữ liệu riêng theo vai trò & pha chơi
    if phase == "NIGHT" and viewer_alive:
        # A. Lượt Sói
        if night_subphase == "WEREWOLF" and viewer_team == "werewolf":
            my_info["available_actions"].append("wolf_vote")
            my_info["role_data"]["wolf_votes"] = room_data.get("wolf_votes", {})
            my_info["role_data"]["wolf_targets"] = [
                s["uid"] for s in public_seats if s["alive"] and s.get("team") != "werewolf"
            ]

        # B. Lượt Tiên Tri
        elif night_subphase == "SEER" and viewer_role == "seer":
            my_info["available_actions"].append("seer_inspect")
            my_info["role_data"]["last_inspect"] = viewer.get("last_inspect")
            my_info["role_data"]["valid_targets"] = [
                s["uid"] for s in public_seats if s["alive"] and s["uid"] != viewer_uid
            ]

        # C. Lượt Bảo Vệ
        elif night_subphase == "GUARD" and viewer_role == "guard":
            my_info["available_actions"].append("guard_protect")
            last_protected = viewer.get("last_protected")
            my_info["role_data"]["last_protected"] = last_protected
            my_info["role_data"]["valid_targets"] = [
                s["uid"] for s in public_seats if s["alive"] and s["uid"] != last_protected
            ]

        # D. Lượt Phù Thủy
        elif night_subphase == "WITCH" and viewer_role == "witch":
            has_heal = viewer.get("has_heal_potion", True)
            has_poison = viewer.get("has_poison_potion", True)
            victim_id = room_data.get("night_victim_id")
            
            my_info["role_data"]["has_heal"] = has_heal
            my_info["role_data"]["has_poison"] = has_poison
            my_info["role_data"]["night_victim"] = victim_id if has_heal else None
            
            if has_heal and victim_id:
                my_info["available_actions"].append("witch_heal")
            if has_poison:
                my_info["available_actions"].append("witch_poison")
                my_info["role_data"]["poison_targets"] = [
                    s["uid"] for s in public_seats if s["alive"]
                ]

    # Pha Ban Ngày (Bầu Trưởng Làng hoặc Bỏ Phiếu Treo Cổ)
    elif phase in ("DAY_VOTE", "MAYOR_ELECTION") and viewer_alive:
        my_info["available_actions"].append("vote")
        my_info["role_data"]["my_vote"] = room_data.get("votes", {}).get(viewer_uid)
        my_info["role_data"]["vote_targets"] = [
            s["uid"] for s in public_seats if s["alive"]
        ]

    # Pha Thợ Săn phản ứng bắn
    elif phase == "HUNTER_REACTION" and viewer_role == "hunter" and not viewer_alive and not viewer.get("hunter_fired"):
        my_info["available_actions"].append("hunter_shoot")
        my_info["role_data"]["valid_targets"] = [
            s["uid"] for s in public_seats if s["alive"]
        ]

    # Lọc danh sách tin nhắn chat theo quyền hạn
    chat_history = []
    for msg in room_data.get("chat_messages", []):
        ch = msg.get("channel", "village")
        if ch == "village":
            chat_history.append(msg)
        elif ch == "wolves" and viewer_team == "werewolf":
            chat_history.append(msg)
        elif ch == "dead" and not viewer_alive:
            chat_history.append(msg)
        elif ch == "lovers" and viewer_uid in (viewer.get("lover_id"), msg.get("sender_uid")):
            chat_history.append(msg)

    # Tổng kết snapshot
    return {
        "room_id": room_data.get("room_id"),
        "phase": phase,
        "day_number": day_number,
        "night_subphase": night_subphase,
        "deadline_at": deadline_at,
        "server_time": server_time,
        "seats": public_seats,
        "me": my_info,
        "deck_preset": room_data.get("deck", []),
        "settings": room_data.get("settings", {}),
        "chat": chat_history[-50:], # Giữ tối đa 50 tin nhắn gần nhất
        "game_over": game_over,
        "winner_team": winner_team,
        "recap_events": room_data.get("recap_events", [])
    }
