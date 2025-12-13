'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { devicesAPI, controlAPI } from '@/lib/api';
import { useAuthStore } from '@/store/authStore';
import toast from 'react-hot-toast';
import {
  ArrowLeft,
  Camera,
  Mic,
  Volume2,
  Monitor as MonitorIcon,
  Battery,
  Cpu,
  HardDrive,
  Thermometer,
  Wifi,
  RefreshCw,
  RotateCw,
  Trash2,
  AlertTriangle,
  Edit2,
  Check,
  X,
  Power,
  Moon,
  Sun,
} from 'lucide-react';
import DeviceControl from '@/components/DeviceControl';
import DeviceStatus from '@/components/DeviceStatus';
import VideoPlayer from '@/components/VideoPlayer';
import VoiceRecognitionPanel from '@/components/VoiceRecognitionPanel';
import RecognitionChatWindow from '@/components/RecognitionChatWindow';
import { RecognitionResult } from '@/lib/api';

export default function DeviceDetailPage() {
  const router = useRouter();
  const params = useParams();
  const deviceId = Number(params.id);
  const { isAuthenticated } = useAuthStore();
  const [mounted, setMounted] = useState(false);
  const [isRestarting, setIsRestarting] = useState(false);
  const [isWaking, setIsWaking] = useState(false);
  const [isSleeping, setIsSleeping] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [recognitionResults, setRecognitionResults] = useState<RecognitionResult[]>([]);
  const [isProcessingAudio, setIsProcessingAudio] = useState(false);
  const [isEditingIP, setIsEditingIP] = useState(false);
  const [ipAddress, setIpAddress] = useState('');
  const [isUpdatingIP, setIsUpdatingIP] = useState(false);

  useEffect(() => {
    setMounted(true);
    // TODO: 로그인 기능 수정 후 인증 체크 활성화
    // if (!isAuthenticated && mounted) {
    //   router.push('/login');
    // }
  }, [isAuthenticated, mounted, router]);

  // 장비 정보 조회 (WebSocket useEffect 전에 선언해야 함)
  const { data: device, isLoading: deviceLoading, refetch: refetchDevice } = useQuery({
    queryKey: ['device', deviceId],
    queryFn: async () => {
      const { data } = await devicesAPI.getById(deviceId);
      return data;
    },
    // TODO: 로그인 수정 후 isAuthenticated 체크 활성화
    enabled: mounted && !isNaN(deviceId),
  });

  // 백엔드 WebSocket으로 음성인식 결과 수신 (ESP32에서 전송한 결과)
  useEffect(() => {
    if (!mounted || !device) return;

    // 백엔드 WebSocket 연결 (장비 구독)
    const token = localStorage.getItem('access_token');
    if (!token) {
      // 토큰이 없어도 연결 시도 (임시)
      console.warn('WebSocket 연결을 위한 토큰이 없습니다 (임시로 연결 시도)');
    }

    // API URL에서 WebSocket URL 생성
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || (typeof window !== 'undefined' ? window.location.origin.replace('3000', '8000') : 'http://localhost:8000');
    const wsUrl = apiUrl.replace(/^http:/, 'ws:').replace(/^https:/, 'wss:') + '/ws' + (token ? `?token=${token}` : '');
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      console.log('✅ 백엔드 WebSocket 연결 성공');
      // 장비 구독
      ws.send(JSON.stringify({
        type: 'subscribe_device',
        device_id: device.id
      }));
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        // 음성인식 결과 수신 (ESP32에서 전송)
        if (data.type === 'asr_result' && data.device_id === device.id) {
          const result: RecognitionResult = {
            type: 'recognition_result',
            device_id: data.device_id,
            device_name: data.device_name,
            session_id: data.session_id,
            text: data.text,
            timestamp: data.timestamp,
            duration: data.duration || 0,
            is_emergency: data.is_emergency || false,
            emergency_keywords: data.emergency_keywords || [],
          };

          setRecognitionResults((prev) => [...prev, result]);
          
          // 장비 디스플레이에 표시 (이미 ESP32에서 표시하지만, 프론트엔드에서도 명시적으로 요청)
          const displayText = result.is_emergency
            ? `🚨 응급: ${result.text}`
            : result.text;
          
          controlAPI.display(device.id, 'show_text', displayText).catch((error) => {
            console.error('디스플레이 업데이트 실패:', error);
          });
        }
      } catch (error) {
        console.error('WebSocket 메시지 파싱 오류:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('❌ 백엔드 WebSocket 오류:', error);
    };

    ws.onclose = () => {
      console.log('🔌 백엔드 WebSocket 연결 종료');
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
    };
  }, [mounted, device]);

  // IP 주소 편집 상태 초기화
  useEffect(() => {
    if (device?.ip_address) {
      setIpAddress(device.ip_address);
    } else {
      setIpAddress('');
    }
  }, [device?.ip_address]);

  // 장비 최신 상태 조회
  const { data: status, isLoading: statusLoading, refetch: refetchStatus } = useQuery({
    queryKey: ['deviceStatus', deviceId],
    queryFn: async () => {
      try {
      const { data } = await devicesAPI.getLatestStatus(deviceId);
      return data;
      } catch (error: any) {
        // 상태 정보가 없을 경우 에러 무시 (장비가 아직 연결 안됨)
        if (error.response?.status === 404) {
          console.log('장비 상태 정보 없음 (장비 미연결)');
          return null;
        }
        throw error;
      }
    },
    enabled: mounted && !isNaN(deviceId),
    refetchInterval: 5000, // 5초마다 자동 갱신
  });

  const handleRefresh = () => {
    refetchDevice();
    refetchStatus();
    toast.success('새로고침되었습니다');
  };

  const handleRestart = async () => {
    if (!device?.is_online) {
      toast.error('장비가 오프라인 상태입니다');
      return;
    }

    const confirmed = window.confirm('장비를 재시작하시겠습니까?\n재시작하는 동안 제어가 불가능합니다.');
    if (!confirmed) return;

    setIsRestarting(true);
    try {
      await controlAPI.system(deviceId, 'restart');
      toast.success('재시작 명령을 전송했습니다. 약 30초 후 다시 연결됩니다.');
      
      // 30초 후 자동 새로고침
      setTimeout(() => {
        refetchDevice();
        refetchStatus();
        setIsRestarting(false);
      }, 30000);
    } catch (error) {
      toast.error('재시작 명령 전송에 실패했습니다');
      setIsRestarting(false);
    }
  };

  const handleWake = async () => {
    setIsWaking(true);
    try {
      await controlAPI.system(deviceId, 'wake');
      toast.success('깨우기 명령을 전송했습니다. 장비가 연결되면 자동으로 온라인 상태가 됩니다.');
      
      // 10초 후 상태 새로고침 (장비가 깨어날 시간 필요)
      setTimeout(() => {
        refetchDevice();
        refetchStatus();
        setIsWaking(false);
      }, 10000);
    } catch (error: any) {
      toast.error('깨우기 명령 전송에 실패했습니다');
      setIsWaking(false);
    }
  };

  // 알람음 재생 핸들러
  const [isPlayingAlarm, setIsPlayingAlarm] = useState(false);
  
  const handlePlayAlarm = async (alarmType: 'beep' | 'alert' | 'notification' | 'emergency') => {
    if (!device?.is_online) {
      toast.error('장비가 오프라인 상태입니다');
      return;
    }
    
    setIsPlayingAlarm(true);
    try {
      await controlAPI.playAlarm(deviceId, alarmType, 1);
      toast.success(`${alarmType} 알람 재생 명령을 전송했습니다`);
    } catch (error: any) {
      toast.error('알람 재생에 실패했습니다');
    } finally {
      setTimeout(() => setIsPlayingAlarm(false), 1000);
    }
  };

  // 상태 보고 주기 변경 핸들러
  const [isChangingInterval, setIsChangingInterval] = useState(false);
  
  const handleChangeInterval = async (intervalSeconds: number) => {
    if (!device?.is_online) {
      toast.error('장비가 오프라인 상태입니다');
      return;
    }
    
    setIsChangingInterval(true);
    try {
      await controlAPI.setReportInterval(deviceId, intervalSeconds);
      toast.success(`상태 보고 주기를 ${intervalSeconds}초로 변경했습니다`);
      refetchDevice();
    } catch (error: any) {
      toast.error('보고 주기 변경에 실패했습니다');
    } finally {
      setIsChangingInterval(false);
    }
  };

  const handleSleep = async () => {
    if (!device?.is_online) {
      toast.error('장비가 이미 오프라인 상태입니다');
      return;
    }

    const confirmed = window.confirm('장비를 절전 모드로 전환하시겠습니까?\n절전 모드에서는 버튼을 눌러 깨울 수 있습니다.');
    if (!confirmed) return;

    setIsSleeping(true);
    try {
      await controlAPI.system(deviceId, 'sleep');
      toast.success('절전 모드 명령을 전송했습니다');
      
      // 3초 후 상태 새로고침
      setTimeout(() => {
        refetchDevice();
        refetchStatus();
        setIsSleeping(false);
      }, 3000);
    } catch (error) {
      toast.error('절전 모드 명령 전송에 실패했습니다');
      setIsSleeping(false);
    }
  };

  const handleDelete = async () => {
    const confirmed = window.confirm(
      `장비 "${device?.device_name}"를 정말 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.`
    );
    if (!confirmed) return;

    try {
      await devicesAPI.delete(deviceId);
      toast.success('장비가 삭제되었습니다');
      router.push('/dashboard');
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '장비 삭제에 실패했습니다';
      toast.error(errorMessage);
    }
  };

  const handleIPEditStart = () => {
    setIpAddress(device?.ip_address || '');
    setIsEditingIP(true);
  };

  const handleIPEditCancel = () => {
    setIpAddress(device?.ip_address || '');
    setIsEditingIP(false);
  };

  const handleIPUpdate = async () => {
    if (!device) return;

    // IP 주소 형식 검증 (더 엄격한 검증)
    const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/;
    if (ipAddress && ipAddress.trim() !== '') {
      if (!ipRegex.test(ipAddress.trim())) {
        toast.error('유효하지 않은 IP 주소 형식입니다 (예: 192.168.1.100)');
        return;
      }
      
      // 각 옥텟이 0-255 범위인지 확인
      const parts = ipAddress.trim().split('.');
      const isValid = parts.every(part => {
        const num = parseInt(part, 10);
        return num >= 0 && num <= 255;
      });
      
      if (!isValid) {
        toast.error('IP 주소의 각 숫자는 0-255 범위여야 합니다');
        return;
      }
    }

    setIsUpdatingIP(true);
    try {
      await devicesAPI.update(deviceId, { 
        ip_address: ipAddress.trim() || null 
      });
      toast.success('IP 주소가 업데이트되었습니다');
      setIsEditingIP(false);
      refetchDevice(); // 장비 정보 새로고침
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'IP 주소 업데이트에 실패했습니다';
      toast.error(errorMessage);
    } finally {
      setIsUpdatingIP(false);
    }
  };

  if (!mounted || deviceLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">로딩 중...</p>
        </div>
      </div>
    );
  }

  if (!device) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">장비를 찾을 수 없습니다</p>
          <button
            onClick={() => router.push('/dashboard')}
            className="mt-4 text-primary-600 hover:text-primary-700"
          >
            대시보드로 돌아가기
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center">
              <button
                onClick={() => router.push('/dashboard')}
                className="mr-4 p-2 hover:bg-gray-100 rounded-lg"
              >
                <ArrowLeft className="h-5 w-5" />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  {device.device_name}
                </h1>
                <p className="text-sm text-gray-600 mt-1">
                  {device.device_id} • {device.location || '위치 미설정'}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <div className={`flex items-center px-3 py-1 rounded-full ${
                device.is_online
                  ? 'bg-green-100 text-green-800'
                  : 'bg-gray-100 text-gray-800'
              }`}>
                <Wifi className="h-4 w-4 mr-1" />
                {device.is_online ? '온라인' : '오프라인'}
              </div>
              {/* Wake Up 버튼 - 오프라인일 때만 표시 */}
              {!device.is_online && (
                <button
                  onClick={handleWake}
                  disabled={isWaking}
                  className="inline-flex items-center px-4 py-2 border border-green-300 rounded-lg text-sm font-medium text-green-700 bg-white hover:bg-green-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  title="장비 깨우기"
                >
                  {isWaking ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-green-700 mr-2"></div>
                      깨우는 중...
                    </>
                  ) : (
                    <>
                      <Sun className="h-4 w-4 mr-2" />
                      깨우기
                    </>
                  )}
                </button>
              )}
              {/* Sleep 버튼 - 온라인일 때만 표시 */}
              {device.is_online && (
                <button
                  onClick={handleSleep}
                  disabled={isSleeping}
                  className="inline-flex items-center px-4 py-2 border border-indigo-300 rounded-lg text-sm font-medium text-indigo-700 bg-white hover:bg-indigo-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  title="절전 모드"
                >
                  {isSleeping ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-indigo-700 mr-2"></div>
                      전환 중...
                    </>
                  ) : (
                    <>
                      <Moon className="h-4 w-4 mr-2" />
                      절전
                    </>
                  )}
                </button>
              )}
              {/* 상태 보고 주기 설정 */}
              {device.is_online && (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-500">보고 주기:</span>
                  <select
                    value={device.status_report_interval || 60}
                    onChange={(e) => handleChangeInterval(Number(e.target.value))}
                    disabled={isChangingInterval}
                    className="px-2 py-1.5 text-sm border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50"
                    title="상태 보고 주기 변경"
                  >
                    <option value={10}>10초</option>
                    <option value={30}>30초</option>
                    <option value={60}>1분</option>
                    <option value={120}>2분</option>
                    <option value={300}>5분</option>
                    <option value={600}>10분</option>
                    <option value={1800}>30분</option>
                    <option value={3600}>1시간</option>
                  </select>
                </div>
              )}
              {/* 알람 버튼들 */}
              {device.is_online && (
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => handlePlayAlarm('beep')}
                    disabled={isPlayingAlarm}
                    className="inline-flex items-center px-3 py-2 border border-orange-300 rounded-l-lg text-sm font-medium text-orange-700 bg-white hover:bg-orange-50 disabled:opacity-50"
                    title="비프음"
                  >
                    <Volume2 className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => handlePlayAlarm('alert')}
                    disabled={isPlayingAlarm}
                    className="inline-flex items-center px-3 py-2 border-y border-orange-300 text-sm font-medium text-orange-700 bg-white hover:bg-orange-50 disabled:opacity-50"
                    title="경고음"
                  >
                    ⚠️
                  </button>
                  <button
                    onClick={() => handlePlayAlarm('emergency')}
                    disabled={isPlayingAlarm}
                    className="inline-flex items-center px-3 py-2 border border-red-400 rounded-r-lg text-sm font-medium text-red-700 bg-white hover:bg-red-50 disabled:opacity-50"
                    title="긴급 알람"
                  >
                    🚨
                  </button>
                </div>
              )}
              <button
                onClick={handleRestart}
                disabled={!device.is_online || isRestarting}
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                title="장비 재시작"
              >
                {isRestarting ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-700 mr-2"></div>
                    재시작 중...
                  </>
                ) : (
                  <>
                    <RotateCw className="h-4 w-4 mr-2" />
                    재시작
                  </>
                )}
              </button>
              <button
                onClick={handleRefresh}
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                새로고침
              </button>
              <button
                onClick={handleDelete}
                className="inline-flex items-center px-4 py-2 border border-red-300 rounded-lg text-sm font-medium text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                title="장비 삭제"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                삭제
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 장비 정보 섹션 */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">장비 정보</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                IP 주소
                <span className="ml-2 text-xs text-gray-500 font-normal">
                  (장비가 접근할 수 있는 백엔드 서버 주소)
                </span>
              </label>
              <div className="flex items-center space-x-2">
                {isEditingIP ? (
                  <>
                    <input
                      type="text"
                      value={ipAddress}
                      onChange={(e) => setIpAddress(e.target.value)}
                      placeholder="예: 192.168.1.100"
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                      disabled={isUpdatingIP}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !isUpdatingIP) {
                          handleIPUpdate();
                        } else if (e.key === 'Escape' && !isUpdatingIP) {
                          handleIPEditCancel();
                        }
                      }}
                    />
                    <button
                      onClick={handleIPUpdate}
                      disabled={isUpdatingIP}
                      className="p-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      title="저장 (Enter)"
                    >
                      {isUpdatingIP ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      ) : (
                        <Check className="h-4 w-4" />
                      )}
                    </button>
                    <button
                      onClick={handleIPEditCancel}
                      disabled={isUpdatingIP}
                      className="p-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      title="취소 (ESC)"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </>
                ) : (
                  <>
                    <div className="flex-1 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-gray-900">
                      {device.ip_address || (
                        <span className="text-gray-400 italic">미설정</span>
                      )}
                    </div>
                    <button
                      onClick={handleIPEditStart}
                      className="p-2 bg-primary-100 text-primary-700 rounded-lg hover:bg-primary-200 transition-colors"
                      title="IP 주소 편집"
                    >
                      <Edit2 className="h-4 w-4" />
                    </button>
                  </>
                )}
              </div>
              {!isEditingIP && !device.ip_address && (
                <p className="mt-1 text-xs text-amber-600">
                  ⚠️ IP 주소를 설정하면 장비에서 오디오 파일을 다운로드할 수 있습니다
                </p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                장비 ID
              </label>
              <div className="px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-gray-900">
                {device.device_id}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                위치
              </label>
              <div className="px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-gray-900">
                {device.location || '미설정'}
              </div>
            </div>
            {device.description && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  설명
                </label>
                <div className="px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-gray-900">
                  {device.description}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Video Stream Section */}
        {device.ip_address && (
          <div className="mb-6">
            <VideoPlayer
              streamUrl={device.ip_address}
              deviceName={device.device_name}
              isOnline={device.is_online}
            />
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Device Status */}
          <DeviceStatus device={device} status={status} isLoading={statusLoading} />

          {/* Device Control */}
          <DeviceControl device={device} />
        </div>

        {/* Voice Recognition Section */}
        <div className="space-y-6">
          {/* Voice Recognition Panel */}
          <VoiceRecognitionPanel
            device={device}
            onResult={async (result: RecognitionResult) => {
              setRecognitionResults((prev) => [...prev, result]);
              
              // 📱 음성인식 결과를 장비 디스플레이에 표시
              try {
                // 응급 상황인 경우 특별 포맷팅
                const displayText = result.is_emergency
                  ? `🚨 응급: ${result.text}`
                  : result.text;
                
                await controlAPI.display(device.id, 'show_text', displayText);
              } catch (error) {
                console.error('디스플레이 업데이트 실패:', error);
              }
            }}
            onProcessing={async (isProcessing) => {
              setIsProcessingAudio(isProcessing);
              
              // 📱 음성 처리 중 상태를 장비 디스플레이에 표시
              if (isProcessing) {
                try {
                  await controlAPI.display(device.id, 'show_text', '🎤 음성인식 중...');
                } catch (error) {
                  console.error('디스플레이 업데이트 실패:', error);
                }
              }
            }}
          />

          {/* Recognition Chat Window */}
          <RecognitionChatWindow
            results={recognitionResults}
            onClear={() => setRecognitionResults([])}
          />
        </div>
      </main>
    </div>
  );
}

