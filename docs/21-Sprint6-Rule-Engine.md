# Sprint 6 — AI Rule Engine

## Mục tiêu

Xây dựng **AI Rule Engine** — trung tâm xử lý toàn bộ Business Logic. Engine **không dùng
AI model**; chỉ đọc dữ liệu đã xử lý từ Detection / Tracking / Behavior Feature (+ ROI,
Timeline, Temporal Buffer) để **suy luận hành vi** và tạo `BehaviorEvent`.

Giới hạn (theo yêu cầu): **KHÔNG** Telegram, **KHÔNG** Database persistence, **KHÔNG**
Dashboard. Output duy nhất là `BehaviorEventDTO`, đẩy vào `AlertQueue` cho Sprint 7.

## Kiến trúc

```
DetectionResult → TrackingResult → BehaviorFeatureDTO
   → RuleEngine (Facts → Condition → Expression → Evaluation → Event → Action)
   → BehaviorEvent → AlertQueue → Sprint 7
```

Module: `backend/app/modules/rule_engine/` với các gói con: `rule_engine/`,
`rule_executor/`, `rule_parser/`, `rule_validator/`, `rule_scheduler/`, `rule_history/`,
`condition/`, `action/`, `expression/`, `event/`, `timeline/`, `state/`, `cache/`,
`config/`, `schemas/`, `services/`, `repositories/`, `visualization/`, `tests/`.

## Triết lý config-driven

Mọi rule cấu hình trong `config/rules.yaml` (hoặc thêm động qua API). Có thể bật/tắt,
sửa thời gian, ngưỡng, mức cảnh báo, ROI, độ ưu tiên **mà không sửa source**. Hỗ trợ
cả JSON và YAML.

### Rule Format

- `conditions` là **list** (AND ngầm định) hoặc **group** `{operator: AND|OR|NOT, conditions}`.
- Leaf `{type, operator, value}`, operator: `== != > >= < <= in not_in contains`.
- Leaf `type: duration` → so với thời gian điều kiện nền giữ liên tục (state timer).
- Hỗ trợ **AND / OR / NOT / GROUP / Nested Condition** (giới hạn 10 cấp — chống circular).

## Rule Execution

`RuleExecutor` tách điều kiện nền (bỏ leaf `duration`) khỏi ngưỡng thời gian:

1. `base_active` = đánh giá cây (leaf duration = True).
2. Cập nhật `active_seconds` theo `dt` khi `base_active` đúng; reset khi sai.
3. `fired` = `base_active AND` (đánh giá lại cây với `duration = active_seconds`).

## Event & State Machine

`BehaviorEventDTO`: `event_id, camera_id, track_id, rule_id, event_type, severity,
confidence, state, start_time, end_time, duration, snapshot, video_reference, metadata`.

Vòng đời: `Created(NEW) → Candidate(ACTIVE) → Confirmed(CONFIRMED) → Resolved(ENDED)`;
`IGNORED` khi Cooldown/Duplicate loại. `StateMachine` kiểm soát chuyển trạng thái hợp lệ.

## 6 hành vi mặc định

| Rule | Điều kiện | Severity | Cooldown |
|---|---|---|---|
| PHONE_USAGE | phone_detected + hand_near_phone + duration>10 | HIGH | 300s |
| AWAY_FROM_DESK | away_from_desk + duration>300 | MEDIUM | 600s |
| PRIVATE_TALKING | person_count≥2 + has_nearby_person + !working + duration>120 | MEDIUM | 300s |
| EATING | food_visible + food_near_mouth + duration>60 | LOW | 300s |
| SLEEPING | head_down + low_motion + duration>20 | HIGH | 120s |
| IDLE | stationary + !working + duration>600 | LOW | 600s |

Priority: Critical / High / Medium / Low / Info.

## Chống nhiễu

- **Cooldown** (`config/cooldown.yaml`): khóa (rule, track) sau khi event kết thúc.
- **Duplicate Filter**: cùng rule + track trong `duplicate_window` (mặc định 300s) → bỏ.
- **Temporal Analysis** (`TemporalTracker`): tỉ lệ active qua 10s/30s/1m/5m/10m/30m.
- **RuleScheduler**: dọn cooldown/duplicate/temporal/state định kỳ → không memory leak.

## Performance Score

`PerformanceScoreCalculator` tích lũy thời gian Working/Phone/Talking/Eating/Sleeping/
Away/Idle mỗi track → `score = 100 − Σ weight·(cat_time/total)·100` (kẹp [0,100]). Trọng
số trong `rule_engine.yaml`. Truy vấn qua `GET /api/v1/rules/performance`.

## API (mount `/api/v1`)

Rules: `GET/POST /rules`, `GET/PUT/DELETE /rules/{id}`, `POST /rules/enable`,
`POST /rules/disable`, `GET /rules/statistics`, `GET /rules/performance`,
`GET /rules/flow`, `GET /rules/lifecycle`.

Events: `GET /events`, `GET /events/live`, `GET /events/history`,
`GET /events/statistics`, `GET /events/queue`.

## Config

`config/rules.yaml`, `config/rule_engine.yaml`, `config/severity.yaml`,
`config/cooldown.yaml` — mount read-only trong `docker-compose.yml` qua env
`RULES_CONFIG_PATH`, `RULE_ENGINE_CONFIG_PATH`, `SEVERITY_CONFIG_PATH`,
`COOLDOWN_CONFIG_PATH`.

## Logging & Error Handling

- Log: Rule Loaded/Enabled/Disabled, Event Created/Confirmed/Ended, Action alert→queue.
- Exceptions: `InvalidRuleError`, `CircularRuleError`, `MissingParameterError`,
  `ExpressionError`, `RuleTimeoutError`, `DuplicateRuleError`, `RuleNotFoundError`.
  Lỗi biểu thức khi chạy được nuốt an toàn (rule đó coi như không active), không sập engine.

## Visualization

`visualization/` xuất dict: `rule_flow()` (pipeline), `condition_tree(rule)` (cây điều kiện),
`event_lifecycle()` (state machine). Đưa qua API `/rules/flow`, `/rules/lifecycle`,
`/rules/{id}`.

## Kiểm thử

- **Unit** (`backend/tests/modules/rule_engine/`): expression, condition tree + parser,
  rule parser (JSON/YAML/file), validator, facts, cooldown/duplicate, temporal/state,
  executor, performance/repositories, engine (lifecycle/cooldown/duplicate).
- **Integration**: Detection → Tracking → Behavior Feature → Rule Engine → Event
  (PHONE_USAGE, EATING, SLEEPING), performance score, alert queue, multi-track độc lập,
  visualization, dọn state (no leak).

```
python -m pytest tests/modules/rule_engine/ -q     # 57 passed
python -m pytest -q                                 # 218 passed (toàn dự án)
```

## Checklist cuối Sprint

✓ Đọc Detection/Tracking/Behavior · ✓ Rule JSON & YAML · ✓ AND/OR/NOT · ✓ Cooldown ·
✓ Duplicate Filter · ✓ Temporal Analysis · ✓ Event Lifecycle · ✓ Performance Score ·
✓ API Rule & Event · ✓ Unit + Integration test pass · ✓ Không memory leak · ✓ Không deadlock
(thao tác đồng bộ, khóa `RLock` ngắn, không khóa lồng chéo).

## Không nằm trong Sprint 6

Telegram, Database persistence, Dashboard — chờ Sprint 7 (tiêu thụ `AlertQueue`).
