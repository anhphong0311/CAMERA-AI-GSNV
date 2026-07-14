import { useEffect, useState } from "react";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { VideoPlayer } from "@/components/replay/VideoPlayer";
import { SeverityBadge } from "@/components/common/SeverityBadge";
import { EmptyState } from "@/components/common/EmptyState";
import { useRecentAlerts } from "@/hooks/api";
import { logAction } from "@/lib/logger";
import { cn, formatDateTime } from "@/lib/utils";
import type { AlertEvent } from "@/types";

/** Video Replay — chọn sự kiện, phát video bằng chứng. */
export function ReplayPage() {
  const { data: events } = useRecentAlerts(60);
  const [selected, setSelected] = useState<AlertEvent | null>(null);

  useEffect(() => {
    if (selected) logAction("replay", `event ${selected.event_id}`);
  }, [selected]);

  return (
    <div className="space-y-4">
      <PageHeader title="Video Replay" description="Xem lại video bằng chứng các sự kiện" />
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">Sự kiện</CardTitle>
          </CardHeader>
          <CardContent className="max-h-[70vh] space-y-2 overflow-y-auto">
            {(events ?? []).length === 0 && <EmptyState title="Chưa có sự kiện" />}
            {(events ?? []).map((e) => (
              <button
                key={e.event_id}
                onClick={() => setSelected(e)}
                className={cn(
                  "flex w-full items-center justify-between gap-2 rounded-md border p-2 text-left text-sm transition-colors hover:bg-accent",
                  selected?.event_id === e.event_id && "border-primary bg-accent"
                )}
              >
                <div className="min-w-0">
                  <p className="truncate font-medium">{e.rule_id}</p>
                  <p className="truncate text-xs text-muted-foreground">
                    {e.camera_name ?? `Camera ${e.camera_id}`} · {formatDateTime(e.ts)}
                  </p>
                </div>
                <SeverityBadge severity={e.severity} />
              </button>
            ))}
          </CardContent>
        </Card>

        <div className="lg:col-span-2">
          <VideoPlayer
            src={selected?.video?.path}
            title={selected ? `${selected.rule_id}_${selected.event_id}` : undefined}
          />
          {selected && (
            <Card className="mt-4">
              <CardContent className="grid grid-cols-2 gap-3 pt-4 text-sm md:grid-cols-4">
                <Info label="Rule" value={selected.rule_id} />
                <Info label="Camera" value={selected.camera_name ?? `#${selected.camera_id}`} />
                <Info label="Track" value={`#${selected.track_id}`} />
                <Info label="Confidence" value={`${(selected.confidence * 100).toFixed(0)}%`} />
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="font-medium">{value}</p>
    </div>
  );
}
