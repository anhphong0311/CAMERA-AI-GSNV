import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { RealtimeSocket, type ConnectionStatus } from "@/lib/ws";

interface WebSocketContextValue {
  socket: RealtimeSocket;
  status: ConnectionStatus;
}

const WebSocketContext = createContext<WebSocketContextValue | null>(null);

export function WebSocketProvider({ children }: { children: ReactNode }) {
  const socketRef = useRef<RealtimeSocket>();
  if (!socketRef.current) socketRef.current = new RealtimeSocket();
  const socket = socketRef.current;

  const [status, setStatus] = useState<ConnectionStatus>(socket.status);

  useEffect(() => {
    const off = socket.onStatus(setStatus);
    socket.connect();
    return () => {
      off();
      socket.close();
    };
  }, [socket]);

  const value = useMemo(() => ({ socket, status }), [socket, status]);
  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useWebSocket(): WebSocketContextValue {
  const ctx = useContext(WebSocketContext);
  if (!ctx) throw new Error("useWebSocket phải dùng trong WebSocketProvider");
  return ctx;
}
