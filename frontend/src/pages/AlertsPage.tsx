import { useMemo, useState } from "react";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { DataTable, type Column } from "@/components/common/DataTable";
import { SeverityBadge } from "@/components/common/SeverityBadge";
import { EventDetailDialog } from "@/components/alert/EventDetailDialog";
import { useRecentAlerts } from "@/hooks/api";
import { useRealtimeFeed } from "@/hooks/useRealtimeChannel";
import { formatDateTime, formatDuration } from "@/lib/utils";
import type { AlertEvent } from "@/types";

/** Alert Center — cảnh báo realtime + chi tiết sự kiện khi click. */
export function AlertsPage() {
  const { data: rest } = useRecentAlerts(80);
  const live = useRealtimeFeed<AlertEvent>("alert", 80);
  const [selected, setSelected] = useState<AlertEvent | null>(null);

  const rows = useMemo(() => {
    const map = new Map<string, AlertEvent>();
    [...live, ...(rest ?? [])].forEach((a) => map.set(a.event_id, a));
    return Array.from(map.values()).sort(
      (a, b) => new Date(b.ts ?? 0).getTime() - new Date(a.ts ?? 0).getTime()
    );
  }, [live, rest]);

  const columns: Column<AlertEvent>[] = [
    { key: "severity", header: "Severity", render: (r) => <SeverityBadge severity={r.severity} /> },
    { key: "status", header: "Status", render: (r) => <Badge variant="outline">{r.status}</Badge> },
    { key: "rule_id", header: "Rule" },
    { key: "camera", header: "Camera", render: (r) => r.camera_name ?? `#${r.camera_id}` },
    { key: "track_id", header: "Track", render: (r) => `#${r.track_id}` },
    { key: "duration", header: "Duration", render: (r) => formatDuration(r.duration) },
    { key: "ts", header: "Time", render: (r) => formatDateTime(r.ts) },
  ];

  return (
    <div className="space-y-4">
      <PageHeader title="Alert Center" description="Cảnh báo vi phạm realtime — click để xem chi tiết" />
      <Card>
        <CardContent className="pt-4">
          <DataTable
            columns={columns}
            rows={rows}
            rowKey={(r) => r.event_id}
            onRowClick={setSelected}
            emptyMessage="Chưa có cảnh báo nào"
          />
        </CardContent>
      </Card>
      <EventDetailDialog
        event={selected}
        open={!!selected}
        onOpenChange={(v) => !v && setSelected(null)}
      />
    </div>
  );
}
