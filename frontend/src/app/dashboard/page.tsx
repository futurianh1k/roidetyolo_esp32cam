'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { authAPI, devicesAPI, Device } from '@/lib/api';
import { useAuthStore } from '@/store/authStore';
import toast from 'react-hot-toast';
import {
  LogOut,
  RefreshCw,
  Monitor,
  Wifi,
  WifiOff,
  ChevronRight,
} from 'lucide-react';
import DeviceCard from '@/components/DeviceCard';
import DashboardStats from '@/components/DashboardStats';

export default function DashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated, clearAuth } = useAuthStore();
  const [mounted, setMounted] = useState(false);

  // 클라이언트 사이드에서만 실행
  useEffect(() => {
    setMounted(true);
    if (!isAuthenticated && mounted) {
      router.push('/login');
    }
  }, [isAuthenticated, mounted, router]);

  // 사용자 정보 조회
  const { data: currentUser, isLoading: userLoading } = useQuery({
    queryKey: ['currentUser'],
    queryFn: async () => {
      const { data } = await authAPI.getCurrentUser();
      return data;
    },
    enabled: mounted && isAuthenticated,
  });

  // 장비 목록 조회
  const { data: devicesData, isLoading: devicesLoading, refetch } = useQuery({
    queryKey: ['devices'],
    queryFn: async () => {
      const { data } = await devicesAPI.getList({ page: 1, page_size: 100 });
      return data;
    },
    enabled: mounted && isAuthenticated,
    refetchInterval: 10000, // 10초마다 자동 갱신
  });

  const handleLogout = async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        await authAPI.logout(refreshToken);
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      clearAuth();
      toast.success('로그아웃되었습니다');
      router.push('/login');
    }
  };

  const handleRefresh = () => {
    refetch();
    toast.success('새로고침되었습니다');
  };

  if (!mounted || userLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">로딩 중...</p>
        </div>
      </div>
    );
  }

  const devices = devicesData?.devices || [];
  const onlineDevices = devices.filter(d => d.is_online).length;
  const offlineDevices = devices.length - onlineDevices;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Core S3 Management System
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                {currentUser?.username} ({currentUser?.role})
              </p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={handleRefresh}
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                새로고침
              </button>
              <button
                onClick={handleLogout}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-lg text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                <LogOut className="h-4 w-4 mr-2" />
                로그아웃
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats */}
        <DashboardStats
          totalDevices={devices.length}
          onlineDevices={onlineDevices}
          offlineDevices={offlineDevices}
        />

        {/* Devices Section */}
        <div className="mt-8">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-gray-900">
              장비 목록
            </h2>
            {devicesLoading && (
              <div className="flex items-center text-sm text-gray-500">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600 mr-2"></div>
                로딩 중...
              </div>
            )}
          </div>

          {devices.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <Monitor className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                등록된 장비가 없습니다
              </h3>
              <p className="text-gray-600">
                Core S3 장비를 등록하여 원격 관리를 시작하세요
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {devices.map((device) => (
                <DeviceCard
                  key={device.id}
                  device={device}
                  onClick={() => router.push(`/devices/${device.id}`)}
                />
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

