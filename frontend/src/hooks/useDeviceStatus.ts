/**
 * 장비 상태 실시간 수신 훅
 * WebSocket을 통해 장비 상태 업데이트를 수신
 */

import { useEffect, useState, useRef, useCallback } from 'react';
import { DeviceStatus } from '@/lib/api';

interface DeviceStatusUpdate {
  type: string;
  device_id: number;
  device_name?: string;
  is_online?: boolean;
  battery_level?: number;
  memory_usage?: number;
  temperature?: number;
  cpu_usage?: number;
  camera_status?: 'active' | 'paused' | 'stopped';
  mic_status?: 'active' | 'paused' | 'stopped';
  timestamp?: string;
}

interface UseDeviceStatusOptions {
  deviceId?: number;
  onStatusUpdate?: (status: DeviceStatusUpdate) => void;
  onOnlineStatusChange?: (deviceId: number, isOnline: boolean) => void;
}

interface UseDeviceStatusReturn {
  isConnected: boolean;
  lastStatus: DeviceStatusUpdate | null;
  onlineDevices: Set<number>;
  subscribeDevice: (deviceId: number) => void;
  unsubscribeDevice: (deviceId: number) => void;
}

export function useDeviceStatus(options: UseDeviceStatusOptions = {}): UseDeviceStatusReturn {
  const { deviceId, onStatusUpdate, onOnlineStatusChange } = options;
  
  const [isConnected, setIsConnected] = useState(false);
  const [lastStatus, setLastStatus] = useState<DeviceStatusUpdate | null>(null);
  const [onlineDevices, setOnlineDevices] = useState<Set<number>>(new Set());
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  const subscribedDevicesRef = useRef<Set<number>>(new Set());
  
  const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      // 토큰 가져오기 (localStorage에서)
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      const wsUrl = token ? `${WS_URL}?token=${token}` : WS_URL;
      
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('[WebSocket] 연결됨');
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;
        
        // 이전에 구독했던 장비 다시 구독
        subscribedDevicesRef.current.forEach(id => {
          sendMessage({ type: 'subscribe_device', device_id: id });
        });
        
        // 특정 장비 ID가 지정되었으면 자동 구독
        if (deviceId) {
          subscribeDevice(deviceId);
        }
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleMessage(message);
        } catch (error) {
          console.error('[WebSocket] 메시지 파싱 오류:', error);
        }
      };

      wsRef.current.onclose = (event) => {
        console.log('[WebSocket] 연결 종료:', event.code, event.reason);
        setIsConnected(false);
        
        // 자동 재연결 (최대 시도 횟수 제한)
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
          reconnectAttemptsRef.current += 1;
          console.log(`[WebSocket] ${delay}ms 후 재연결 시도 (${reconnectAttemptsRef.current}/${maxReconnectAttempts})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('[WebSocket] 오류:', error);
      };
    } catch (error) {
      console.error('[WebSocket] 연결 실패:', error);
    }
  }, [deviceId, WS_URL]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setIsConnected(false);
  }, []);

  const sendMessage = useCallback((message: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  const subscribeDevice = useCallback((id: number) => {
    subscribedDevicesRef.current.add(id);
    sendMessage({ type: 'subscribe_device', device_id: id });
  }, [sendMessage]);

  const unsubscribeDevice = useCallback((id: number) => {
    subscribedDevicesRef.current.delete(id);
    sendMessage({ type: 'unsubscribe_device', device_id: id });
  }, [sendMessage]);

  const handleMessage = useCallback((message: any) => {
    switch (message.type) {
      case 'connected':
        console.log('[WebSocket] 서버 연결 확인:', message);
        break;
        
      case 'subscribed':
        console.log('[WebSocket] 장비 구독 완료:', message.device_id);
        break;
        
      case 'unsubscribed':
        console.log('[WebSocket] 장비 구독 해제:', message.device_id);
        break;
        
      case 'device_status':
        // 장비 상태 업데이트
        setLastStatus(message);
        
        // 온라인 상태 업데이트
        if (message.device_id) {
          setOnlineDevices(prev => {
            const newSet = new Set(prev);
            if (message.is_online !== false) {
              newSet.add(message.device_id);
            } else {
              newSet.delete(message.device_id);
            }
            return newSet;
          });
        }
        
        // 콜백 호출
        if (onStatusUpdate) {
          onStatusUpdate(message);
        }
        break;
        
      case 'device_online_status':
        // 온라인/오프라인 상태 변경
        if (message.device_id !== undefined && message.is_online !== undefined) {
          setOnlineDevices(prev => {
            const newSet = new Set(prev);
            if (message.is_online) {
              newSet.add(message.device_id);
            } else {
              newSet.delete(message.device_id);
            }
            return newSet;
          });
          
          if (onOnlineStatusChange) {
            onOnlineStatusChange(message.device_id, message.is_online);
          }
        }
        break;
        
      case 'pong':
        // Ping 응답
        break;
        
      case 'error':
        console.error('[WebSocket] 서버 오류:', message.message);
        break;
        
      default:
        console.log('[WebSocket] 알 수 없는 메시지:', message);
    }
  }, [onStatusUpdate, onOnlineStatusChange]);

  // 연결 시작 및 정리
  useEffect(() => {
    connect();
    
    // Ping 전송 (30초마다)
    const pingInterval = setInterval(() => {
      sendMessage({ type: 'ping' });
    }, 30000);
    
    return () => {
      clearInterval(pingInterval);
      disconnect();
    };
  }, [connect, disconnect, sendMessage]);

  return {
    isConnected,
    lastStatus,
    onlineDevices,
    subscribeDevice,
    unsubscribeDevice,
  };
}

export default useDeviceStatus;
