# Hướng Dẫn Vận Hành & Triển Khai Ma Sói Discord Activity

Tài liệu hướng dẫn cấu hình biến môi trường, khởi chạy và liên kết Ma Sói Activity lên Discord Developer Portal.

---

## 1. Cấu Hình Biến Môi Trường (`.env` hoặc `config.py`)

Đảm bảo các biến sau được thiết lập đầy đủ trong môi trường triển khai hoặc file `config.py`:

```env
# Discord Bot & Activity Credentials
DISCORD_CLIENT_ID=your_discord_client_id
DISCORD_CLIENT_SECRET=your_discord_client_secret
DISCORD_BOT_TOKEN=your_bot_token
TOKEN=your_bot_token

# Cổng Web & Activity Proxy
VPS_PORT=31378
TL_PORT=8000
ACTIVITY_URL_BASE=https://your-domain-or-proxy.com
```

---

## 2. Cấu Hình Discord Developer Portal (Embedded App SDK)

1. Truy cập [Discord Developer Portal](https://discord.com/developers/applications) > Chọn Application của bạn.
2. Vào mục **Activities**:
   - Bật tính năng **Activity**.
   - URL Mapping:
     - Thêm map prefix `/.proxy/` trỏ về domain máy chủ của bạn (ví dụ: `https://crazy-game.your-domain.com`).
     - Trang chính: `https://crazy-game.your-domain.com/` (hoặc `/.proxy/index.html`).
3. Vào mục **OAuth2**:
   - Thêm Redirect URI: `https://crazy-game.your-domain.com/` (hoặc URL proxy activity của Discord).
   - Scopes cần thiết: `identify`, `rpc.activities.write`.

---

## 3. Khởi Chạy Hệ Thống

1. **Build Frontend**:
   ```bash
   cd frontend
   npm run build
   ```
   Lệnh này tạo thư mục `frontend/dist/` chứa toàn bộ code Vite bundle và thư mục `dist/masoi/` chứa ảnh nền làng sương mù ngày/đêm cùng font emoji.

2. **Khởi động Bot**:
   ```bash
   python main.py
   ```
   Bot sẽ đồng thời:
   - Khởi động Discord Bot và đăng ký Slash Command `/masoi`.
   - Mở Web Server AioHTTP trên cổng `31378`.
   - Phục vụ Web frontend tại `/`, `/masoi`, `/tienlen`.
   - Xử lý các API `/api/masoi/config`, `/api/masoi/token`, `/api/masoi/ws` và proxy các kết nối Tiến Lên tới `TL_PORT`.

---

## 4. Trải Nghiệm Trong Kênh Discord

1. Gõ lệnh `/masoi` trong bất kỳ kênh text hoặc voice nào của server Discord.
2. Bot phản hồi embed kèm nút **🎮 Mở Ma Sói Activity**.
3. Người chơi (từ 4 đến 12 người) bấm nút để mở Activity, tự động xác thực OAuth2 identify và ngồi vào ghế quanh đống lửa trại.
4. Chủ phòng bấm **Bắt đầu ván** khi mọi người đã sẵn sàng!
