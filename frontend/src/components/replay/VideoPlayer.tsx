import { useRef, useState } from "react";
import {
  Download,
  Maximize2,
  Pause,
  Play,
  RotateCcw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { logAction } from "@/lib/logger";
import { formatDuration } from "@/lib/utils";

const SPEEDS = [0.5, 1, 1.5, 2] as const;

/**
 * VideoPlayer — trình phát video bằng chứng: Seek / Speed / Pause / Fullscreen / Download.
 */
export function VideoPlayer({
  src,
  title,
}: {
  src?: string;
  title?: string;
}) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const wrapRef = useRef<HTMLDivElement>(null);
  const [playing, setPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState(0);
  const [speed, setSpeed] = useState(1);

  const toggle = () => {
    const v = videoRef.current;
    if (!v) return;
    if (v.paused) {
      void v.play();
      setPlaying(true);
    } else {
      v.pause();
      setPlaying(false);
    }
  };

  const seek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = videoRef.current;
    if (!v) return;
    v.currentTime = Number(e.target.value);
    setProgress(v.currentTime);
  };

  const changeSpeed = () => {
    const idx = SPEEDS.indexOf(speed as (typeof SPEEDS)[number]);
    const next = SPEEDS[(idx + 1) % SPEEDS.length];
    setSpeed(next);
    if (videoRef.current) videoRef.current.playbackRate = next;
  };

  const download = () => {
    if (!src) return;
    const a = document.createElement("a");
    a.href = src;
    a.download = title || "evidence.mp4";
    a.click();
    logAction("download", `video ${title ?? src}`);
  };

  return (
    <div ref={wrapRef} className="overflow-hidden rounded-lg border bg-black">
      <div className="relative aspect-video">
        {src ? (
          <video
            ref={videoRef}
            src={src}
            className="h-full w-full"
            onTimeUpdate={(e) => setProgress(e.currentTarget.currentTime)}
            onLoadedMetadata={(e) => setDuration(e.currentTarget.duration)}
            onEnded={() => setPlaying(false)}
          />
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
            Chọn một sự kiện để xem video bằng chứng
          </div>
        )}
      </div>
      <div className="flex items-center gap-2 bg-card px-3 py-2">
        <Button size="sm" variant="ghost" onClick={toggle} disabled={!src}>
          {playing ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
        </Button>
        <Button
          size="sm"
          variant="ghost"
          onClick={() => {
            if (videoRef.current) {
              videoRef.current.currentTime = 0;
              setProgress(0);
            }
          }}
          disabled={!src}
        >
          <RotateCcw className="h-4 w-4" />
        </Button>
        <input
          type="range"
          min={0}
          max={duration || 0}
          value={progress}
          onChange={seek}
          disabled={!src}
          className="h-1 flex-1 cursor-pointer accent-primary"
        />
        <span className="w-24 text-right text-xs tabular-nums text-muted-foreground">
          {formatDuration(progress)} / {formatDuration(duration)}
        </span>
        <Button size="sm" variant="outline" className="h-7 w-12 text-xs" onClick={changeSpeed} disabled={!src}>
          {speed}x
        </Button>
        <Button size="sm" variant="ghost" onClick={() => wrapRef.current?.requestFullscreen?.()} disabled={!src}>
          <Maximize2 className="h-4 w-4" />
        </Button>
        <Button size="sm" variant="ghost" onClick={download} disabled={!src}>
          <Download className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
