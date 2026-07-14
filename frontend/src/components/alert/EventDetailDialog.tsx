import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { SeverityBadge } from "@/components/common/SeverityBadge";
import { VideoPlayer } from "@/components/replay/VideoPlayer";
import { formatDateTime, formatDuration } from "@/lib/utils";
import { ImageOff } from "lucide-react";
import type { AlertEvent } from "@/types";

/** Chi tiết sự kiện — Snapshot / Video / Timeline / Rule / Confidence / Track / Metadata. */
export function EventDetailDialog({
  event,
  open,
  onOpenChange,
}: {
  event: AlertEvent | null;
  open: boolean;
  onOpenChange: (v: boolean) => void;
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            Chi tiết sự kiện
            {event && <SeverityBadge severity={event.severity} />}
          </DialogTitle>
        </DialogHeader>

        {event && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="overflow-hidden rounded-lg border">
                <p className="border-b bg-muted px-3 py-1 text-xs font-medium">Snapshot</p>
                {event.snapshot?.path ? (
                  <img src={event.snapshot.path} alt="snapshot" className="aspect-video w-full object-cover" />
                ) : (
                  <div className="flex aspect-video items-center justify-center text-muted-foreground">
                    <ImageOff className="h-8 w-8" />
                  </div>
                )}
              </div>
              <div className="overflow-hidden rounded-lg border">
                <p className="border-b bg-muted px-3 py-1 text-xs font-medium">Video bằng chứng</p>
                <VideoPlayer src={event.video?.path} title={`${event.rule_id}_${event.event_id}`} />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm md:grid-cols-3">
              <Field label="Rule" value={event.rule_id} />
              <Field label="Confidence" value={`${(event.confidence * 100).toFixed(0)}%`} />
              <Field label="Track" value={`#${event.track_id}`} />
              <Field label="Camera" value={event.camera_name ?? `#${event.camera_id}`} />
              <Field label="ROI" value={event.roi ?? "—"} />
              <Field label="Duration" value={formatDuration(event.duration)} />
              <Field label="Status" value={<Badge variant="outline">{event.status}</Badge>} />
              <Field label="Thời gian" value={formatDateTime(event.ts)} />
              <Field label="Event ID" value={event.event_id} />
            </div>

            <div>
              <p className="mb-1 text-xs font-medium text-muted-foreground">Timeline</p>
              <div className="flex items-center gap-2 text-xs">
                {["NEW", "ACTIVE", "CONFIRMED", "ENDED"].map((s, i) => (
                  <div key={s} className="flex items-center gap-2">
                    <Badge variant={i === 0 ? "default" : "secondary"}>{s}</Badge>
                    {i < 3 && <span className="text-muted-foreground">→</span>}
                  </div>
                ))}
              </div>
            </div>

            {event.metadata && (
              <pre className="max-h-40 overflow-auto rounded-md bg-muted p-3 text-xs">
                {JSON.stringify(event.metadata, null, 2)}
              </pre>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="font-medium">{value}</p>
    </div>
  );
}
