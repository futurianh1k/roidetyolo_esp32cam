/**
 * VoiceRecognitionPanel 컴포넌트
 * 
 * 음성인식 세션을 시작/종료하는 패널
 * 
 * 주요 기능:
 * - 음성인식 세션 시작/종료 버튼
 * - 세션 상태 표시
 * - WebSocket 연결 상태 표시
 * - 언어 선택 (선택적)
 */

'use client';

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { asrAPI, ASRSessionStartRequest, Device } from '@/lib/api';
import { useASRWebSocket } from '@/hooks/useASRWebSocket';
import toast from 'react-hot-toast';
import { Mic, MicOff, Loader2, Wifi, WifiOff, AlertCircle } from 'lucide-react';

interface VoiceRecognitionPanelProps {
  device: Device;
  onResult?: (result: any) => void;
}

export default function VoiceRecognitionPanel({
  device,
  onResult,
}: VoiceRecognitionPanelProps) {
  const queryClient = useQueryClient();
  const [language, setLanguage] = useState<string>('ko');
  const [vadEnabled, setVadEnabled] = useState<boolean>(true);
  const [wsUrl, setWsUrl] = useState<string | null>(null);

  // 세션 상태 조회
  const {
    data: sessionStatus,
    isLoading: statusLoading,
    refetch: refetchStatus,
  } = useQuery({
    queryKey: ['asrSessionStatus', device.id],
    queryFn: async () => {
      const { data } = await asrAPI.getSessionStatus(device.id);
      return data;
    },
    enabled: device.is_online,
    refetchInterval: (data) => {
      // 활성 세션이 있으면 5초마다, 없으면 30초마다
      return data?.has_active_session ? 5000 : 30000;
    },
  });

  // 세션 시작
  const startMutation = useMutation({
    mutationFn: async (request: ASRSessionStartRequest) => {
      const { data } = await asrAPI.startSession(device.id, request);
      return data;
    },
    onSuccess: (data) => {
      toast.success('음성인식이 시작되었습니다');
      setWsUrl(data.ws_url); // WebSocket URL 저장
      queryClient.invalidateQueries({ queryKey: ['asrSessionStatus', device.id] });
    },
    onError: (error: any) => {
      const message =
        error.response?.data?.detail || '음성인식 시작에 실패했습니다';
      toast.error(message);
      setWsUrl(null);
    },
  });

  // 세션 종료
  const stopMutation = useMutation({
    mutationFn: async (sessionId: string) => {
      const { data } = await asrAPI.stopSession(device.id, { session_id: sessionId });
      return data;
    },
    onSuccess: () => {
      toast.success('음성인식이 종료되었습니다');
      setWsUrl(null); // WebSocket URL 제거
      queryClient.invalidateQueries({ queryKey: ['asrSessionStatus', device.id] });
    },
    onError: (error: any) => {
      const message =
        error.response?.data?.detail || '음성인식 종료에 실패했습니다';
      toast.error(message);
    },
  });

  // WebSocket 연결 (세션이 활성화되어 있을 때만)
  const { isConnected, isConnecting, error: wsError } = useASRWebSocket({
    wsUrl: wsUrl,
    enabled: (sessionStatus?.has_active_session || false) && !!wsUrl,
    onResult: (result) => {
      onResult?.(result);
    },
    onError: (error) => {
      toast.error(`WebSocket 오류: ${error.message}`);
    },
  });

  const handleStart = () => {
    if (!device.is_online) {
      toast.error('장비가 오프라인 상태입니다');
      return;
    }

    startMutation.mutate({
      language,
      vad_enabled: vadEnabled,
    });
  };

  const handleStop = () => {
    if (!sessionStatus?.session?.session_id) {
      toast.error('활성 세션이 없습니다');
      return;
    }

    stopMutation.mutate(sessionStatus.session.session_id);
  };

  const isLoading = startMutation.isPending || stopMutation.isPending;
  const hasActiveSession = sessionStatus?.has_active_session || false;
  const session = sessionStatus?.session;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          <Mic className="h-5 w-5 mr-2 text-primary-600" />
          음성인식
        </h3>
        {hasActiveSession && (
          <div className="flex items-center space-x-2">
            {isConnected ? (
              <div className="flex items-center text-green-600">
                <Wifi className="h-4 w-4 mr-1" />
                <span className="text-sm">연결됨</span>
              </div>
            ) : isConnecting ? (
              <div className="flex items-center text-yellow-600">
                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                <span className="text-sm">연결 중...</span>
              </div>
            ) : (
              <div className="flex items-center text-red-600">
                <WifiOff className="h-4 w-4 mr-1" />
                <span className="text-sm">연결 끊김</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 장비 오프라인 경고 */}
      {!device.is_online && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg flex items-center">
          <AlertCircle className="h-5 w-5 text-yellow-600 mr-2" />
          <span className="text-sm text-yellow-800">
            장비가 오프라인 상태입니다. 음성인식을 시작할 수 없습니다.
          </span>
        </div>
      )}

      {/* 세션 상태 정보 */}
      {hasActiveSession && session && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="text-sm text-blue-900">
            <div className="font-medium mb-1">활성 세션</div>
            <div className="text-xs text-blue-700 space-y-1">
              <div>세션 ID: {session.session_id.substring(0, 8)}...</div>
              <div>인식된 세그먼트: {session.segments_count}개</div>
              {session.last_result && (
                <div>마지막 결과: "{session.last_result}"</div>
              )}
              {session.is_processing && (
                <div className="text-blue-600">🔄 음성 처리 중...</div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 설정 (세션이 없을 때만 표시) */}
      {!hasActiveSession && (
        <div className="mb-4 space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              언어
            </label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              disabled={isLoading}
            >
              <option value="auto">자동 감지</option>
              <option value="ko">한국어</option>
              <option value="en">영어</option>
              <option value="zh">중국어</option>
              <option value="ja">일본어</option>
            </select>
          </div>
          <div className="flex items-center">
            <input
              type="checkbox"
              id="vad-enabled"
              checked={vadEnabled}
              onChange={(e) => setVadEnabled(e.target.checked)}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              disabled={isLoading}
            />
            <label
              htmlFor="vad-enabled"
              className="ml-2 text-sm text-gray-700"
            >
              VAD (음성 활동 감지) 활성화
            </label>
          </div>
        </div>
      )}

      {/* 버튼 */}
      <div className="flex space-x-3">
        {!hasActiveSession ? (
          <button
            onClick={handleStart}
            disabled={!device.is_online || isLoading}
            className="flex-1 inline-flex items-center justify-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                시작 중...
              </>
            ) : (
              <>
                <Mic className="h-5 w-5 mr-2" />
                음성인식 시작
              </>
            )}
          </button>
        ) : (
          <button
            onClick={handleStop}
            disabled={isLoading}
            className="flex-1 inline-flex items-center justify-center px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                종료 중...
              </>
            ) : (
              <>
                <MicOff className="h-5 w-5 mr-2" />
                음성인식 종료
              </>
            )}
          </button>
        )}
      </div>

      {/* WebSocket 에러 표시 */}
      {wsError && (
        <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded-lg text-sm text-red-800">
          <AlertCircle className="h-4 w-4 inline mr-1" />
          {wsError.message}
        </div>
      )}
    </div>
  );
}
