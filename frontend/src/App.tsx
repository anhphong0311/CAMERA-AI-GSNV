import { Suspense } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AppLayout } from "@/components/layout/AppLayout";
import { ProtectedRoute } from "@/components/common/ProtectedRoute";
import { WebSocketProvider } from "@/contexts/WebSocketContext";
import { Loading } from "@/components/Loading";

import { LoginPage } from "@/pages/LoginPage";
import { NotFoundPage } from "@/pages/NotFoundPage";
import { OverviewPage } from "@/pages/OverviewPage";
import { LiveCameraPage } from "@/pages/LiveCameraPage";
import { CameraManagementPage } from "@/pages/CameraManagementPage";
import { LiveDetectionPage } from "@/pages/LiveDetectionPage";
import { TrackingPage } from "@/pages/TrackingPage";
import { AlertsPage } from "@/pages/AlertsPage";
import { ReplayPage } from "@/pages/ReplayPage";
import { EmployeesPage } from "@/pages/EmployeesPage";
import { RulesPage } from "@/pages/RulesPage";
import { RoiPage } from "@/pages/RoiPage";
import { StatisticsPage } from "@/pages/StatisticsPage";
import { ReportsPage } from "@/pages/ReportsPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { SystemMonitorPage } from "@/pages/SystemMonitorPage";
import { TrainingDashboardPage } from "@/pages/TrainingDashboardPage";
import { LogsPage } from "@/pages/LogsPage";

/** Bọc WebSocket realtime quanh layout (chỉ chạy khi đã đăng nhập). */
function RealtimeLayout() {
  return (
    <WebSocketProvider>
      <AppLayout />
    </WebSocketProvider>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<Loading />}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          <Route element={<ProtectedRoute />}>
            <Route element={<RealtimeLayout />}>
              {/* Mọi role */}
              <Route path="/" element={<OverviewPage />} />
              <Route path="/live" element={<LiveCameraPage />} />
              <Route path="/detection" element={<LiveDetectionPage />} />
              <Route path="/tracking" element={<TrackingPage />} />
              <Route path="/alerts" element={<AlertsPage />} />
              <Route path="/replay" element={<ReplayPage />} />
              <Route path="/statistics" element={<StatisticsPage />} />
              <Route path="/reports" element={<ReportsPage />} />
              <Route path="/system" element={<SystemMonitorPage />} />

              {/* Admin + Supervisor — ML Platform */}
              <Route element={<ProtectedRoute roles={["admin", "supervisor"]} />}>
                <Route path="/training" element={<TrainingDashboardPage />} />
              </Route>

              {/* Admin + Supervisor */}
              <Route element={<ProtectedRoute roles={["admin", "supervisor"]} />}>
                <Route path="/cameras" element={<CameraManagementPage />} />
                <Route path="/employees" element={<EmployeesPage />} />
                <Route path="/rules" element={<RulesPage />} />
                <Route path="/roi" element={<RoiPage />} />
                <Route path="/logs" element={<LogsPage />} />
              </Route>

              {/* Admin */}
              <Route element={<ProtectedRoute roles={["admin"]} />}>
                <Route path="/settings" element={<SettingsPage />} />
              </Route>
            </Route>
          </Route>

          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
