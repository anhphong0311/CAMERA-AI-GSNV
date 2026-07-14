import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Check, Eraser, Pentagon, Square } from "lucide-react";
import type { ROI, ROIPoint } from "@/types";

type Mode = "polygon" | "rectangle";

/**
 * ROICanvas — vẽ vùng quan tâm (Polygon / Rectangle) trên nền camera.
 *
 * Toạ độ chuẩn hoá 0..1 (không phụ thuộc kích thước hiển thị). Emit ROI mới
 * qua onCreate; hiển thị các ROI đã lưu.
 */
export function ROICanvas({
  rois,
  onCreate,
}: {
  rois: ROI[];
  onCreate: (points: ROIPoint[], type: Mode) => void;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [mode, setMode] = useState<Mode>("polygon");
  const [points, setPoints] = useState<ROIPoint[]>([]);
  const [rectStart, setRectStart] = useState<ROIPoint | null>(null);
  const [hover, setHover] = useState<ROIPoint | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;
    const W = (canvas.width = canvas.clientWidth);
    const H = (canvas.height = canvas.clientHeight);
    ctx.fillStyle = "#0b1220";
    ctx.fillRect(0, 0, W, H);
    ctx.strokeStyle = "rgba(148,163,184,0.1)";
    for (let x = 0; x < W; x += 40) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, H);
      ctx.stroke();
    }
    for (let y = 0; y < H; y += 40) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(W, y);
      ctx.stroke();
    }

    const drawPoly = (pts: ROIPoint[], color: string, name?: string) => {
      if (pts.length === 0) return;
      ctx.beginPath();
      pts.forEach((p, i) => {
        const x = p.x * W;
        const y = p.y * H;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.closePath();
      ctx.fillStyle = color + "33";
      ctx.fill();
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.stroke();
      pts.forEach((p) => {
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(p.x * W, p.y * H, 3, 0, Math.PI * 2);
        ctx.fill();
      });
      if (name) {
        ctx.fillStyle = color;
        ctx.font = "12px sans-serif";
        ctx.fillText(name, pts[0].x * W + 4, pts[0].y * H - 4);
      }
    };

    rois.forEach((r) => drawPoly(r.points, "#38bdf8", r.name));

    // ROI đang vẽ
    if (mode === "polygon") {
      const preview = hover ? [...points, hover] : points;
      drawPoly(preview, "#22c55e");
    } else if (rectStart && hover) {
      const rect: ROIPoint[] = [
        rectStart,
        { x: hover.x, y: rectStart.y },
        hover,
        { x: rectStart.x, y: hover.y },
      ];
      drawPoly(rect, "#22c55e");
    }
  }, [rois, points, hover, rectStart, mode]);

  const toNorm = (e: React.MouseEvent): ROIPoint => {
    const rect = canvasRef.current!.getBoundingClientRect();
    return {
      x: +((e.clientX - rect.left) / rect.width).toFixed(4),
      y: +((e.clientY - rect.top) / rect.height).toFixed(4),
    };
  };

  const handleClick = (e: React.MouseEvent) => {
    const p = toNorm(e);
    if (mode === "polygon") {
      setPoints((prev) => [...prev, p]);
    } else if (!rectStart) {
      setRectStart(p);
    } else {
      onCreate(
        [
          rectStart,
          { x: p.x, y: rectStart.y },
          p,
          { x: rectStart.x, y: p.y },
        ],
        "rectangle"
      );
      setRectStart(null);
      setHover(null);
    }
  };

  const finishPolygon = () => {
    if (points.length >= 3) {
      onCreate(points, "polygon");
      setPoints([]);
      setHover(null);
    }
  };

  const clear = () => {
    setPoints([]);
    setRectStart(null);
    setHover(null);
  };

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        <Button
          size="sm"
          variant={mode === "polygon" ? "default" : "outline"}
          onClick={() => {
            setMode("polygon");
            clear();
          }}
        >
          <Pentagon className="h-4 w-4" /> Polygon
        </Button>
        <Button
          size="sm"
          variant={mode === "rectangle" ? "default" : "outline"}
          onClick={() => {
            setMode("rectangle");
            clear();
          }}
        >
          <Square className="h-4 w-4" /> Rectangle
        </Button>
        {mode === "polygon" && (
          <Button size="sm" variant="secondary" onClick={finishPolygon} disabled={points.length < 3}>
            <Check className="h-4 w-4" /> Hoàn tất ({points.length})
          </Button>
        )}
        <Button size="sm" variant="ghost" onClick={clear}>
          <Eraser className="h-4 w-4" /> Xoá nháp
        </Button>
      </div>
      <canvas
        ref={canvasRef}
        onClick={handleClick}
        onMouseMove={(e) => setHover(toNorm(e))}
        onMouseLeave={() => setHover(null)}
        className="aspect-video w-full cursor-crosshair rounded-lg border"
      />
      <p className="text-xs text-muted-foreground">
        {mode === "polygon"
          ? "Click để thêm điểm, bấm Hoàn tất để lưu polygon."
          : "Click điểm đầu rồi click điểm đối diện để tạo hình chữ nhật."}
      </p>
    </div>
  );
}
