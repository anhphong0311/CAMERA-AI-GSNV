# User Manual — AEMS v1.0.0

## Overview

AEMS giám sát hành vi nhân viên qua camera, phát hiện vi phạm (dùng điện thoại, ngủ, ăn...) và gửi cảnh báo.

## Login

1. Mở trình duyệt → `https://your-domain`
2. Nhập username/password
3. Chọn vai trò phù hợp (Viewer/Supervisor)

## Dashboard Pages

| Page | Mô tả |
|------|-------|
| Overview | Tổng quan camera, cảnh báo hôm nay |
| Live Camera | Xem stream + detection overlay |
| Live Detection | Bounding boxes realtime |
| Tracking | Track IDs và ROI |
| Alerts | Danh sách sự kiện vi phạm |
| Rules | Xem/quản lý quy tắc (Supervisor+) |
| ROI | Vùng giám sát |
| Statistics | Thống kê theo thời gian |
| Reports | Báo cáo xuất file |

## Xem cảnh báo

1. Vào **Alerts**
2. Click event để xem snapshot
3. Supervisor có thể xác nhận/từ chối event

## FAQ

**Q: Tại sao camera offline?**  
A: Kiểm tra RTSP URL, mạng, và log camera worker.

**Q: Không nhận Telegram?**  
A: Kiểm tra bot token và chat ID trong cấu hình admin.

**Q: Dashboard không cập nhật realtime?**  
A: Kiểm tra WebSocket (icon kết nối góc màn hình), refresh trang.

## Support

Xem [Troubleshooting Guide](../deployment/Troubleshooting-Guide.md)
