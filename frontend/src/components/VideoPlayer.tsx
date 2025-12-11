'use client';

import { useState, useEffect, useRef } from 'react';
import { Play, Pause, Square, RefreshCw, AlertTriangle, Wifi, WifiOff } from 'lucide-react';
import toast from 'react-hot-toast';

interface VideoPlayerProps {
  streamUrl: string;
  deviceName?: string;
  isOnline?: boolean;
  className?: string;
}

export default function VideoPlayer({ 
  streamUrl, 
  deviceName,
  isOnline = true,
  className = '' 
}: VideoPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string>('');
  const imgRef = useRef<HTMLImageElement>(null);
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // 스트림 URL이 변경되면 재생 중지
  useEffect(() => {
    if (streamUrl) {
      setIsPlaying(false);
      setHasError(false);
      setErrorMessage('');
    }
  }, [streamUrl]);

  // 재생 중일 때 이미지 새로고침
  useEffect(() => {
    if (!isPlaying || !streamUrl || !isOnline) {
      return;
    }

    setIsLoading(true);
    setHasError(false);
    setErrorMessage('');

    // MJPEG 스트림의 경우 이미지 src를 업데이트하여 자동 새로고침
    // 타임스탬프를 추가하여 캐시 방지
    const updateImage = () => {
      if (imgRef.current && streamUrl) {
        const separator = streamUrl.includes('?') ? '&' : '?';
        imgRef.current.src = `${streamUrl}${separator}_t=${Date.now()}`;
      }
    };

    // 초기 로드
    updateImage();

    // 이미지 로드 성공
    const handleLoad = () => {
      setIsLoading(false);
      setHasError(false);
    };

    // 이미지 로드 실패
    const handleError = () => {
      setIsLoading(false);
      setHasError(true);
      setErrorMessage('스트림을 불러올 수 없습니다');
      
      // 3초 후 자동 재시도
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
      retryTimeoutRef.current = setTimeout(() => {
        if (isPlaying) {
          updateImage();
        }
      }, 3000);
    };

    const img = imgRef.current;
    if (img) {
      img.addEventListener('load', handleLoad);
      img.addEventListener('error', handleError);
    }

    return () => {
      if (img) {
        img.removeEventListener('load', handleLoad);
        img.removeEventListener('error', handleError);
      }
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
    };
  }, [isPlaying, streamUrl, isOnline]);

  const handlePlay = () => {
    if (!isOnline) {
      toast.error('장비가 오프라인 상태입니다');
      return;
    }
    if (!streamUrl) {
      toast.error('스트림 URL이 설정되지 않았습니다');
      return;
    }
    setIsPlaying(true);
    setHasError(false);
  };

  const handlePause = () => {
    setIsPlaying(false);
    if (imgRef.current) {
      imgRef.current.src = '';
    }
  };

  const handleStop = () => {
    setIsPlaying(false);
    setHasError(false);
    setErrorMessage('');
    if (imgRef.current) {
      imgRef.current.src = '';
    }
  };

  const handleRetry = () => {
    setHasError(false);
    setErrorMessage('');
    if (isPlaying) {
      if (imgRef.current && streamUrl) {
        const separator = streamUrl.includes('?') ? '&' : '?';
        imgRef.current.src = `${streamUrl}${separator}_t=${Date.now()}`;
      }
    }
  };

  // 스트림 URL 생성 (MJPEG HTTP 스트림)
  // ESP32-CAM의 경우 일반적으로 http://{ip}:81/stream 형식
  const getStreamUrl = () => {
    if (!streamUrl) return '';
    
    // 이미 전체 URL인 경우
    if (streamUrl.startsWith('http://') || streamUrl.startsWith('https://')) {
      return streamUrl;
    }
    
    // IP 주소만 있는 경우 기본 포트와 경로 추가
    return `http://${streamUrl}:81/stream`;
  };

  const finalStreamUrl = getStreamUrl();

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <div className={`h-3 w-3 rounded-full mr-2 ${
            isOnline ? 'bg-green-500' : 'bg-gray-400'
          }`} />
          <h3 className="text-lg font-semibold text-gray-900">
            {deviceName || '카메라 스트림'}
          </h3>
        </div>
        <div className="flex items-center space-x-2">
          {isOnline ? (
            <Wifi className="h-4 w-4 text-green-500" />
          ) : (
            <WifiOff className="h-4 w-4 text-gray-400" />
          )}
        </div>
      </div>

      {/* 비디오 영역 */}
      <div className="relative bg-black rounded-lg overflow-hidden aspect-video mb-4">
        {!isPlaying ? (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
            <div className="text-center">
              <div className="text-gray-400 mb-2">
                <Play className="h-12 w-12 mx-auto" />
              </div>
              <p className="text-sm text-gray-400">
                재생 버튼을 눌러 스트림을 시작하세요
              </p>
            </div>
          </div>
        ) : hasError ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-900">
            <AlertTriangle className="h-12 w-12 text-yellow-500 mb-2" />
            <p className="text-sm text-gray-300 mb-4">{errorMessage}</p>
            <button
              onClick={handleRetry}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm"
            >
              <RefreshCw className="h-4 w-4 inline mr-2" />
              재시도
            </button>
          </div>
        ) : (
          <>
            {isLoading && (
              <div className="absolute inset-0 flex items-center justify-center bg-gray-900 bg-opacity-75">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-2"></div>
                  <p className="text-sm text-gray-300">스트림 연결 중...</p>
                </div>
              </div>
            )}
            <img
              ref={imgRef}
              src=""
              alt="Camera Stream"
              className="w-full h-full object-contain"
              style={{ display: isLoading ? 'none' : 'block' }}
            />
          </>
        )}
      </div>

      {/* 제어 버튼 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <button
            onClick={handlePlay}
            disabled={!isOnline || !finalStreamUrl || isPlaying}
            className={`inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              !isOnline || !finalStreamUrl || isPlaying
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-primary-600 text-white hover:bg-primary-700'
            }`}
          >
            <Play className="h-4 w-4 mr-2" />
            재생
          </button>
          <button
            onClick={handlePause}
            disabled={!isPlaying}
            className={`inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              !isPlaying
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
            }`}
          >
            <Pause className="h-4 w-4 mr-2" />
            일시정지
          </button>
          <button
            onClick={handleStop}
            disabled={!isPlaying}
            className={`inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              !isPlaying
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-red-600 text-white hover:bg-red-700'
            }`}
          >
            <Square className="h-4 w-4 mr-2" />
            정지
          </button>
        </div>

        {/* 스트림 정보 */}
        <div className="text-xs text-gray-500">
          {finalStreamUrl && (
            <span className="truncate max-w-xs" title={finalStreamUrl}>
              {finalStreamUrl.replace(/^https?:\/\//, '')}
            </span>
          )}
        </div>
      </div>

      {/* 안내 메시지 */}
      {!finalStreamUrl && (
        <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-800">
            ⚠️ 스트림 URL이 설정되지 않았습니다. 장비의 IP 주소를 설정해주세요.
          </p>
        </div>
      )}
      {!isOnline && (
        <div className="mt-3 p-3 bg-gray-50 border border-gray-200 rounded-lg">
          <p className="text-sm text-gray-600">
            장비가 오프라인 상태입니다. 스트림을 재생할 수 없습니다.
          </p>
        </div>
      )}
    </div>
  );
}

