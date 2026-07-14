import { useMemo } from "react";
import { PageHeader } from "@/components/common/PageHeader";
import { StatCard } from "@/components/common/StatCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { DataTable, type Column } from "@/components/common/DataTable";
import { ScanEye } from "lucide-react";
import { useRealtimeByCamera } from "@/hooks/useRealtimeChannel";
import { DETECTION_LABELS } from "@/lib/constants";
import { formatRelative } from "@/lib/utils";
import type { DetectionFrame } from "@/types";

interface DetRow {
  key: string;
  camera: number;
  label: string;
  confidence: number;
  track: number | null;
  roi?: string;
  ts: string;
}

/** Live Detection — danh sách đối tượng nhận diện realtime. */
export function LiveDetectionPage() {
  const frames = useRealtimeByCamera<DetectionFrame>("detection");

  const rows = useMemo<DetRow[]>(() => {
    const out: DetRow[] = [];
    Object.values(frames).forEach((f) => {
      f.objects.forEach((o, i) =>
        out.push({
          key: `${f.camera_id}-${i}-${o.label}`,
          camera: f.camera_id,
          label: o.label,
          confidence: o.confidence,
          track: o.track_id,
          roi: o.roi,
          ts: f.ts,
        })
      );
    });
    return out;
  }, [frames]);

  const counts = useMemo(() => {
    const c: Record<string, number> = {};
    rows.forEach((r) => (c[r.label] = (c[r.label] ?? 0) + 1));
    return c;
  }, [rows]);

  const columns: Column<DetRow>[] = [
    { key: "camera", header: "Camera", render: (r) => `#${r.camera}` },
    { key: "label", header: "Đối tượng", render: (r) => <Badge variant="secondary">{r.label}</Badge> },
    { key: "track", header: "Track", render: (r) => (r.track != null ? `#${r.track}` : "—") },
    { key: "confidence", header: "Confidence", render: (r) => `${(r.confidence * 100).toFixed(0)}%` },
    { key: "roi", header: "ROI", render: (r) => r.roi ?? "—" },
    { key: "ts", header: "Thời gian", render: (r) => formatRelative(r.ts) },
  ];

  return (
    <div className="space-y-4">
      <PageHeader title="Live Detection" description="Đối tượng nhận diện realtime từ AI Engine" />

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {DETECTION_LABELS.slice(0, 6).map((l) => (
          <StatCard key={l} title={l} value={counts[l] ?? 0} icon={ScanEye} />
        ))}
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold">
            Đối tượng hiện tại ({rows.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable columns={columns} rows={rows} rowKey={(r) => r.key} emptyMessage="Đang chờ dữ liệu detection..." />
        </CardContent>
      </Card>
    </div>
  );
}
