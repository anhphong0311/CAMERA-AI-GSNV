import { useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export interface HeatPoint {
  x: number; // 0..1
  y: number; // 0..1
  weight: number; // 0..1
}

/**
 * HeatmapChart — bản đồ nhiệt điểm nóng hành vi (Phone/Talking/Eating/...).
 * Vẽ gradient hướng tâm trên canvas theo mật độ điểm.
 */
export function HeatmapChart({
  title,
  points,
}: {
  title: string;
  points: HeatPoint[];
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;
    const W = (canvas.width = canvas.clientWidth);
    const H = (canvas.height = canvas.clientHeight);

    ctx.fillStyle = "#0b1220";
    ctx.fillRect(0, 0, W, H);

    // Lớp mật độ (grayscale alpha)
    points.forEach((p) => {
      const radius = 40 + p.weight * 40;
      const g = ctx.createRadialGradient(
        p.x * W,
        p.y * H,
        0,
        p.x * W,
        p.y * H,
        radius
      );
      g.addColorStop(0, `rgba(255,0,0,${0.35 * p.weight + 0.1})`);
      g.addColorStop(0.5, `rgba(255,165,0,${0.2 * p.weight})`);
      g.addColorStop(1, "rgba(0,0,255,0)");
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.arc(p.x * W, p.y * H, radius, 0, Math.PI * 2);
      ctx.fill();
    });
  }, [points]);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <canvas ref={canvasRef} className="aspect-video w-full rounded-lg border" />
        <div className="mt-2 flex items-center gap-3 text-xs text-muted-foreground">
          <span className="inline-flex items-center gap-1">
            <span className="h-3 w-3 rounded-full bg-blue-500/60" /> Thấp
          </span>
          <span className="inline-flex items-center gap-1">
            <span className="h-3 w-3 rounded-full bg-orange-500/60" /> Trung bình
          </span>
          <span className="inline-flex items-center gap-1">
            <span className="h-3 w-3 rounded-full bg-red-500/70" /> Cao
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
