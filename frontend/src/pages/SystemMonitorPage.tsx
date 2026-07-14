import { useEffect, useState } from "react";
import { Cpu, HardDrive, MemoryStick, Network, Activity } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { LineChartCard } from "@/components/charts/Charts";
import { useCameras, useSystemSnapshot } from "@/hooks/api";
import { useRealtimeChannel } from "@/hooks/useRealtimeChannel";
import { pct } from "@/lib/utils";
import type { SystemMetrics } from "@/types";

function Meter({
  label,
  value,
  icon: Icon,
  extra,
}: {
  label: string;
  value: number | null | undefined;
  icon: typeof Cpu;
  extra?: string;
}) {
  return (
    <Card>
      <CardContent className="space-y-2 p-4">
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-2 text-sm font-medium">
            <Icon className="h-4 w-4 text-primary" /> {label}
          </span>
          <span className="text-sm font-bold">{pct(value)}</span>
        </div>
        <Progress value={value ?? 0} />
        {extra && <p className="text-xs text-muted-foreground">{extra}</p>}
      </CardContent>
    </Card>
  );
}

/** System Monitor — CPU/GPU/RAM/VRAM/Disk/Network/FPS + Camera Health. */
export function SystemMonitorPage() {
  const { data: snapshot } = useSystemSnapshot();
  const live = useRealtimeChannel<SystemMetrics>("system");
  const { data: cameras } = useCameras();
  const [history, setHistory] = useState<{ t: string; cpu: number; gpu: number }[]>([]);

  const sys = live ?? snapshot;

  useEffect(() => {
    if (!sys) return;
    setHistory((prev) =>
      [
        ...prev,
        {
          t: new Date().toLocaleTimeString("vi-VN", { minute: "2-digit", second: "2-digit" }),
          cpu: sys.cpu_percent ?? 0,
          gpu: sys.gpu_percent ?? 0,
        },
      ].slice(-30)
    );
  }, [sys]);

  return (
    <div className="space-y-4">
      <PageHeader title="System Monitor" description="Giám sát tài nguyên hệ thống realtime" />

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Meter label="CPU" value={sys?.cpu_percent} icon={Cpu} />
        <Meter
          label="GPU"
          value={sys?.gpu_available ? sys?.gpu_percent : 0}
          icon={Activity}
          extra={sys?.gpu_available ? undefined : "GPU không khả dụng"}
        />
        <Meter
          label="RAM"
          value={sys?.ram_percent}
          icon={MemoryStick}
          extra={sys?.ram_total_mb ? `${sys.ram_used_mb} / ${sys.ram_total_mb} MB` : undefined}
        />
        <Meter
          label="VRAM"
          value={sys?.gpu_available ? sys?.vram_percent : 0}
          icon={HardDrive}
          extra={sys?.vram_total_mb ? `${sys.vram_used_mb} / ${sys.vram_total_mb} MB` : undefined}
        />
        <Meter
          label="Disk"
          value={sys?.disk_percent}
          icon={HardDrive}
          extra={sys?.disk_total_gb ? `${sys.disk_used_gb} / ${sys.disk_total_gb} GB` : undefined}
        />
        <Card>
          <CardContent className="space-y-1 p-4">
            <span className="flex items-center gap-2 text-sm font-medium">
              <Network className="h-4 w-4 text-primary" /> Network
            </span>
            <p className="text-sm">↑ {sys?.net_sent_kbps ?? 0} KB/s</p>
            <p className="text-sm">↓ {sys?.net_recv_kbps ?? 0} KB/s</p>
          </CardContent>
        </Card>
      </div>

      <LineChartCard title="CPU / GPU theo thời gian" data={history} xKey="t" yKey="cpu" />

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold">Camera Health</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          {(cameras ?? []).map((c) => (
            <div key={c.camera_id} className="flex items-center justify-between rounded-md border p-3">
              <div>
                <p className="text-sm font-medium">{c.name}</p>
                <p className="text-xs text-muted-foreground">{c.fps.toFixed(0)} FPS</p>
              </div>
              <Badge variant={c.status === "online" ? "success" : "destructive"}>
                {c.status}
              </Badge>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
