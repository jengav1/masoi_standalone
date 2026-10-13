# games/masoi_activity/rules.py
"""
Quy tắc kiểm tra thắng, kiểm tra bộ bài (Preset validation) và tính toán phiếu vote (Mục 6, 8)
"""
from typing import Dict, List, Tuple, Set, Optional
from .roles import ROLE_REGISTRY, RoleDefinition

DEFAULT_PRESETS: Dict[int, List[str]] = {
    2: ["werewolf", "seer"],
    3: ["werewolf", "villager", "seer"],
    4: ["werewolf", "villager", "villager", "seer"],
    5: ["werewolf", "villager", "villager", "seer", "guard"],
    6: ["werewolf", "villager", "villager", "seer", "guard", "witch"],
    7: ["werewolf", "werewolf", "villager", "villager", "seer", "guard", "witch"],
    8: ["werewolf", "werewolf", "villager", "villager", "seer", "guard", "witch", "hunter"],
    9: ["werewolf", "werewolf", "villager", "villager", "villager", "seer", "guard", "witch", "hunter"],
    10: ["werewolf", "werewolf", "werewolf", "villager", "villager", "villager", "seer", "guard", "witch", "hunter"],
    11: ["werewolf", "werewolf", "werewolf", "villager", "villager", "villager", "villager", "seer", "guard", "witch", "hunter"],
    12: ["werewolf", "werewolf", "werewolf", "villager", "villager", "villager", "villager", "villager", "seer", "guard", "witch", "hunter"],
}

def validate_deck(player_count: int, deck: List[str]) -> Tuple[bool, str]:
    if len(deck) != player_count:
        return False, f"Số lá bài ({len(deck)}) phải bằng số người chơi ({player_count})."
    
    counts: Dict[str, int] = {}
    for r in deck:
        if r not in ROLE_REGISTRY:
            return False, f"Vai trò '{r}' không hợp lệ."
        counts[r] = counts.get(r, 0) + 1
        limit = ROLE_REGISTRY[r].max_count
        if counts[r] > limit:
            return False, f"Vai trò '{ROLE_REGISTRY[r].name}' tối đa là {limit} người."

    has_wolf = any(ROLE_REGISTRY[r].team in ("werewolf", "neutral") for r in deck)
    has_village = any(ROLE_REGISTRY[r].team == "village" for r in deck)

    if not has_wolf or not has_village:
        return False, "Bộ bài phải có ít nhất 1 phe Sói và 1 phe Dân Làng."

    return True, ""

class WinEvaluator:
    @staticmethod
    def evaluate(alive_players: List[Dict]) -> Tuple[bool, Optional[str], str]:
        """
        Kiểm tra điều kiện thắng:
        alive_players: danh sách dict gồm {'uid', 'role_id', 'team', 'lovers'}
        Trả về: (game_over: bool, winning_team: str, reason: str)
        """
        if not alive_players:
            return True, "draw", "Tất cả mọi người đều đã chết. Hòa cờ!"

        # Kiểm tra phe Người Yêu (Lovers Win) nếu 2 người yêu khác phe còn sống sót cùng nhau
        lover_pairs = set()
        for p in alive_players:
            lover_id = p.get("lover_id")
            if lover_id:
                pair = tuple(sorted([p["uid"], lover_id]))
                lover_pairs.add(pair)
        
        # Nếu chỉ còn đúng 2 người và họ là cặp đôi yêu nhau
        if len(alive_players) == 2 and len(lover_pairs) == 1:
            return True, "lovers", "Cặp đôi tình nhân đã sống sót tới cuối cùng và chiến thắng!"

        # Đếm số lượng theo phe
        wolf_count = sum(1 for p in alive_players if p.get("team") == "werewolf")
        village_count = sum(1 for p in alive_players if p.get("team") == "village")
        white_wolf_count = sum(1 for p in alive_players if p.get("role_id") == "white_wolf")

        # 1. Phe Sói Trắng độc hành
        if white_wolf_count > 0 and len(alive_players) == 1:
            return True, "white_wolf", "Sói Trắng là kẻ sống sót duy nhất và chiến thắng!"

        # 2. Hết Sói -> Phe Dân Làng Thắng
        if wolf_count == 0 and white_wolf_count == 0:
            return True, "village", "Toàn bộ Ma Sói đã bị tiêu diệt! Dân Làng chiến thắng!"

        # 3. Số Sói >= Số Dân -> Phe Sói Thắng
        if wolf_count >= village_count and white_wolf_count == 0:
            return True, "werewolf", "Số lượng Ma Sói đã áp đảo người dân! Phe Ma Sói chiến thắng!"

        return False, None, ""
