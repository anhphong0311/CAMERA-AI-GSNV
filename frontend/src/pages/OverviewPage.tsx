import { useEffect, useState } from "react";
import {
  AlertTriangle,
  Camera,
  CameraOff,
  Cpu,
  Gauge,
  HardDrive,
  MemoryStick,
  ShieldAlert,
} from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { StatCard } from "@/components/common/StatCard";
import { SeverityBadge } from "@/components/common/SeverityBadge";
import { EmptyState } from "@/components/common/EmptyState";
import { AreaChartCard } from "@/components/charts/Charts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useOverview } from "@/hooks/api";
import { useRealtimeChannel, useRealtimeFeed } from "@/hooks/useRealtimeChannel";
import { formatRelative, pct } from "@/lib/utils";
import type { AlertEvent, SystemMetrics } from "@/types";

/** Trang Overview — KPI realtime + alert gần đây + xu hướng. */
export function OverviewPage() {
  const { data: overview } = useOverview();
  const system = useRealtimeChannel<SystemMetrics>("system");
  const alerts = useRealtimeFeed<AlertEvent>("alert", 8);
  const [trend, setTrend] = useState<{ t: string; alerts: number }[]>([]);

  const sys = system ?? overview?.system;

  useEffect(() => {
    const id = setInterval(() => {
      setTrend((prev) =>
        [
          ...prev,
          {
            t: new Date().toLocaleTimeString("vi-VN", {
              hour: "2-digit",
              minute: "2-digit",
              second: "2-digit",
            }),
            alerts: overview?.today_alerts ?? 0,
          },
        ].slice(-20)
      );
    }, 3000);
    return () => clearInterval(id);
  }, [overview?.today_alerts]);

  return (
    <div className="space-y-6">
      <PageHeader title="Dashboard" description="Tổng quan hệ thống giám sát — cập nhật realtime" />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard title="Camera Online" value={overview?.cameras_online ?? "—"} icon={Camera} accent="text-success" hint={`Tổng ${overview?.cameras_total ?? 0} camera`} />
        <StatCard title="Camera Offline" value={overview?.cameras_offline ?? "—"} icon={CameraOff} accent="text-destructive" />
        <StatCard title="AI FPS" value={overview?.ai_fps ?? "—"} icon={Gauge} accent="text-primary" />
        <StatCard title="Alerts hôm nay" value={overview?.today_alerts ?? "—"} icon={AlertTriangle} accent="text-warning" hint={`${overview?.today_violations ?? 0} vi phạm`} />
        <StatCard title="CPU" value={pct(sys?.cpu_percent)} icon={Cpu} />
        <StatCard title="GPU" value={sys?.gpu_available ? pct(sys?.gpu_percent) : "N/A"} icon={ShieldAlert} />
        <StatCard title="RAM" value={pct(sys?.ram_percent)} icon={MemoryStick} />
        <StatCard title="VRAM" value={sys?.gpu_available ? pct(sys?.vram_percent) : "N/A"} icon={HardDrive} />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <AreaChartCard title="Xu hướng cảnh báo (realtime)" data={trend} xKey="t" yKey="alerts" />
        </div>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">Cảnh báo gần đây</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {alerts.length === 0 ? (
              <EmptyState title="Chưa có cảnh báo" />
            ) : (
              alerts.map((a) => (
                <div key={a.event_id} className="flex items-center justify-between gap-2 rounded-md border p-2 text-sm">
                  <div className="min-w-0">
                    <p className="truncate font-medium">{a.rule_id}</p>
                    <p className="truncate text-xs text-muted-foreground">
                      {a.camera_name ?? `Camera ${a.camera_id}`} · Track #{a.track_id}
                    </p>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <SeverityBadge severity={a.severity} />
                    <span className="text-[10px] text-muted-foreground">{formatRelative(a.ts)}</span>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
