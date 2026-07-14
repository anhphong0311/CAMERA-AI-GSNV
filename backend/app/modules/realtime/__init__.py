"""
Realtime module (Sprint 8) — WebSocket hub + broadcaster cho Dashboard.

Chỉ chịu trách nhiệm phát dữ liệu realtime (detection/tracking/alert/system)
tới các client Dashboard. KHÔNG xử lý AI/Rule; chỉ đọc trạng thái từ các service
đã có (Sprint 1-7) và/hoặc phát dữ liệu demo khi chưa có luồng camera thật.
"""
