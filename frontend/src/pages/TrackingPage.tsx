import { useMemo } from "react";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { DataTable, type Column } from "@/components/common/DataTable";
import { useRealtimeByCamera } from "@/hooks/useRealtimeChannel";
import { formatDuration } from "@/lib/utils";
import type { TrackingFrame, TrackInfo } from "@/types";

/** Tracking — bảng track realtime: ROI, duration, movement, speed, stationary. */
export function TrackingPage() {
  const frames = useRealtimeByCamera<TrackingFrame>("tracking");

  const rows = useMemo<TrackInfo[]>(
    () => Object.values(frames).flatMap((f) => f.tracks),
    [frames]
  );

  const columns: Column<TrackInfo>[] = [
    { key: "track_id", header: "Track ID", render: (r) => <Badge>#{r.track_id}</Badge> },
    { key: "camera_id", header: "Camera", render: (r) => `#${r.camera_id}` },
    { key: "roi", header: "Current ROI" },
    { key: "duration", header: "Duration", render: (r) => formatDuration(r.duration) },
    {
      key: "direction",
      header: "Movement",
      render: (r) => <Badge variant="outline">{r.direction}</Badge>,
    },
    { key: "speed", header: "Speed", render: (r) => `${r.speed.toFixed(2)} m/s` },
    {
      key: "stationary_time",
      header: "Stationary",
      render: (r) => formatDuration(r.stationary_time),
    },
  ];

  return (
    <div className="space-y-4">
      <PageHeader title="Tracking" description="Theo dõi đối tượng realtime từ Tracking Engine" />
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold">
            Track đang hoạt động ({rows.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable
            columns={columns}
            rows={rows}
            rowKey={(r) => `${r.camera_id}-${r.track_id}`}
            emptyMessage="Đang chờ dữ liệu tracking..."
          />
        </CardContent>
      </Card>
    </div>
  );
}
