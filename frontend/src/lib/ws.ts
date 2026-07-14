import type { WsChannel, WsMessage } from "@/types";

/**
 * RealtimeSocket — client WebSocket native (tương thích FastAPI WebSocket).
 *
 * Ghi chú kiến trúc: spec liệt kê "Socket.IO Client", nhưng backend dùng
 * FastAPI WebSocket thuần (không phải Socket.IO server). Vì vậy client dùng
 * WebSocket API chuẩn của trình duyệt — interop đúng với backend. Lớp này
 * đóng gói: auto-reconnect (backoff), heartbeat ping, và pub/sub theo channel.
 */

export type ConnectionStatus = "connecting" | "open" | "closed" | "error";

type Handler = (data: unknown, msg: WsMessage) => void;
type StatusHandler = (status: ConnectionStatus) => void;

export class RealtimeSocket {
  private url: string;
  private ws: WebSocket | null = null;
  private handlers = new Map<WsChannel | "*", Set<Handler>>();
  private statusHandlers = new Set<StatusHandler>();
  private reconnectAttempts = 0;
  private heartbeat?: ReturnType<typeof setInterval>;
  private closedByUser = false;
  private _status: ConnectionStatus = "closed";

  constructor(url?: string) {
    this.url =
      url ||
      import.meta.env.VITE_WS_URL ||
      `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/api/v1/ws`;
  }

  get status(): ConnectionStatus {
    return this._status;
  }

  private setStatus(s: ConnectionStatus) {
    this._status = s;
    this.statusHandlers.forEach((h) => h(s));
  }

  connect(): void {
    this.closedByUser = false;
    this.open();
  }

  private open(): void {
    try {
      this.setStatus("connecting");
      this.ws = new WebSocket(this.url);
    } catch {
      this.scheduleReconnect();
      return;
    }

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.setStatus("open");
      this.heartbeat = setInterval(() => this.send("ping"), 25_000);
    };

    this.ws.onmessage = (ev) => {
      let msg: WsMessage;
      try {
        msg = JSON.parse(ev.data as string) as WsMessage;
      } catch {
        return;
      }
      this.handlers.get(msg.channel)?.forEach((h) => h(msg.data, msg));
      this.handlers.get("*")?.forEach((h) => h(msg.data, msg));
    };

    this.ws.onerror = () => this.setStatus("error");

    this.ws.onclose = () => {
      this.cleanup();
      this.setStatus("closed");
      if (!this.closedByUser) this.scheduleReconnect();
    };
  }

  private scheduleReconnect(): void {
    this.reconnectAttempts += 1;
    const delay = Math.min(1000 * 2 ** this.reconnectAttempts, 15_000);
    setTimeout(() => {
      if (!this.closedByUser) this.open();
    }, delay);
  }

  private cleanup(): void {
    if (this.heartbeat) clearInterval(this.heartbeat);
    this.heartbeat = undefined;
  }

  send(data: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) this.ws.send(data);
  }

  on(channel: WsChannel | "*", handler: Handler): () => void {
    if (!this.handlers.has(channel)) this.handlers.set(channel, new Set());
    this.handlers.get(channel)!.add(handler);
    return () => this.handlers.get(channel)?.delete(handler);
  }

  onStatus(handler: StatusHandler): () => void {
    this.statusHandlers.add(handler);
    handler(this._status);
    return () => this.statusHandlers.delete(handler);
  }

  close(): void {
    this.closedByUser = true;
    this.cleanup();
    this.ws?.close();
    this.ws = null;
  }
}
