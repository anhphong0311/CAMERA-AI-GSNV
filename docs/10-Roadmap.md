# 10 — Roadmap

**Cách tiếp cận:** phát triển theo phase, mỗi phase có mục tiêu đo lường được, ưu tiên đưa "1 camera + 1 rule end-to-end" chạy sớm (walking skeleton), sau đó mở rộng.

---

## 1. Tổng quan phase

```mermaid
timeline
    title Lộ trình AEMS
    Phase 0 - Foundation : Repo, CI, Docker, DB skeleton
    Phase 1 - Vertical Slice : 1 cam RTSP → YOLO → 1 rule → alert Telegram
    Phase 2 - AI Core : Pose, ByteTrack, ROI, temporal
    Phase 3 - Rule Engine : 7 hành vi + hot-reload + shadow
    Phase 4 - Backend/API : CRUD, auth, evidence, performance
    Phase 5 - Dashboard : Live, alerts, timeline, replay, charts
    Phase 6 - Scale/Perf : Multi-cam, TensorRT, tuning FP
    Phase 7 - Hardening : Security, DR, docs, UAT
```

---

## 2. Gantt

```mermaid
gantt
    dateFormat  YYYY-MM-DD
    title AEMS Delivery Plan
    section Foundation
    Repo/CI/Docker/DB       :p0, 2026-07-07, 10d
    section Vertical Slice
    RTSP+YOLO+1rule+TG      :p1, after p0, 12d
    section AI Core
    Pose+ByteTrack         :p2a, after p1, 10d
    ROI+Motion+Temporal    :p2b, after p2a, 10d
    section Rule Engine
    7 Behaviors            :p3, after p2b, 18d
    Shadow+Tuning          :p3b, after p3, 10d
    section Backend/API
    Auth+CRUD+Evidence     :p4, after p2b, 18d
    Performance+Reports    :p4b, after p4, 12d
    section Frontend
    Live+Alerts+Timeline   :p5, after p4, 18d
    Replay+Charts+Heatmap  :p5b, after p5, 12d
    section Scale & Perf
    Multi-cam+TensorRT     :p6, after p3b, 14d
    section Hardening
    Security+DR+UAT        :p7, after p6, 14d
```

---

## 3. Chi tiết mục tiêu từng phase

| Phase | Mục tiêu | Deliverable | Định nghĩa hoàn thành (DoD) |
|-------|----------|-------------|------------------------------|
| P0 Foundation | Nền tảng dev | Monorepo, CI, docker-compose, DB migration, .env | `docker compose up` chạy stack rỗng, CI xanh |
| P1 Vertical Slice | Chứng minh khả thi | 1 camera → YOLO person → rule phone (đơn giản) → alert Telegram | Nhận 1 alert thật qua Telegram kèm ảnh |
| P2 AI Core | Perception đầy đủ | Pose + ByteTrack + ROI + motion + temporal buffer | Track ID ổn định, ROI gán đúng, tín hiệu ổn định |
| P3 Rule Engine | 7 hành vi | Đủ 7 rule + FSM + hot-reload + shadow mode | Mỗi rule pass golden clips, FP ≤ ngưỡng |
| P4 Backend/API | Dịch vụ | Auth/RBAC, CRUD, evidence storage, performance/report | API pass test, evidence lưu & signed URL |
| P5 Dashboard | UI | Live overlay, alerts, timeline, replay, charts, heatmap, ROI editor | Manager dùng được end-to-end |
| P6 Scale/Perf | Hiệu năng | Multi-cam, TensorRT, adaptive skip, tuning | Đạt NFR-PERF (≥4–8 cam/GPU) |
| P7 Hardening | Sẵn sàng SX | Security, DR, monitoring, docs, UAT | Pass security review + UAT ký nhận |

---

## 4. Cột mốc (Milestones)

| Milestone | Nội dung | Tiêu chí |
|-----------|----------|----------|
| M1 | Walking skeleton | Alert Telegram từ 1 camera |
| M2 | AI core hoàn chỉnh | Pose+track+ROI+temporal ổn định |
| M3 | Rule Engine đủ 7 | Shadow mode + tuning đạt precision mục tiêu |
| M4 | Beta nội bộ | Dashboard + backend đầy đủ, chạy 2–4 camera |
| M5 | Production-ready | Multi-cam, security, DR, UAT xong |

---

## 5. Chiến lược phát hành
- **Shadow-first:** rule chạy log-only trước khi bật alert thật.
- **Camera rollout theo nhóm:** mở rộng dần, tuning theo môi trường thực.
- **Feature flags:** bật/tắt từng rule, từng module.

## 6. Phụ thuộc & rủi ro tiến độ
- Dataset "food" custom cần chuẩn bị sớm (P2/P3).
- GPU/WSL2 setup có thể tốn thời gian (P0).
- Tuning FP là vòng lặp — dự phòng buffer thời gian ở P3b/P6.

## 7. Best Practices
- Ưu tiên vertical slice để giảm rủi ro tích hợp.
- Mỗi phase kết thúc bằng demo + retro.
- Đo lường (FP rate, FPS) từ sớm để định hướng tuning.
