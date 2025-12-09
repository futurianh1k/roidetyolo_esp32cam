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
} from 'lucide-react';
import DeviceControl from '@/components/DeviceControl';
import DeviceStatus from '@/components/DeviceStatus';
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
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [recognitionResults, setRecognitionResults] = useState<RecognitionResult[]>([]);

  useEffect(() => {
    setMounted(true);
    // TODO: 로그인 기능 수정 후 인증 체크 활성화
    // if (!isAuthenticated && mounted) {
    //   router.push('/login');
    // }
  }, [isAuthenticated, mounted, router]);

  // 장비 정보 조회
  const { data: device, isLoading: deviceLoading, refetch: refetchDevice } = useQuery({
    queryKey: ['device', deviceId],
    queryFn: async () => {
      const { data } = await devicesAPI.getById(deviceId);
      return data;
    },
    // TODO: 로그인 수정 후 isAuthenticated 체크 활성화
    enabled: mounted && !isNaN(deviceId),
  });

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
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Device Status */}
          <DeviceStatus device={device} status={status} isLoading={statusLoading} />

          {/* Device Control */}
          <DeviceControl device={device} />
        </div>

        {/* Voice Recognition Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Voice Recognition Panel */}
          <VoiceRecognitionPanel
            device={device}
            onResult={(result: RecognitionResult) => {
              setRecognitionResults((prev) => [...prev, result]);
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

