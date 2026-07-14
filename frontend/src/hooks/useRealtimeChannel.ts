import { useEffect, useRef, useState } from "react";
import { useWebSocket } from "@/contexts/WebSocketContext";
import type { WsChannel } from "@/types";

/**
 * Đăng ký một channel WebSocket, trả về payload mới nhất.
 */
export function useRealtimeChannel<T>(channel: WsChannel): T | null {
  const { socket } = useWebSocket();
  const [data, setData] = useState<T | null>(null);
  useEffect(() => socket.on(channel, (d) => setData(d as T)), [socket, channel]);
  return data;
}

/**
 * Tích lũy payload từ một channel thành danh sách (mới nhất ở đầu).
 */
export function useRealtimeFeed<T>(channel: WsChannel, max = 100): T[] {
  const { socket } = useWebSocket();
  const [items, setItems] = useState<T[]>([]);
  useEffect(
    () =>
      socket.on(channel, (d) => {
        setItems((prev) => [d as T, ...prev].slice(0, max));
      }),
    [socket, channel, max]
  );
  return items;
}

/**
 * Gom payload theo camera_id (dùng cho detection/tracking nhiều camera).
 */
export function useRealtimeByCamera<T extends { camera_id: number }>(
  channel: WsChannel
): Record<number, T> {
  const { socket } = useWebSocket();
  const ref = useRef<Record<number, T>>({});
  const [map, setMap] = useState<Record<number, T>>({});
  useEffect(
    () =>
      socket.on(channel, (d) => {
        const frame = d as T;
        ref.current = { ...ref.current, [frame.camera_id]: frame };
        setMap(ref.current);
      }),
    [socket, channel]
  );
  return map;
}
