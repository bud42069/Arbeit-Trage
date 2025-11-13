import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * Custom hook for WebSocket connection to backend gateway
 * Handles reconnection, message parsing, and real-time updates
 */
export const useWebSocket = (url) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttempts = useRef(0);

  const connect = useCallback(() => {
    try {
      // Close existing connection
      if (wsRef.current) {
        wsRef.current.close();
      }

      console.log(`[WebSocket] Attempting to connect to: ${url}`);
      
      // Create WebSocket connection
      const ws = new WebSocket(url);
      
      ws.onopen = () => {
        console.log('[WebSocket] Connected successfully');
        setIsConnected(true);
        reconnectAttempts.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log('[WebSocket] Received message:', message.type);
          setLastMessage(message);
        } catch (error) {
          console.error('[WebSocket] Failed to parse message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('[WebSocket] Connection error:', error);
      };

      ws.onclose = (event) => {
        console.log(`[WebSocket] Disconnected - Code: ${event.code}, Reason: ${event.reason}`);
        setIsConnected(false);
        
        // Attempt reconnection with exponential backoff
        reconnectAttempts.current += 1;
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
        
        console.log(`[WebSocket] Will reconnect in ${delay}ms (attempt ${reconnectAttempts.current})`);
        
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, delay);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('[WebSocket] Failed to create connection:', error);
    }
  }, [url]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  const sendMessage = useCallback((message) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  return {
    isConnected,
    lastMessage,
    sendMessage
  };
};

/**
 * Hook for subscribing to specific event types from WebSocket
 */
export const useWebSocketSubscription = (eventType, onMessage) => {
  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
  const wsUrl = backendUrl.replace('http', 'ws') + '/api/ws';
  
  const { lastMessage, isConnected } = useWebSocket(wsUrl);

  useEffect(() => {
    if (lastMessage && lastMessage.type === eventType && onMessage) {
      onMessage(lastMessage.data);
    }
  }, [lastMessage, eventType, onMessage]);

  return { isConnected };
};
