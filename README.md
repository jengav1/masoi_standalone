# 🐺 Ma Sói (Werewolf) - Standalone Repository

Dự án game **Ma Sói (Werewolf)** độc lập dành cho Discord, bao gồm:
1. **Discord Activity (Làng Sương Mù - Agrou Style)**: Chơi trực tiếp trong giao diện tương tác iframe Discord Activity (vòng lửa trại, thời gian thực bằng WebSocket, âm thanh, hiệu ứng ngày/đêm).
2. **Chế độ Bot Kinh Điển (Classic Text Embeds)**: Chơi qua tin nhắn Discord Embed và các tương tác Button/Select Component.

---

## 📁 Cấu Trúc Thư Mục

```text
masoi_standalone/
├── backend/                  # Logic game phía máy chủ
│   ├── engine.py             # Máy trạng thái (FSM) vòng lặp ngày/đêm, xử lý kỹ năng vai trò
│   ├── roles.py              # Định nghĩa vai trò (Dân Làng, Sói, Tiên Tri, Bảo Vệ, Phù Thủy, Thợ Săn...)
│   ├── rules.py              # Luật chơi, kiểm tra điều kiện thắng (Phe Sói vs Phe Làng)
│   ├── protocol.py           # Bộ mã hóa/giải mã Snapshot trạng thái cho từng người chơi
│   ├── server.py             # WebSocket server & xác thực Discord OAuth2 token
│   ├── room_service.py       # Quản lý vòng đời phòng chơi theo Channel/Guild
│   ├── classic.py            # Chế độ Ma Sói dạng Text Embed truyền thống
│   └── cog.py                # Discord Cog điều phối lệnh /masoi
├── frontend/                 # Giao diện Discord Activity
│   ├── src/
│   │   ├── ui.js             # Logic render vòng lửa trại, hiệu ứng, âm thanh, WebSocket client
│   │   └── masoi.css         # Styling giao diện Làng Sương Mù Agrou
│   └── assets/               # Tài nguyên đồ họa (village-day.jpg, village-night.jpg, emoji.ttf)
├── docs/                     # Tài liệu thiết kế & đặc tả
│   ├── agrou-compatibility.md # So sánh tương thích Agrou
│   ├── deployment.md          # Hướng dẫn deploy Discord Activity lên Cloudflare/VPS
│   └── preview-reference.html # Bản preview HTML minh họa
├── config.py                 # File cấu hình Token & Client ID
├── run_bot.py                # File khởi chạy Bot & Activity Server độc lập
└── requirements.txt          # Thư viện Python cần thiết
```

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy

### 1. Cài đặt thư viện
```bash
pip install -r requirements.txt
```

### 2. Cấu hình Bot Discord
Chỉnh sửa file `config.py` hoặc thiết lập các biến môi trường:
- `DISCORD_BOT_TOKEN`: Token của bot Discord (bật đầy đủ Privileged Gateway Intents).
- `DISCORD_CLIENT_ID`: Application ID của Discord App.
- `DISCORD_CLIENT_SECRET`: Client Secret từ Discord Developer Portal (phục vụ OAuth2 Activity).
- `PORT`: Cổng Web Server (mặc định: `31378`).

### 3. Chạy Bot
```bash
python run_bot.py
```

### 4. Sử dụng lệnh
Trong server Discord, gõ lệnh:
- `/masoi` -> Chọn chế độ **Làng Sương Mù (Discord Activity)** hoặc **Giao diện Text Embed (Bot thường)**.
