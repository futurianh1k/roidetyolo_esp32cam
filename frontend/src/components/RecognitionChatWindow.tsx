/**
 * RecognitionChatWindow 컴포넌트
 * 
 * 음성인식 결과를 채팅 형식으로 표시하는 창
 * 
 * 주요 기능:
 * - 인식 결과 히스토리 표시
 * - 타임스탬프 표시
 * - 응급 상황 강조 표시
 * - 자동 스크롤
 * - 결과 초기화
 */

'use client';

import { useEffect, useRef } from 'react';
import { RecognitionResult } from '@/lib/api';
import { Trash2, AlertTriangle, Clock } from 'lucide-react';

interface RecognitionChatWindowProps {
  results: RecognitionResult[];
  onClear?: () => void;
}

export default function RecognitionChatWindow({
  results,
  onClear,
}: RecognitionChatWindowProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // 새 결과가 추가되면 자동 스크롤
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [results]);

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString('ko-KR', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return timestamp;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">인식 결과</h3>
        {results.length > 0 && (
          <button
            onClick={onClear}
            className="inline-flex items-center px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            title="결과 초기화"
          >
            <Trash2 className="h-4 w-4 mr-1" />
            초기화
          </button>
        )}
      </div>

      {/* 채팅 메시지 영역 */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto space-y-3 min-h-0"
        style={{ maxHeight: '500px' }}
      >
        {results.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-400">
            <div className="text-center">
              <p className="text-sm">인식 결과가 없습니다</p>
              <p className="text-xs mt-1">음성인식을 시작하면 결과가 여기에 표시됩니다</p>
            </div>
          </div>
        ) : (
          results.map((result, index) => (
            <div
              key={index}
              className={`p-3 rounded-lg border ${
                result.is_emergency
                  ? 'bg-red-50 border-red-200'
                  : 'bg-gray-50 border-gray-200'
              }`}
            >
              {/* 헤더 */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  {result.is_emergency && (
                    <AlertTriangle className="h-4 w-4 text-red-600" />
                  )}
                  <span className="text-xs font-medium text-gray-600">
                    {result.device_name}
                  </span>
                </div>
                <div className="flex items-center text-xs text-gray-500">
                  <Clock className="h-3 w-3 mr-1" />
                  {formatTimestamp(result.timestamp)}
                </div>
              </div>

              {/* 인식 텍스트 */}
              <div
                className={`text-sm ${
                  result.is_emergency ? 'text-red-900 font-medium' : 'text-gray-900'
                }`}
              >
                {result.text}
              </div>

              {/* 메타 정보 */}
              <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
                <div>
                  {result.duration > 0 && (
                    <span>길이: {result.duration.toFixed(1)}초</span>
                  )}
                </div>
                {result.emergency_keywords.length > 0 && (
                  <div className="text-red-600">
                    키워드: {result.emergency_keywords.join(', ')}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* 통계 정보 */}
      {results.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>총 {results.length}개 결과</span>
            {results.filter((r) => r.is_emergency).length > 0 && (
              <span className="text-red-600 font-medium">
                응급 상황 {results.filter((r) => r.is_emergency).length}건
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
