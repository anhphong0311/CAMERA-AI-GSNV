# FAQ — AEMS v1.0.0

**Q: Hệ thống hỗ trợ bao nhiêu camera?**  
A: Khuyến nghị ≤20 camera/GPU. Với CPU-only, ≤5 camera.

**Q: Có cần GPU không?**  
A: Không bắt buộc. GPU tăng FPS đáng kể. CPU fallback hoạt động.

**Q: Làm sao thêm rule mới?**  
A: Sửa `config/rules.yaml` hoặc API `POST /api/v1/rules`.

**Q: Telegram không gửi được?**  
A: Kiểm tra `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, và `enabled=true` trong config.

**Q: Làm sao reset password admin?**  
A: Sửa `ADMIN_PASSWORD` trong `.env.production` và restart backend, hoặc dùng admin API.

**Q: Database migration lỗi?**  
A: `docker compose exec backend alembic upgrade head` — xem log chi tiết.

**Q: WebSocket không kết nối?**  
A: Frontend phải dùng `wss://` khi HTTPS. Kiểm tra nginx WebSocket proxy.

**Q: License?**  
A: MIT — xem [LICENSE](../../LICENSE)

**Q: Lộ trình v2.0?**  
A: Xem [Project-Summary.md](Project-Summary.md)
