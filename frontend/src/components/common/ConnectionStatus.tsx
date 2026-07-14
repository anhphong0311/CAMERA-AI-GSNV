import { useWebSocket } from "@/contexts/WebSocketContext";
import { cn } from "@/lib/utils";
import { Wifi, WifiOff, Loader2 } from "lucide-react";

/**
 * Chỉ báo trạng thái kết nối WebSocket realtime.
 */
export function ConnectionStatus() {
  const { status } = useWebSocket();

  const map = {
    open: { label: "Realtime", icon: Wifi, cls: "text-success" },
    connecting: { label: "Đang kết nối", icon: Loader2, cls: "text-warning" },
    closed: { label: "Mất kết nối", icon: WifiOff, cls: "text-muted-foreground" },
    error: { label: "Lỗi kết nối", icon: WifiOff, cls: "text-destructive" },
  }[status];

  const Icon = map.icon;
  return (
    <div
      className={cn("flex items-center gap-1.5 text-xs font-medium", map.cls)}
      title={`WebSocket: ${status}`}
    >
      <Icon className={cn("h-4 w-4", status === "connecting" && "animate-spin")} />
      <span className="hidden md:inline">{map.label}</span>
    </div>
  );
}
