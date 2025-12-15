'use client';

import { useState, useEffect, useRef } from 'react';
import { Play, Pause, Square, RefreshCw, AlertTriangle, Wifi, WifiOff, Shield, Copy, ExternalLink, Video } from 'lucide-react';
import toast from 'react-hot-toast';

type StreamType = 'http' | 'rtsp' | 'websocket';

interface VideoPlayerProps {
  streamUrl?: string;
  rtspUrl?: string;
  deviceId?: number;
  deviceName?: string;
  isOnline?: boolean;
  className?: string;
  useProxy?: boolean;
  backendUrl?: string;
}

// 백엔드 API URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function VideoPlayer({ 
  streamUrl,
  rtspUrl,
  deviceId,
  deviceName,
  isOnline = true,
  className = '',
  useProxy = true,
  backendUrl = API_BASE_URL,
}: VideoPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [proxyMode, setProxyMode] = useState(useProxy);
  const [streamType, setStreamType] = useState<StreamType>('http');
  const imgRef = useRef<HTMLImageElement>(null);
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // 스트림 URL이 변경되면 재생 중지
  useEffect(() => {
    if (streamUrl || deviceId) {
      setIsPlaying(false);
      setHasError(false);
      setErrorMessage('');
    }
  }, [streamUrl, deviceId]);

  // 직접 스트림 URL 생성 (MJPEG HTTP 스트림)
  const getDirectStreamUrl = () => {
    if (!streamUrl) return '';
    
    if (streamUrl.startsWith('http://') || streamUrl.startsWith('https://')) {
      return streamUrl;
    }
    
    if (streamUrl.includes(':') && streamUrl.includes('/')) {
      return `http://${streamUrl}`;
    }
    
    if (streamUrl.includes(':')) {
      return `http://${streamUrl}/stream`;
    }
    
    return `http://${streamUrl}:81/stream`;
  };

  // RTSP URL 가져오기
  const getRtspUrl = () => {
    if (rtspUrl) return rtspUrl;
    if (streamUrl && !streamUrl.startsWith('http')) {
      // IP 주소만 있는 경우 기본 RTSP URL 생성
      const ip = streamUrl.split(':')[0];
      return `rtsp://${ip}:554/stream`;
    }
    return '';
  };

  // 프록시 스트림 URL 생성
  const getProxyStreamUrl = () => {
    if (deviceId) {
      return `${backendUrl}/stream/device/${deviceId}?type=http`;
    }
    
    const directUrl = getDirectStreamUrl();
    if (directUrl) {
      return `${backendUrl}/stream/proxy?url=${encodeURIComponent(directUrl)}`;
    }
    
    return '';
  };

  // 최종 스트림 URL 결정
  const finalStreamUrl = proxyMode ? getProxyStreamUrl() : getDirectStreamUrl();
  const finalRtspUrl = getRtspUrl();

  // 재생 중일 때 이미지 로드
  useEffect(() => {
    if (streamType !== 'http' || !isPlaying || !finalStreamUrl || !isOnline) {
      return;
    }

    setIsLoading(true);
    setHasError(false);
    setErrorMessage('');

    const updateImage = () => {
      if (imgRef.current && finalStreamUrl) {
        const separator = finalStreamUrl.includes('?') ? '&' : '?';
        imgRef.current.src = `${finalStreamUrl}${separator}_t=${Date.now()}`;
        console.log('Loading stream:', imgRef.current.src);
      }
    };

    updateImage();

    const handleLoad = () => {
      setIsLoading(false);
      setHasError(false);
      console.log('Stream loaded successfully');
    };

    const handleError = () => {
      setIsLoading(false);
      setHasError(true);
      
      if (proxyMode) {
        setErrorMessage(
          '스트림을 불러올 수 없습니다. ' +
          '(백엔드 프록시 연결 실패 또는 장비 오프라인)'
        );
      } else {
        setErrorMessage(
          '스트림을 불러올 수 없습니다. ' +
          '(네트워크 오류 또는 CORS 정책으로 차단됨)'
        );
      }
      console.error('Stream load failed:', finalStreamUrl);
      
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
      retryTimeoutRef.current = setTimeout(() => {
        if (isPlaying) {
          updateImage();
        }
      }, 5000);
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
  }, [isPlaying, finalStreamUrl, isOnline, proxyMode, streamType]);

  const handlePlay = () => {
    if (!isOnline) {
      toast.error('장비가 오프라인 상태입니다');
      return;
    }
    if (!streamUrl && !deviceId) {
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
      if (imgRef.current && finalStreamUrl) {
        const separator = finalStreamUrl.includes('?') ? '&' : '?';
        imgRef.current.src = `${finalStreamUrl}${separator}_t=${Date.now()}`;
      }
    }
  };

  const toggleProxyMode = () => {
    setProxyMode(!proxyMode);
    if (isPlaying) {
      setIsPlaying(false);
      setTimeout(() => setIsPlaying(true), 100);
    }
    toast.success(proxyMode ? '직접 연결 모드로 전환' : '프록시 모드로 전환');
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('URL이 클립보드에 복사되었습니다');
  };

  const openInExternalPlayer = (url: string) => {
    // VLC URL scheme
    const vlcUrl = `vlc://${url}`;
    window.open(vlcUrl, '_blank');
    toast.success('외부 플레이어로 열기를 시도합니다');
  };

  const hasStreamSource = streamUrl || deviceId;

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
          {/* 스트림 타입 선택 */}
          <div className="flex rounded-lg border border-gray-200 overflow-hidden">
            <button
              onClick={() => { setStreamType('http'); setIsPlaying(false); }}
              className={`px-2 py-1 text-xs font-medium transition-colors ${
                streamType === 'http'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-50'
              }`}
              title="HTTP MJPEG 스트림 (브라우저 호환)"
            >
              HTTP
            </button>
            <button
              onClick={() => { setStreamType('rtsp'); setIsPlaying(false); }}
              className={`px-2 py-1 text-xs font-medium transition-colors ${
                streamType === 'rtsp'
                  ? 'bg-purple-600 text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-50'
              }`}
              title="RTSP 스트림 (외부 플레이어 필요)"
            >
              RTSP
            </button>
          </div>
          
          {/* 프록시 모드 토글 (HTTP only) */}
          {streamType === 'http' && (
            <button
              onClick={toggleProxyMode}
              className={`p-1.5 rounded-lg transition-colors ${
                proxyMode 
                  ? 'bg-blue-100 text-blue-600 hover:bg-blue-200' 
                  : 'bg-gray-100 text-gray-400 hover:bg-gray-200'
              }`}
              title={proxyMode ? '프록시 모드 (CORS 우회)' : '직접 연결 모드'}
            >
              <Shield className="h-4 w-4" />
            </button>
          )}
          
          {isOnline ? (
            <Wifi className="h-4 w-4 text-green-500" />
          ) : (
            <WifiOff className="h-4 w-4 text-gray-400" />
          )}
        </div>
      </div>

      {/* 비디오 영역 */}
      <div className="relative bg-black rounded-lg overflow-hidden aspect-video mb-4">
        {streamType === 'rtsp' ? (
          // RTSP 모드: URL 표시 및 복사
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-900 p-4">
            <Video className="h-12 w-12 text-purple-400 mb-4" />
            <p className="text-sm text-gray-300 mb-2 text-center">
              RTSP 스트림은 브라우저에서 직접 재생할 수 없습니다.
            </p>
            <p className="text-xs text-gray-400 mb-4 text-center">
              VLC, ffplay, MPV 등 외부 플레이어를 사용하세요.
            </p>
            
            {finalRtspUrl ? (
              <div className="w-full max-w-md">
                <div className="bg-gray-800 rounded-lg p-3 mb-3">
                  <code className="text-xs text-green-400 break-all">{finalRtspUrl}</code>
                </div>
                <div className="flex space-x-2 justify-center">
                  <button
                    onClick={() => copyToClipboard(finalRtspUrl)}
                    className="px-3 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm flex items-center"
                  >
                    <Copy className="h-4 w-4 mr-2" />
                    URL 복사
                  </button>
                  <button
                    onClick={() => openInExternalPlayer(finalRtspUrl)}
                    className="px-3 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 text-sm flex items-center"
                  >
                    <ExternalLink className="h-4 w-4 mr-2" />
                    VLC로 열기
                  </button>
                </div>
                
                {/* 명령어 예시 */}
                <div className="mt-4 text-left">
                  <p className="text-xs text-gray-400 mb-2">터미널 명령어:</p>
                  <div className="space-y-1">
                    <div className="flex items-center">
                      <code className="text-xs text-gray-500 bg-gray-800 px-2 py-1 rounded flex-1">
                        vlc {finalRtspUrl}
                      </code>
                      <button
                        onClick={() => copyToClipboard(`vlc ${finalRtspUrl}`)}
                        className="ml-2 p-1 text-gray-400 hover:text-white"
                      >
                        <Copy className="h-3 w-3" />
                      </button>
                    </div>
                    <div className="flex items-center">
                      <code className="text-xs text-gray-500 bg-gray-800 px-2 py-1 rounded flex-1">
                        ffplay {finalRtspUrl}
                      </code>
                      <button
                        onClick={() => copyToClipboard(`ffplay ${finalRtspUrl}`)}
                        className="ml-2 p-1 text-gray-400 hover:text-white"
                      >
                        <Copy className="h-3 w-3" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-sm text-yellow-400">RTSP URL이 설정되지 않았습니다.</p>
            )}
          </div>
        ) : !isPlaying ? (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
            <div className="text-center">
              <div className="text-gray-400 mb-2">
                <Play className="h-12 w-12 mx-auto" />
              </div>
              <p className="text-sm text-gray-400">
                재생 버튼을 눌러 스트림을 시작하세요
              </p>
              {proxyMode && (
                <p className="text-xs text-blue-400 mt-1">
                  🔒 프록시 모드 (CORS 우회)
                </p>
              )}
            </div>
          </div>
        ) : hasError ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-900">
            <AlertTriangle className="h-12 w-12 text-yellow-500 mb-2" />
            <p className="text-sm text-gray-300 mb-4 text-center px-4">{errorMessage}</p>
            <div className="flex space-x-2">
              <button
                onClick={handleRetry}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
              >
                <RefreshCw className="h-4 w-4 inline mr-2" />
                재시도
              </button>
              <button
                onClick={toggleProxyMode}
                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 text-sm"
              >
                {proxyMode ? '직접 연결' : '프록시 사용'}
              </button>
            </div>
          </div>
        ) : (
          <>
            {isLoading && (
              <div className="absolute inset-0 flex items-center justify-center bg-gray-900 bg-opacity-75">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-2"></div>
                  <p className="text-sm text-gray-300">스트림 연결 중...</p>
                  {proxyMode && (
                    <p className="text-xs text-blue-400 mt-1">
                      프록시 서버를 통해 연결 중
                    </p>
                  )}
                </div>
              </div>
            )}
            <img
              ref={imgRef}
              src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
              alt="Camera Stream"
              className="w-full h-full object-contain"
              style={{ display: isLoading ? 'none' : 'block' }}
            />
          </>
        )}
      </div>

      {/* 제어 버튼 (HTTP 모드만) */}
      {streamType === 'http' && (
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <button
              onClick={handlePlay}
              disabled={!isOnline || !hasStreamSource || isPlaying}
              className={`inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                !isOnline || !hasStreamSource || isPlaying
                  ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
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
          <div className="text-xs text-gray-500 text-right">
            {proxyMode && deviceId && (
              <span className="block text-blue-500">
                프록시: /stream/device/{deviceId}
              </span>
            )}
            {!proxyMode && finalStreamUrl && (
              <span className="truncate max-w-xs block" title={finalStreamUrl}>
                {finalStreamUrl.replace(/^https?:\/\//, '')}
              </span>
            )}
          </div>
        </div>
      )}

      {/* 안내 메시지 */}
      {!hasStreamSource && (
        <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-800">
            ⚠️ 스트림 URL이 설정되지 않았습니다. 장비의 IP 주소 또는 RTSP URL을 설정해주세요.
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
