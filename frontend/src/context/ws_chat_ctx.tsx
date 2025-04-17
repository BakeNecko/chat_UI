import React, { createContext, useContext, useEffect, useState, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { ChatMsgResponse, NotifyMsg } from '../client';
import { isLoggedIn } from '../hooks/useAuth';

interface WebSocketContextType {
  socket: WebSocket | null;
  sendMessage: (message: string, type: string, receiverId: string | number) => void;
  subscribeToMessages: (callback: (message: ChatMsgResponse) => void) => void;
  unsubscribeFromMessages: (callback: (message: ChatMsgResponse) => void) => void;
  connectionStatus: 'connecting' | 'connected' | 'disconnected';
  notifications: NotifyMsg[];
  setNotifications: React.Dispatch<React.SetStateAction<NotifyMsg[]>>;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [subscribers, setSubscribers] = useState<((message: ChatMsgResponse) => void)[]>([]);
  const [notifications, setNotifications] = useState<NotifyMsg[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  const subscribersRef = useRef<((message: ChatMsgResponse) => void)[]>([]);

  useEffect(() => {
    subscribersRef.current = subscribers;
  }, [subscribers]);

  const createWebSocket = () => {
    if (!isLoggedIn()) {
      console.warn('No access token found. Cannot establish WebSocket connection.');
      setConnectionStatus('disconnected');
      return null;
    }

    const jwt_token = localStorage.getItem("access_token") || "";
    const ws = new WebSocket('ws://localhost:8000/api/v1/ws/chat');

    ws.onopen = () => {
      console.log('WebSocket соединение установлено');
      setConnectionStatus('connected');
      ws.send(JSON.stringify({ type: 'init', content: jwt_token }));
    };

    ws.onmessage = (event: MessageEvent) => {
      let newMessage = event.data;
      let counter = 0; 
      const maxIterations = 10;
    
      while (typeof newMessage === 'string' && counter < maxIterations) {
        try {
          newMessage = JSON.parse(newMessage);
        } catch (error) {
          console.error('Ошибка при парсинге сообщения:', error);
          return;
        }
        counter++;
      }
    
      if (counter >= maxIterations) {
        console.error('Достигнуто максимальное количество итераций при парсинге JSON.');
        return;
      }
      if ('type' in newMessage) {
        setNotifications(prev => [...prev, newMessage as NotifyMsg]);
      } else {
        subscribersRef.current.forEach(callback => callback(newMessage as ChatMsgResponse));
      }
    };

    ws.onclose = () => {
      console.log('WebSocket connection closed');
      setConnectionStatus('disconnected');
      attemptReconnect();
    };

    ws.onerror = (error: Event) => {
      console.error('WebSocket ошибка:', error);
      setConnectionStatus('disconnected');
    };

    return ws;
  };

  const attemptReconnect = () => {
    if (isLoggedIn()) {
      console.log('Attempting to reconnect...');
      setTimeout(() => {
        const newSocket = createWebSocket();
        if (newSocket) {
          setSocket(newSocket);
        }
      }, 5000);
    }
  };

  const subscribeToMessages = (callback: (message: ChatMsgResponse) => void) => {
    setSubscribers(prev => [...prev, callback]);
  };

  const unsubscribeFromMessages = (callback: (message: ChatMsgResponse) => void) => {
    setSubscribers(prev => prev.filter(subscriber => subscriber !== callback));
  };

  useEffect(() => {
    if (isLoggedIn() && !socket) {
      console.log('Attempting to create WebSocket connection...');
      const newSocket = createWebSocket();
      if (newSocket) {
        setSocket(newSocket);
      }
    } else if (!isLoggedIn() && socket) {
      console.log('User  is not logged in. Closing WebSocket connection...');
      socket.close();
      setConnectionStatus('disconnected');
      setSubscribers([]);
      setSocket(null);
    }
  }, [socket]);

  const sendMessage = (message: string, type: string, receiverId: string | number) => {
    const message_uuid = uuidv4();
    const msg_data = { type, content: message, receiver_id: receiverId, message_uuid };
    
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(msg_data));
    } else {
      console.error('WebSocket is not open. Attempting to reconnect...');
    }
  };

  return (
    <WebSocketContext.Provider value={{ 
      socket, 
      connectionStatus,
      notifications,
      sendMessage, 
      subscribeToMessages, 
      unsubscribeFromMessages, 
      setNotifications,
      }}>
      {children}
    </WebSocketContext.Provider>
  );
};