# Ma Sói Discord Activity — Tài Liệu Tương Thích Luật Chơi & Cơ Chế Agrou

Tài liệu này đặc tả toàn bộ quy tắc, cơ chế chia vai, thứ tự hành động và bảo mật thông tin trong bản Rebuild Ma Sói Discord Activity (Làng Sương Mù Agrou) của dự án CRAZY GAME.

---

## 1. Vai trò (Roles) & Thứ tự Đêm (Night Priority)

Hệ thống hỗ trợ từ 4 đến 12 người chơi với các vai trò chuẩn hóa theo Agrou:

| Role ID | Tên Vai Trò | Phe (Team) | Độ Ưu Tiên Đêm | Hành Động |
|---|---|---|---|---|
| `cupid` | Thần Tình Yêu (Cupid) | Neutral / Lovers | 10 (Chỉ đêm 1) | Ghép đôi 2 người chơi thành Cặp Đôi (Lovers). Khi 1 người chết, người kia chết theo. |
| `guard` | Bảo Vệ (Guard) | Dân Làng | 20 (Mỗi đêm) | Chọn 1 người bảo vệ khỏi cú cắn của Sói. **Không thể bảo vệ cùng 1 người 2 đêm liên tiếp**. |
| `werewolf` | Ma Sói | Ma Sói | 30 (Mỗi đêm) | Thảo luận qua Hang Sói bí mật và bỏ phiếu cắn 1 nạn nhân. |
| `white_wolf` | Sói Trắng | Solo Sói Trắng | 35 (Đêm chẵn) | Cùng thức với bầy sói, và được thức riêng vào đêm chẵn để tiêu diệt 1 con sói khác. |
| `witch` | Phù Thủy (Witch) | Dân Làng | 40 (Mỗi đêm) | Có 1 bình Cứu (`heal_pot`) và 1 bình Độc (`kill_pot`). Biết ai bị cắn để quyết định cứu hoặc đầu độc thêm 1 người. |
| `seer` | Tiên Tri (Seer) | Dân Làng | 50 (Mỗi đêm) | Soi 1 người chơi để biết chính xác người đó là Sói (`werewolf`) hay Dân (`villager`). |
| `hunter` | Thợ Săn (Hunter) | Dân Làng | Phản ứng khi chết | Khi bị treo cổ hoặc bị cắn chết, được kích hoạt phát súng ân huệ để kéo 1 người khác chết cùng. |
| `villager` | Dân Làng (Villager) | Dân Làng | Không thức đêm | Dùng tài lập luận và phiếu biểu quyết ban ngày để tìm sói. |

---

## 2. Preset Cấu Hình Bàn Chơi (4 – 12 Người)

Hệ thống tự động kích hoạt preset cân bằng theo số lượng người tham gia trong phòng:

- **4 người**: 1 Ma Sói, 1 Tiên Tri, 2 Dân Làng
- **5 người**: 1 Ma Sói, 1 Tiên Tri, 1 Bảo Vệ, 2 Dân Làng
- **6 người**: 2 Ma Sói, 1 Tiên Tri, 1 Bảo Vệ, 2 Dân Làng
- **7 người**: 2 Ma Sói, 1 Tiên Tri, 1 Bảo Vệ, 1 Phù Thủy, 2 Dân Làng
- **8 người**: 2 Ma Sói, 1 Tiên Tri, 1 Bảo Vệ, 1 Phù Thủy, 1 Thợ Săn, 2 Dân Làng
- **9 người**: 2 Ma Sói, 1 Tiên Tri, 1 Bảo Vệ, 1 Phù Thủy, 1 Thợ Săn, 1 Thần Tình Yêu, 2 Dân Làng
- **10 người**: 3 Ma Sói, 1 Tiên Tri, 1 Bảo Vệ, 1 Phù Thủy, 1 Thợ Săn, 1 Thần Tình Yêu, 2 Dân Làng
- **11 người**: 3 Ma Sói, 1 Tiên Tri, 1 Bảo Vệ, 1 Phù Thủy, 1 Thợ Săn, 1 Thần Tình Yêu, 3 Dân Làng
- **12 người**: 3 Ma Sói, 1 Sói Trắng, 1 Tiên Tri, 1 Bảo Vệ, 1 Phù Thủy, 1 Thợ Săn, 1 Thần Tình Yêu, 3 Dân Làng

---

## 3. Quy Tắc Biểu Quyết & Trưởng Làng (Mayor / Village Chief)

1. **Bầu Trưởng Làng (Mayor)**:
   - Được tiến hành vào Ban Ngày đợt 1 trước khi bước vào biểu quyết treo cổ.
   - Phiếu của Trưởng Làng có trọng số **2.0 điểm** khi biểu quyết ban ngày (`vote_weight = 2.0`).
   - Nếu Trưởng Làng chết, Trưởng Làng được chọn truyền lại Vương Miện 👑 cho một người còn sống khác trước khi nhắm mắt.
2. **Xử lý Hòa Phiếu (Tie Breaking)**:
   - Nếu số phiếu cao nhất bằng nhau, Trưởng Làng sẽ có quyền quyết định tối hậu. Nếu không có Trưởng Làng hoặc phiếu trắng thắng thế, ngày hôm đó làng không treo cổ ai.
3. **Phiếu Trắng (Skip Vote)**:
   - Người chơi có thể bấm vào đống lửa trại trung tâm (`🏳️ Phiếu trắng`) nếu chưa có đủ chứng cứ kết tội.

---

## 4. Bảo Mật State & Quyền Snapshot (ACL Filtering)

Để chống tuyệt đối hiện tượng soi Network Inspect / F12 hoặc sửa CSS để gian lận:
1. **Server-side authority**: Toàn bộ logic ván đấu, phân vai, mục tiêu cắn, bình thuốc phù thủy, kết quả soi của tiên tri chỉ nằm trên RAM máy chủ Python.
2. **Snapshot lọc theo UID người xem**:
   - `me.role_name`, `me.role_emoji`, `me.role_desc` chỉ được gửi cho chính chủ sở hữu.
   - Mọi người chơi khác chỉ thấy `role: "SECRET"` hoặc chỉ thấy vai công khai khi đã chết (`public_role`).
   - Kênh chat `wolves` (Hang Sói) và danh sách đồng bọn sói chỉ được gửi trong snapshot của người chơi thuộc phe Sói. Dân Làng không hề nhận được dữ liệu tin nhắn sói qua WebSocket.
