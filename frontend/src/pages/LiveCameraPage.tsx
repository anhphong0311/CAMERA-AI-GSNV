import { useEffect, useMemo, useState } from "react";
import { PageHeader } from "@/components/common/PageHeader";
import { GridSelector, type GridSize } from "@/components/camera/GridSelector";
import { CameraTile } from "@/components/camera/CameraTile";
import { Button } from "@/components/ui/button";
import { Eye, EyeOff } from "lucide-react";
import { useCameras, useManagedCameras } from "@/hooks/api";
import { useRealtimeByCamera } from "@/hooks/useRealtimeChannel";
import { logAction } from "@/lib/logger";
import { cn } from "@/lib/utils";
import type { DetectionFrame } from "@/types";

/** Live Camera — lưới 1/4/9/16 + Live Overlay realtime. */
export function LiveCameraPage() {
  const { data: managedCameras } = useManagedCameras();
  const { data: demoCameras } = useCameras();
  const cameras = managedCameras?.length
    ? managedCameras.filter((camera) => camera.enabled !== false)
    : (demoCameras ?? []);
  const sortedCameras = [...cameras].sort(
    (a, b) => Number(b.status === "online") - Number(a.status === "online") || a.camera_id - b.camera_id
  );
  const rawDetections = useRealtimeByCamera<DetectionFrame>("detection");
  const [grid, setGrid] = useState<GridSize>("all");
  const [overlay, setOverlay] = useState(true);

  const hasManaged = Boolean(managedCameras?.length);
  const detections = useMemo(() => {
    if (!hasManaged || !managedCameras?.length) return rawDetections;
    const ids = new Set(managedCameras.map((c) => c.camera_id));
    return Object.fromEntries(
      Object.entries(rawDetections).filter(([id]) => ids.has(Number(id)))
    );
  }, [rawDetections, hasManaged, managedCameras]);

  useEffect(() => {
    logAction("view_camera", "open live grid");
  }, []);

  const visibleCount = grid === "all" ? Math.max(16, sortedCameras.length) : grid;
  const cols = grid === "all" ? Math.ceil(Math.sqrt(visibleCount)) : Math.sqrt(grid);
  const rows = Math.ceil(visibleCount / cols);
  const compact = grid === "all" || grid === 16;

  const list = sortedCameras.slice(0, visibleCount);
  // Bổ sung ô trống nếu ít camera hơn lưới
  while (list.length < cols * rows) {
    list.push({ camera_id: -list.length - 1, name: "—", status: "offline", fps: 0 });
  }

  return (
    <div className="space-y-4">
      <PageHeader
        title="Live Camera"
        description="Xem trực tiếp nhiều camera với overlay AI"
        actions={
          <>
            <Button variant="outline" size="sm" onClick={() => setOverlay((v) => !v)}>
              {overlay ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              {overlay ? "Ẩn overlay" : "Hiện overlay"}
            </Button>
            <GridSelector value={grid} onChange={setGrid} allCount={sortedCameras.length} />
          </>
        }
      />
      <div
        className={cn("grid gap-2", compact && "h-[calc(100dvh-11rem)] min-h-[480px]")}
        style={{
          gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))`,
          gridTemplateRows: compact ? `repeat(${rows}, minmax(0, 1fr))` : undefined,
        }}
      >
        {list.map((cam, i) =>
          cam.camera_id > 0 ? (
            <CameraTile
              key={cam.camera_id}
              cameraId={cam.camera_id}
              cameraName={cam.name}
              frame={detections[cam.camera_id] ?? null}
              showOverlay={overlay}
              liveFeed={hasManaged}
              online={cam.status === "online"}
              compact={compact}
            />
          ) : (
            <div
              key={`empty-${i}`}
              className={cn("flex items-center justify-center rounded-lg border border-dashed text-xs text-muted-foreground", compact ? "h-full min-h-0" : "aspect-video")}
            >
              Không có camera
            </div>
          )
        )}
      </div>
    </div>
  );
}
