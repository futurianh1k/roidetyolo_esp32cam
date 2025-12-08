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
} from 'lucide-react';
import DeviceControl from '@/components/DeviceControl';
import DeviceStatus from '@/components/DeviceStatus';

export default function DeviceDetailPage() {
  const router = useRouter();
  const params = useParams();
  const deviceId = Number(params.id);
  const { isAuthenticated } = useAuthStore();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    if (!isAuthenticated && mounted) {
      router.push('/login');
    }
  }, [isAuthenticated, mounted, router]);

  // 장비 정보 조회
  const { data: device, isLoading: deviceLoading, refetch: refetchDevice } = useQuery({
    queryKey: ['device', deviceId],
    queryFn: async () => {
      const { data } = await devicesAPI.getById(deviceId);
      return data;
    },
    enabled: mounted && isAuthenticated && !isNaN(deviceId),
  });

  // 장비 최신 상태 조회
  const { data: status, isLoading: statusLoading, refetch: refetchStatus } = useQuery({
    queryKey: ['deviceStatus', deviceId],
    queryFn: async () => {
      const { data } = await devicesAPI.getLatestStatus(deviceId);
      return data;
    },
    enabled: mounted && isAuthenticated && !isNaN(deviceId),
    refetchInterval: 5000, // 5초마다 자동 갱신
  });

  const handleRefresh = () => {
    refetchDevice();
    refetchStatus();
    toast.success('새로고침되었습니다');
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
                onClick={handleRefresh}
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                새로고침
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Device Status */}
          <DeviceStatus device={device} status={status} isLoading={statusLoading} />

          {/* Device Control */}
          <DeviceControl device={device} />
        </div>
      </main>
    </div>
  );
}

