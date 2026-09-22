import { useEffect, useRef, useState } from "react";
import { Camera as CameraIcon, Maximize2, Pause, Play, ZoomIn } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { logAction } from "@/lib/logger";
import { useCameraFrame } from "@/hooks/api";
import type { DetectionFrame } from "@/types";

/**
 * CameraTile — vẽ frame RTSP (JPEG poll) hoặc nền mô phỏng + Live Overlay.
 * Chỉ redraw khi có frame/overlay mới (không RAF liên tục).
 */
export function CameraTile({
  cameraId,
  cameraName,
  frame,
  showOverlay = true,
  liveFeed = true,
  online = true,
  compact = false,
}: {
  cameraId: number;
  cameraName: string;
  frame: DetectionFrame | null;
  showOverlay?: boolean;
  liveFeed?: boolean;
  online?: boolean;
  compact?: boolean;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wrapRef = useRef<HTMLDivElement>(null);
  const frameRef = useRef<DetectionFrame | null>(frame);
  const videoImgRef = useRef<HTMLImageElement | null>(null);
  const [paused, setPaused] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [videoReady, setVideoReady] = useState(0);
  const { data: liveFrame } = useCameraFrame(cameraId, liveFeed && online);

  frameRef.current = frame;

  useEffect(() => {
    if (!liveFrame?.image_base64) return;
    const img = new Image();
    img.onload = () => {
      videoImgRef.current = img;
      setVideoReady((n) => n + 1);
    };
    img.src = `data:image/jpeg;base64,${liveFrame.image_base64}`;
  }, [liveFrame?.image_base64, liveFrame?.frame_id]);

  useEffect(() => {
    if (online) return;
    videoImgRef.current = null;
    setVideoReady((n) => n + 1);
  }, [online]);

  useEffect(() => {
    if (paused) return;
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;

    const W = (canvas.width = canvas.clientWidth);
    const H = (canvas.height = canvas.clientHeight);
    const videoImg = videoImgRef.current;
    if (videoImg?.complete && videoImg.naturalWidth > 0) {
      ctx.drawImage(videoImg, 0, 0, W, H);
    } else {
      const grd = ctx.createLinearGradient(0, 0, 0, H);
      grd.addColorStop(0, "#0b1220");
      grd.addColorStop(1, "#1e293b");
      ctx.fillStyle = grd;
      ctx.fillRect(0, 0, W, H);
      if (liveFeed && !liveFrame) {
        ctx.fillStyle = "rgba(148,163,184,0.6)";
        ctx.font = "12px sans-serif";
        ctx.fillText(online ? "Đang kết nối RTSP..." : "Camera đang offline", 12, H / 2);
      }
    }

    const f = frameRef.current;
    if (showOverlay && f) {
      for (const o of f.objects) {
        const [x, y, w, h] = o.bbox;
        const px = x * W;
        const py = y * H;
        const pw = w * W;
        const ph = h * H;
        const isPerson = o.label === "person";
        const isPhone = o.label === "phone";
        const interacting = Boolean(o.interacting);
        ctx.lineWidth = interacting ? 3 : 2;
        if (isPhone && interacting) {
          ctx.strokeStyle = "#ef4444";
        } else if (isPhone) {
          ctx.strokeStyle = "#f59e0b";
        } else if (isPerson && interacting) {
          ctx.strokeStyle = "#f97316";
        } else if (isPerson) {
          ctx.strokeStyle = "#22c55e";
        } else {
          ctx.strokeStyle = "#f59e0b";
        }
        ctx.strokeRect(px, py, pw, ph);
        const suffix = interacting
          ? isPhone
            ? " (cầm)"
            : " (phone)"
          : "";
        const label =
          (o.track_id != null ? `#${o.track_id} ` : "") +
          `${o.label}${suffix} ${(o.confidence * 100).toFixed(0)}%`;
        ctx.font = "11px sans-serif";
        const tw = ctx.measureText(label).width + 8;
        ctx.fillStyle = ctx.strokeStyle as string;
        ctx.fillRect(px, Math.max(0, py - 14), tw, 14);
        ctx.fillStyle = "#0b1220";
        ctx.fillText(label, px + 4, Math.max(10, py - 3));
      }
      if (f.phone_interaction) {
        ctx.fillStyle = "rgba(239,68,68,0.85)";
        ctx.font = "bold 11px sans-serif";
        ctx.fillText("📱 Điện thoại", 8, H - 8);
      }
    }
  }, [paused, showOverlay, liveFeed, online, liveFrame, frame, videoReady]);

  const screenshot = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const a = document.createElement("a");
    a.href = canvas.toDataURL("image/png");
    a.download = `snapshot_cam${cameraId}_${Date.now()}.png`;
    a.click();
    logAction("download", `snapshot camera ${cameraId}`);
  };

  const fullscreen = () => {
    wrapRef.current?.requestFullscreen?.();
    logAction("view_camera", `fullscreen camera ${cameraId}`);
  };

  return (
    <div
      ref={wrapRef}
      className={cn("group relative overflow-hidden rounded-lg border bg-black", compact && "h-full min-h-0")}
    >
      <canvas
        ref={canvasRef}
        className={cn("w-full origin-center transition-transform", compact ? "h-full" : "aspect-video")}
        style={{ transform: `scale(${zoom})` }}
      />

      {/* Overlay: tên camera + timestamp + FPS + ROI */}
      {showOverlay && (
        <>
          <div className="pointer-events-none absolute left-2 top-2 rounded bg-black/60 px-2 py-1 text-xs font-medium text-white">
            {cameraName}
          </div>
          <div className="pointer-events-none absolute right-2 top-2 rounded bg-black/60 px-2 py-1 text-[10px] text-white">
            {new Date(frame?.ts ?? Date.now()).toLocaleTimeString("vi-VN")}
          </div>
          <div className="pointer-events-none absolute left-2 bottom-2 rounded bg-emerald-600/80 px-2 py-0.5 text-[10px] font-semibold text-white">
            FPS {frame?.fps?.toFixed(0) ?? "--"}
          </div>
          {frame?.objects[0]?.roi && (
            <div className="pointer-events-none absolute right-2 bottom-2 rounded bg-sky-600/80 px-2 py-0.5 text-[10px] font-semibold text-white">
              ROI {frame.objects[0].roi}
            </div>
          )}
        </>
      )}

      {/* Controls */}
      <div className="absolute inset-x-0 bottom-0 flex items-center justify-center gap-1 bg-gradient-to-t from-black/70 to-transparent p-2 opacity-0 transition-opacity group-hover:opacity-100">
        <Button
          size="sm"
          variant="secondary"
          className="h-7 px-2"
          onClick={() => setPaused((p) => !p)}
        >
          {paused ? <Play className="h-3.5 w-3.5" /> : <Pause className="h-3.5 w-3.5" />}
        </Button>
        <Button size="sm" variant="secondary" className="h-7 px-2" onClick={screenshot}>
          <CameraIcon className="h-3.5 w-3.5" />
        </Button>
        <Button
          size="sm"
          variant="secondary"
          className="h-7 px-2"
          onClick={() => setZoom((z) => (z >= 2 ? 1 : +(z + 0.5).toFixed(1)))}
        >
          <ZoomIn className="h-3.5 w-3.5" />
        </Button>
        <Button size="sm" variant="secondary" className="h-7 px-2" onClick={fullscreen}>
          <Maximize2 className="h-3.5 w-3.5" />
        </Button>
      </div>

      {paused && (
        <div className={cn("absolute inset-0 flex items-center justify-center bg-black/40")}>
          <span className="rounded bg-black/70 px-3 py-1 text-xs text-white">PAUSED</span>
        </div>
      )}
    </div>
  );
}
