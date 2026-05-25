import { useEffect, useRef, useCallback, useState } from 'react';
import type { WsProgressMessage } from '../types/api';

interface UseWebSocketOptions {
  taskId: string | null;
  onMessage?: (msg: WsProgressMessage) => void;
  onError?: (error: Event) => void;
  enabled?: boolean;
}

export function useWebSocket({ taskId, onMessage, onError, enabled = true }: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WsProgressMessage | null>(null);

  const connect = useCallback(() => {
    if (!taskId || !enabled) return;

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsUrl = `${protocol}://${window.location.host}/ws/tasks/${taskId}`;
    const devWsUrl = `${protocol}://${window.location.host}/ws/tasks/${taskId}`;

    const ws = new WebSocket(import.meta.env.DEV ? devWsUrl : wsUrl);
    wsRef.current = ws;

    ws.onopen = () => setIsConnected(true);

    ws.onmessage = (event) => {
      try {
        const data: WsProgressMessage = JSON.parse(event.data);
        setLastMessage(data);
        onMessage?.(data);
      } catch {
        // ignore parse errors
      }
    };

    ws.onerror = (error) => onError?.(error);

    ws.onclose = () => {
      setIsConnected(false);
    };
  }, [taskId, enabled, onMessage, onError]);

  const disconnect = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
    setIsConnected(false);
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return { isConnected, lastMessage, disconnect };
}
