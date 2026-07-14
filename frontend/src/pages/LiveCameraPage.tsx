import { useEffect, useMemo, useState } from "react";
import { PageHeader } from "@/components/common/PageHeader";
import { GridSelector } from "@/components/camera/GridSelector";
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
  const cameras = managedCameras?.length ? managedCameras : demoCameras;
  const rawDetections = useRealtimeByCamera<DetectionFrame>("detection");
  const [grid, setGrid] = useState(4);
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

  const cols = useMemo(() => Math.sqrt(grid), [grid]);

  const list = (cameras ?? []).slice(0, grid);
  // Bổ sung ô trống nếu ít camera hơn lưới
  while (list.length < grid) {
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
            <GridSelector value={grid} onChange={setGrid} />
          </>
        }
      />
      <div
        className={cn("grid gap-3")}
        style={{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }}
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
            />
          ) : (
            <div
              key={`empty-${i}`}
              className="flex aspect-video items-center justify-center rounded-lg border border-dashed text-xs text-muted-foreground"
            >
              Không có camera
            </div>
          )
        )}
      </div>
    </div>
  );
}
