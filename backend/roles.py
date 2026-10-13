# games/masoi_activity/roles.py
"""
Hệ thống Role Registry và logic vai trò Ma Sói theo Agrou (Mục 6 & 7).
Hỗ trợ:
- Villager (Dân làng)
- Werewolf (Sói thường)
- Seer (Tiên tri)
- Guard (Bảo vệ)
- Witch (Phù thủy - Thuốc cứu, thuốc độc)
- Hunter (Thợ săn - Bắn khi chết)
- Mayor (Trưởng làng - chức danh bổ sung, phiếu x2)
- Mở rộng: Cupid (Ghép đôi), Crow/Quạ (Thêm phiếu), White Wolf (Sói trắng)
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

@dataclass
class RoleDefinition:
    id: str
    name: str
    team: str # "village", "werewolf", "neutral"
    emoji: str
    description: str
    night_order: int # Thứ tự thức dậy ban đêm (-1 nếu không có lượt đêm)
    wake_frequency: str = "every_night" # "every_night", "first_night", "none"
    max_count: int = 4
    can_target_self: bool = False

ROLE_REGISTRY: Dict[str, RoleDefinition] = {
    "villager": RoleDefinition(
        id="villager",
        name="Dân Làng",
        team="village",
        emoji="👨‍🌾",
        description="Không có năng lực ban đêm. Ban ngày suy luận và bỏ phiếu tìm kẻ ác.",
        night_order=-1,
        wake_frequency="none",
        max_count=8
    ),
    "werewolf": RoleDefinition(
        id="werewolf",
        name="Ma Sói",
        team="werewolf",
        emoji="🐺",
        description="Mỗi đêm cùng đàn thức dậy chọn 1 nạn nhân để cắn xé.",
        night_order=30,
        wake_frequency="every_night",
        max_count=4
    ),
    "seer": RoleDefinition(
        id="seer",
        name="Tiên Tri",
        team="village",
        emoji="🔮",
        description="Mỗi đêm được soi danh tính/vai trò thật của 1 người chơi.",
        night_order=10,
        wake_frequency="every_night",
        max_count=1
    ),
    "guard": RoleDefinition(
        id="guard",
        name="Bảo Vệ",
        team="village",
        emoji="🛡️",
        description="Mỗi đêm chọn bảo vệ 1 người không bị Sói giết. Không bảo vệ cùng 1 người 2 đêm liên tiếp.",
        night_order=20,
        wake_frequency="every_night",
        max_count=1,
        can_target_self=True
    ),
    "witch": RoleDefinition(
        id="witch",
        name="Phù Thủy",
        team="village",
        emoji="🧙‍♀️",
        description="Có 1 bình thuốc cứu và 1 bình thuốc độc dùng trong cả ván.",
        night_order=40,
        wake_frequency="every_night",
        max_count=1,
        can_target_self=True
    ),
    "hunter": RoleDefinition(
        id="hunter",
        name="Thợ Săn",
        team="village",
        emoji="🔫",
        description="Khi chết (bị treo cổ hoặc cắn), được bắn hạ thêm 1 người bất kỳ.",
        night_order=-1,
        wake_frequency="none",
        max_count=1
    ),
    "cupid": RoleDefinition(
        id="cupid",
        name="Thần Tình Yêu",
        team="village",
        emoji="💘",
        description="Đêm đầu tiên ghép đôi 2 người. Nếu 1 người chết, người kia chết theo.",
        night_order=5,
        wake_frequency="first_night",
        max_count=1
    ),
    "white_wolf": RoleDefinition(
        id="white_wolf",
        name="Sói Trắng",
        team="neutral",
        emoji="🐺❄️",
        description="Thức dậy cùng đàn Sói, nhưng cứ 2 đêm lại được thức riêng giết 1 con Sói khác. Thắng khi là kẻ duy nhất sống sót.",
        night_order=35,
        wake_frequency="every_other_night",
        max_count=1
    ),
}

def get_role_def(role_id: str) -> Optional[RoleDefinition]:
    return ROLE_REGISTRY.get(role_id)
