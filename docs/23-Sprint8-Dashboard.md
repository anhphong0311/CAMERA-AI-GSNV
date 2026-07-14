# Sprint 8 — AI Operation Center Dashboard

Giao diện quản trị realtime cho AEMS. Dashboard **chỉ gọi API + WebSocket**, không
chứa business logic, không xử lý AI/Rule, không truy cập DB trực tiếp.

## Công nghệ

- **Frontend**: React 18 + TypeScript + Vite, TailwindCSS + Shadcn UI (Radix),
  TanStack Query, React Router v7, React Hook Form + Zod, Recharts, Sonner.
- **Realtime**: WebSocket thuần (tương thích FastAPI WebSocket). _Ghi chú: spec liệt
  kê "Socket.IO Client" nhưng backend là FastAPI WebSocket thuần, nên client dùng
  `WebSocket` API chuẩn — đúng interop. Lớp `RealtimeSocket` đóng gói reconnect +
  heartbeat + pub/sub theo channel, dễ thay bằng socket.io nếu backend đổi._
- **Backend (bổ sung Sprint 8, không sửa kiến trúc cũ)**:
  `app/modules/realtime/` — WebSocket hub + broadcaster + system metrics.

## Backend realtime

| Endpoint | Mô tả |
| --- | --- |
| `WS /api/v1/ws` | Kênh realtime: channel `system` / `detection` / `tracking` / `alert` |
| `GET /api/v1/realtime/overview` | KPI tổng quan (camera online/offline, FPS, alerts hôm nay) |
| `GET /api/v1/realtime/system` | Snapshot CPU/GPU/RAM/VRAM/Disk/Network |
| `GET /api/v1/realtime/alerts` | Alert realtime gần đây |
| `GET /api/v1/realtime/cameras` | Trạng thái camera |
| `GET /api/v1/realtime/connections` | Số client WebSocket |

`RealtimeBroadcaster` phát mỗi ~1s. Khi chưa có luồng camera thật, bật demo qua
`AEMS_REALTIME_DEMO=true` (mặc định) để Dashboard demo realtime end-to-end. GPU/VRAM
đọc qua `pynvml` nếu khả dụng, ngược lại trả `N/A`.

## Cấu trúc frontend (module)

```
src/
  contexts/     Auth (JWT/refresh/role), Theme (dark/light), WebSocket
  hooks/        useRealtimeChannel/Feed/ByCamera, api (TanStack Query), useRoiStore
  lib/          api (axios+interceptor), ws (RealtimeSocket), export (xlsx/pdf/csv),
                logger (user actions), constants (menu), utils (format)
  components/
    ui/         Shadcn primitives (button, dialog, select, table, tabs, ...)
    common/     ProtectedRoute, RoleGate, PageHeader, StatCard, DataTable,
                SeverityBadge, ConnectionStatus, ErrorBoundary, EmptyState
    layout/     AppLayout, Sidebar (menu + role filter + responsive), Navbar,
                ThemeToggle
    camera/     CameraTile (canvas + Live Overlay), GridSelector
    roi/        ROICanvas (polygon/rectangle)
    replay/     VideoPlayer (seek/speed/pause/fullscreen/download)
    charts/     Charts (Bar/Line/Area/Pie), HeatmapChart
    alert/      EventDetailDialog
    rule/       RuleFormDialog (CRUD)
  pages/        15 trang (xem menu) + Login + NotFound
```

## Bản đồ menu → trang

Dashboard · Live Camera · Camera Management · Live Detection · Tracking · Alerts ·
Replay · Employees · Rules · ROI Editor · Statistics · Reports · Settings ·
System Monitor · Logs.

## Permission

- **Admin**: toàn quyền (bao gồm Settings).
- **Supervisor**: quản lý Camera/Employees/Rules/ROI/Logs.
- **Viewer**: xem realtime (Dashboard/Live/Detection/Tracking/Alerts/Replay/Statistics/Reports/System).

Vai trò suy theo tài khoản khi đăng nhập demo (`admin`/`supervisor`/`viewer`), hoặc
lấy từ response `/auth/login` khi backend auth sẵn sàng. Remember Login lưu ở
`localStorage`, ngược lại `sessionStorage`.

## Chạy

```bash
# Backend (bật demo realtime)
cd backend && AEMS_REALTIME_DEMO=true uvicorn app.main:app --reload

# Frontend
cd frontend
cp .env.example .env
npm install
npm run dev        # http://localhost:5173 (proxy /api và /ws → :8000)
```

Docker: `docker compose up --build` — Nginx (:8080) đã cấu hình proxy WebSocket
(`Upgrade`/`Connection`) cho `/api/v1/ws`.

## Kiểm thử

```bash
npm run build      # tsc --noEmit + vite build (PASS)
npm run test       # Vitest unit test (11/11 PASS)
npm run test:e2e   # Playwright E2E (cần backend chạy để có dữ liệu realtime)
```

- **Unit**: utils (format), RealtimeSocket (pub/sub), SeverityBadge (component),
  ThemeContext (hook).
- **E2E**: Login, View Camera, Alert Center, Replay, Rule CRUD.

## Checklist cuối Sprint

| Mục | Trạng thái |
| --- | --- |
| Dashboard chạy (`npm run build`/`dev`) | ✅ |
| WebSocket Realtime | ✅ (`/api/v1/ws`, verified) |
| Live Camera hiển thị | ✅ (canvas grid 1/4/9/16 + overlay) |
| Detection Realtime | ✅ |
| Tracking Realtime | ✅ |
| Alert Realtime | ✅ |
| Replay | ✅ (seek/speed/download) |
| Rule CRUD | ✅ (gọi Rule API Sprint 6) |
| ROI Editor | ✅ (polygon/rectangle) |
| Statistics | ✅ (Bar/Pie/Area/Line) |
| Heatmap | ✅ |
| Export Excel/PDF/CSV | ✅ |
| Responsive (Desktop/Tablet) | ✅ |
| Dark Mode | ✅ |
| Unit Test | ✅ 11/11 |
| E2E Test | ✅ specs (cần backend) |

## Ràng buộc kiến trúc

Dashboard chỉ gọi API/WebSocket. Không AI, không Rule, không DB trực tiếp. ROI được
soạn thảo phía client (localStorage) như dữ liệu hiển thị — sẽ trỏ sang Zone API khi
backend expose.
