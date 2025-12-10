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
import { Trash2, AlertTriangle, Clock, Smartphone } from 'lucide-react';

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
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          <span className="text-2xl mr-2">💬</span>
          인식 결과
        </h3>
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
              <Smartphone className="h-12 w-12 mx-auto mb-2 text-gray-300" />
              <p className="text-sm font-medium">인식 결과가 없습니다</p>
              <p className="text-xs mt-1 text-gray-500">
                음성인식을 시작하면 결과가 여기에 표시됩니다
              </p>
            </div>
          </div>
        ) : (
          results.map((result, index) => {
            // 타임스탬프에서 분을 추출
            const getMinute = (timestamp: string): string => {
              try {
                const date = new Date(timestamp);
                return date.toLocaleTimeString('ko-KR', {
                  hour: '2-digit',
                  minute: '2-digit',
                });
              } catch {
                return '';
              }
            };

            const showTimestamp = index === 0 || getMinute(results[index - 1].timestamp) !== getMinute(result.timestamp);

            return (
              <div key={index} className="flex flex-col">
                {/* 타임스탬프 표시 */}
                {showTimestamp && (
                  <div className="text-center mb-3">
                    <span className="inline-block px-3 py-1 text-xs text-gray-500 bg-gray-100 rounded-full">
                      {formatTimestamp(result.timestamp).split(' ')[0]}
                    </span>
                  </div>
                )}

                {/* 채팅 버블 */}
                <div className="flex justify-start">
                  <div
                    className={`max-w-xs px-4 py-2 rounded-lg ${
                      result.is_emergency
                        ? 'bg-red-100 text-red-900 border border-red-300'
                        : 'bg-blue-100 text-blue-900 border border-blue-300'
                    }`}
                  >
                    <div className="flex items-start space-x-2">
                      {result.is_emergency && (
                        <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                      )}
                      <div className="flex-1">
                        <p className="text-sm font-medium break-words">
                          {result.text}
                        </p>
                        {result.emergency_keywords.length > 0 && (
                          <p className="text-xs mt-1 font-semibold">
                            🚨 {result.emergency_keywords.join(', ')}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* 메타 정보 */}
                <div className="flex justify-start mt-1 px-2 text-xs text-gray-500">
                  <Clock className="h-3 w-3 mr-1" />
                  {formatTimestamp(result.timestamp)}
                  {result.duration > 0 && (
                    <span className="ml-2">• {result.duration.toFixed(1)}초</span>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* 통계 정보 */}
      {results.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <div className="text-gray-600">인식 횟수</div>
              <div className="text-lg font-semibold text-gray-900">
                {results.length}건
              </div>
            </div>
            {results.filter((r) => r.is_emergency).length > 0 && (
              <div>
                <div className="text-red-600">응급 상황</div>
                <div className="text-lg font-semibold text-red-600">
                  {results.filter((r) => r.is_emergency).length}건
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
