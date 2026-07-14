# Frontend — AI Operation Center Dashboard (Sprint 8)

React 18 + Vite + TypeScript + TailwindCSS + Shadcn UI (Radix) + TanStack Query +
React Router + React Hook Form + Zod + Recharts. Realtime qua WebSocket.

> Dashboard chỉ gọi API + WebSocket — không xử lý AI/Rule, không truy cập DB.

## Chạy local

```bash
cd frontend
npm install
copy .env.example .env          # cấu hình VITE_API_BASE_URL, VITE_WS_URL
npm run dev                     # http://localhost:5173 (proxy /api & /ws → :8000)
```

Backend bật demo realtime: `AEMS_REALTIME_DEMO=true uvicorn app.main:app --reload`.

## Scripts

```bash
npm run build      # tsc --noEmit + vite build
npm run test       # Vitest (unit)
npm run test:e2e   # Playwright (E2E — cần backend chạy)
npm run lint       # ESLint
```

## Tính năng

- 15 trang: Dashboard, Live Camera (grid 1/4/9/16 + overlay), Camera Management,
  Live Detection, Tracking, Alerts + Event Detail, Replay, Employees, Rules (CRUD),
  ROI Editor (polygon/rectangle), Statistics, Reports (Excel/PDF/CSV), Settings,
  System Monitor, Logs.
- Realtime WebSocket: detection / tracking / alert / system.
- JWT + Refresh + Remember Login + Role (Admin/Supervisor/Viewer).
- Dark/Light mode, responsive Desktop/Tablet.

Chi tiết: [`docs/23-Sprint8-Dashboard.md`](../docs/23-Sprint8-Dashboard.md).
