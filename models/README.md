# Model weights (Sprint 3 — Detection, Sprint 5 — Pose)

Thư mục chứa weight YOLO11 (`.pt`, `.onnx`, `.engine`).

- Mount vào backend container tại `/models` (xem `docker-compose.yml`).
- `MODELS_DIR` env trỏ tới đây; `ModelRepository` tìm weight ở đây trước.
- Nếu để tên weight chuẩn (ví dụ `yolo11n.pt`) và không có sẵn, Ultralytics
  sẽ tự động tải về khi load model lần đầu.

Weight sử dụng:

- `yolo11n.pt` — Detection Engine (Sprint 3).
- `yolo11n-pose.pt` — Pose/Behavior Feature Engine (Sprint 5), cấu hình tại
  `config/behavior.yaml → pose.model_path`.

Không commit file weight lớn vào git.
