import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { RealtimeSocket } from "@/lib/ws";

/** WebSocket giả để kiểm thử pub/sub mà không cần server. */
class MockWebSocket {
  static instances: MockWebSocket[] = [];
  static OPEN = 1;
  readyState = MockWebSocket.OPEN;
  onopen: (() => void) | null = null;
  onmessage: ((ev: { data: string }) => void) | null = null;
  onerror: (() => void) | null = null;
  onclose: (() => void) | null = null;
  sent: string[] = [];

  constructor(public url: string) {
    MockWebSocket.instances.push(this);
    setTimeout(() => this.onopen?.(), 0);
  }
  send(data: string) {
    this.sent.push(data);
  }
  close() {
    this.onclose?.();
  }
  emit(channel: string, data: unknown) {
    this.onmessage?.({ data: JSON.stringify({ channel, data }) });
  }
}

describe("RealtimeSocket", () => {
  beforeEach(() => {
    MockWebSocket.instances = [];
    vi.stubGlobal("WebSocket", MockWebSocket);
  });
  afterEach(() => vi.unstubAllGlobals());

  it("gọi handler khi nhận message đúng channel", () => {
    const socket = new RealtimeSocket("ws://test/ws");
    const handler = vi.fn();
    socket.on("detection", handler);
    socket.connect();
    const ws = MockWebSocket.instances[0];
    ws.emit("detection", { camera_id: 1 });
    expect(handler).toHaveBeenCalledWith({ camera_id: 1 }, expect.any(Object));
  });

  it("không gọi handler với channel khác", () => {
    const socket = new RealtimeSocket("ws://test/ws");
    const handler = vi.fn();
    socket.on("alert", handler);
    socket.connect();
    MockWebSocket.instances[0].emit("system", { cpu_percent: 10 });
    expect(handler).not.toHaveBeenCalled();
  });

  it("unsubscribe gỡ handler", () => {
    const socket = new RealtimeSocket("ws://test/ws");
    const handler = vi.fn();
    const off = socket.on("tracking", handler);
    socket.connect();
    off();
    MockWebSocket.instances[0].emit("tracking", {});
    expect(handler).not.toHaveBeenCalled();
  });
});
