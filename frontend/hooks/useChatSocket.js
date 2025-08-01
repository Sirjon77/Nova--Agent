import { useEffect, useRef } from 'react';

export const useChatSocket = (onMessage) => {
  const wsRef = useRef(null);

  useEffect(() => {
    const ws = new WebSocket(`ws://${window.location.host}/ws/chat`);
    ws.onopen = () => console.log("🔌 Chat WebSocket connected");
    ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        onMessage(data);
      } catch (_) {}
    };
    ws.onerror = (e) => console.error("WebSocket error", e);
    wsRef.current = ws;
    return () => ws.close();
  }, [onMessage]);

  const send = (payload) => {
    if (wsRef.current?.readyState === 1) {
      wsRef.current.send(JSON.stringify(payload));
    }
  };

  return { send };
};