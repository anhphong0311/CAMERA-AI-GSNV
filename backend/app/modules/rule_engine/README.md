# Rule Engine — AI Rule Engine (Sprint 6)

Trung tâm **Business Logic** của AEMS. Suy luận hành vi từ dữ liệu các sprint trước
và tạo ra **BehaviorEvent** chuẩn. Đẩy event vào **AlertQueue** cho Sprint 7 tiêu thụ.

## Nguyên tắc

- **KHÔNG dùng AI model.** Chỉ đọc `DetectionResult`, `TrackingResult`,
  `BehaviorFeatureDTO`, ROI, Timeline, Temporal Buffer.
- **KHÔNG hardcode rule.** Mọi rule cấu hình bằng JSON/YAML: bật/tắt, thời gian,
  ngưỡng, severity, ROI, priority — không cần sửa source.
- **KHÔNG** Telegram, **KHÔNG** Database persistence, **KHÔNG** Dashboard.
- Output duy nhất: `BehaviorEventDTO`.

## Pipeline

```
DetectionResult → TrackingResult → BehaviorFeatureDTO
   → Facts → Condition → Expression → Evaluation → Event → Action → AlertQueue
```

## Cấu trúc thư mục

| Thư mục | Vai trò |
|---|---|
| `rule_engine/` | Core: `RuleEngine`, `FactExtractor`, `PerformanceScore` |
| `rule_executor/` | Đánh giá rule + timer điều kiện nền |
| `rule_parser/` | `Rule` model + parse JSON/YAML/file |
| `rule_validator/` | Kiểm tra rule hợp lệ |
| `rule_scheduler/` | Bảo trì định kỳ (cleanup) |
| `rule_history/` | Lịch sử thực thi rule |
| `condition/` | Cây điều kiện Leaf/Group (AND/OR/NOT, nested) |
| `action/` | `ActionExecutor` + `AlertQueue` |
| `expression/` | Toán tử so sánh (an toàn, không `eval`) |
| `event/` | `BehaviorEventDTO` + `Severity` |
| `timeline/` | `TemporalTracker` (10s..30m) |
| `state/` | `EventState`, `RuleState`, `StateStore`, `StateMachine` |
| `cache/` | `CooldownCache`, `DuplicateFilter` |
| `config/` | Loader cho rule_engine/severity/cooldown yaml |
| `schemas/` | Pydantic API schemas |
| `services/` | `RuleService` (facade đa camera) |
| `repositories/` | `RuleRepository`, `EventRepository` (in-memory) |
| `visualization/` | Rule Flow / Condition Tree / Event Lifecycle |
| `tests/` | Placeholder (test thực ở `backend/tests/...`) |

## Rule Format

```json
{
  "id": "PHONE_USAGE",
  "name": "Phone Usage",
  "enabled": true,
  "severity": "HIGH",
  "priority": 1,
  "cooldown": 300,
  "actions": ["alert"],
  "conditions": {
    "operator": "AND",
    "conditions": [
      { "type": "phone_detected", "operator": "==", "value": true },
      { "type": "hand_near_phone", "operator": "==", "value": true },
      { "type": "duration", "operator": ">", "value": 10 }
    ]
  }
}
```

- `conditions` là **list** (AND ngầm định) hoặc **group** `{operator, conditions}`.
- Leaf: `{type, operator, value}`. Operator: `== != > >= < <= in not_in contains`.
- Leaf đặc biệt `type: duration` → so với thời gian điều kiện nền được giữ liên tục.

## Facts (biến rule tham chiếu)

`phone_detected, hand_near_phone, looking_phone, looking_monitor, head_down,
head_direction, head_angle, movement_speed, stationary, stationary_time, low_motion,
sitting, hand_on_desk, hand_near_face, working, in_roi, roi, away_from_desk,
food_visible, food_near_mouth, person_count, nearest_person_distance, has_nearby_person`

## Hành vi mặc định (rules.yaml)

| Rule | Điều kiện | Severity |
|---|---|---|
| PHONE_USAGE | phone + hand_near_phone + >10s | HIGH |
| AWAY_FROM_DESK | rời ROI + >300s | MEDIUM |
| PRIVATE_TALKING | ≥2 người + gần + không làm việc + >120s | MEDIUM |
| EATING | food/cup/bottle + gần miệng + >60s | LOW |
| SLEEPING | cúi đầu + ít chuyển động + >20s | HIGH |
| IDLE | đứng yên + không làm việc + >600s | LOW |

## Vòng đời Event

`Created(NEW) → Candidate(ACTIVE) → Confirmed(CONFIRMED/Alerted) → Resolved(ENDED)`;
`IGNORED` khi bị **Cooldown** hoặc **Duplicate Filter** loại.

## Cơ chế chống nhiễu

- **Cooldown**: sau khi event kết thúc, khóa (rule, track) N giây (`cooldown.yaml`).
- **Duplicate Filter**: cùng rule + track trong `duplicate_window` → không tạo event mới.
- **Temporal Analysis**: theo dõi tỉ lệ active qua 10s/30s/1m/5m/10m/30m.

## Performance Score

`RuleService.performance_reports()` → mỗi track có `score` (0..100) tính từ thời gian
Working/Phone/Talking/Eating/Sleeping/Away/Idle với trọng số trong `rule_engine.yaml`.

## API (mount `/api/v1`)

- `GET/POST /rules`, `GET/PUT/DELETE /rules/{id}`
- `POST /rules/enable`, `POST /rules/disable`
- `GET /rules/statistics`, `GET /rules/performance`
- `GET /rules/flow`, `GET /rules/lifecycle` (visualization)
- `GET /events`, `GET /events/live`, `GET /events/history`
- `GET /events/statistics`, `GET /events/queue` (AlertQueue)

## Config

`config/rules.yaml`, `config/rule_engine.yaml`, `config/severity.yaml`,
`config/cooldown.yaml` (mount read-only qua env `*_CONFIG_PATH`).

## Test

```
python -m pytest tests/modules/rule_engine/ -q
```
