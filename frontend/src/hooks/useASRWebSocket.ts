/**
 * ASR WebSocket Hook
 * 
 * 음성인식 서버와 WebSocket 통신을 관리하는 커스텀 Hook
 * 
 * 주요 기능:
 * - WebSocket 연결/해제
 * - 인식 결과 수신 및 상태 관리
 * - 자동 재연결
 * - 에러 처리
 * 
 * 참고:
 * - WebSocket URL은 백엔드 API에서 받아옴
 * - 인식 결과는 RecognitionResult 타입으로 전달
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { RecognitionResult } from '@/lib/api';

export interface UseASRWebSocketOptions {
  wsUrl: string | null;
  enabled?: boolean;
  onResult?: (result: RecognitionResult) => void;
  onProcessing?: (isProcessing: boolean) => void;
  onError?: (error: Error) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

export interface UseASRWebSocketReturn {
  isConnected: boolean;
  isConnecting: boolean;
  isProcessing: boolean;
  error: Error | null;
  results: RecognitionResult[];
  connect: () => void;
  disconnect: () => void;
  clearResults: () => void;
}

export function useASRWebSocket({
  wsUrl,
  enabled = true,
  onResult,
  onProcessing,
  onError,
  onConnect,
  onDisconnect,
}: UseASRWebSocketOptions): UseASRWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [results, setResults] = useState<RecognitionResult[]>([]);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectDelay = 3000; // 3초

  /**
   * WebSocket 연결
   */
  const connect = useCallback(() => {
    if (!wsUrl || !enabled) {
      return;
    }

    // 이미 연결되어 있으면 무시
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    // 연결 중이면 무시
    if (isConnecting) {
      return;
    }

    setIsConnecting(true);
    setError(null);

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      // 연결 성공
      ws.onopen = () => {
        console.log('✅ ASR WebSocket 연결 성공:', wsUrl);
        setIsConnected(true);
        setIsConnecting(false);
        reconnectAttemptsRef.current = 0;
        onConnect?.();
      };

      // 메시지 수신
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // 인식 결과 처리
          if (data.type === 'recognition_result') {
            const result: RecognitionResult = {
              type: data.type,
              device_id: data.device_id,
              device_name: data.device_name,
              session_id: data.session_id,
              text: data.text,
              timestamp: data.timestamp,
              duration: data.duration || 0,
              is_emergency: data.is_emergency || false,
              emergency_keywords: data.emergency_keywords || [],
            };

            setResults((prev) => [...prev, result]);
            setIsProcessing(false);
            onProcessing?.(false);
            onResult?.(result);
          }
          // 처리 중 메시지
          else if (data.type === 'processing') {
            console.log('🔄 음성 처리 중...');
            setIsProcessing(true);
            onProcessing?.(true);
          }
          // 연결 확인 메시지
          else if (data.type === 'connected') {
            console.log('✅ ASR 서버 연결 확인:', data.message);
          }
          // 에러 메시지
          else if (data.type === 'error') {
            const errorMsg = data.message || '알 수 없는 오류가 발생했습니다';
            const error = new Error(errorMsg);
            setError(error);
            onError?.(error);
          }
        } catch (err) {
          console.error('❌ WebSocket 메시지 파싱 오류:', err);
          const error = err instanceof Error ? err : new Error('메시지 파싱 실패');
          setError(error);
          onError?.(error);
        }
      };

      // 연결 종료
      ws.onclose = (event) => {
        console.log('🔌 ASR WebSocket 연결 종료:', event.code, event.reason);
        setIsConnected(false);
        setIsConnecting(false);
        setIsProcessing(false);
        wsRef.current = null;
        onDisconnect?.();

        // 정상 종료가 아니면 재연결 시도
        if (event.code !== 1000 && enabled && wsUrl) {
          if (reconnectAttemptsRef.current < maxReconnectAttempts) {
            reconnectAttemptsRef.current += 1;
            console.log(
              `🔄 재연결 시도 ${reconnectAttemptsRef.current}/${maxReconnectAttempts}...`
            );
            
            reconnectTimeoutRef.current = setTimeout(() => {
              connect();
            }, reconnectDelay);
          } else {
            const error = new Error('WebSocket 재연결 실패: 최대 시도 횟수 초과');
            setError(error);
            onError?.(error);
          }
        }
      };

      // 에러 발생
      ws.onerror = (event) => {
        console.error('❌ ASR WebSocket 오류:', event);
        const error = new Error('WebSocket 연결 오류');
        setError(error);
        setIsConnecting(false);
        onError?.(error);
      };
    } catch (err) {
      console.error('❌ WebSocket 생성 실패:', err);
      const error = err instanceof Error ? err : new Error('WebSocket 생성 실패');
      setError(error);
      setIsConnecting(false);
      onError?.(error);
    }
    }, [wsUrl, enabled, onResult, onProcessing, onError, onConnect, onDisconnect, isConnecting]);  /**
   * WebSocket 연결 해제
   */
  const disconnect = useCallback(() => {
    // 재연결 타이머 취소
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // WebSocket 닫기
    if (wsRef.current) {
      wsRef.current.close(1000, '사용자 요청');
      wsRef.current = null;
    }

    setIsConnected(false);
    setIsConnecting(false);
    setIsProcessing(false);
    reconnectAttemptsRef.current = 0;
  }, []);

  /**
   * 인식 결과 초기화
   */
  const clearResults = useCallback(() => {
    setResults([]);
  }, []);

  // wsUrl이 변경되면 자동 연결
  useEffect(() => {
    if (wsUrl && enabled) {
      connect();
    } else {
      disconnect();
    }

    // 컴포넌트 언마운트 시 정리
    return () => {
      disconnect();
    };
  }, [wsUrl, enabled, connect, disconnect]);

  return {
    isConnected,
    isConnecting,
    isProcessing,
    error,
    results,
    connect,
    disconnect,
    clearResults,
  };
}
