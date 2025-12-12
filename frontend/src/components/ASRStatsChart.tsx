'use client';

import { useQuery } from '@tanstack/react-query';
import { asrAPI } from '@/lib/api';
import { BarChart3, TrendingUp, AlertTriangle, Clock } from 'lucide-react';

interface ASRStatsChartProps {
  deviceId?: number;
  startDate?: string;
  endDate?: string;
}

export default function ASRStatsChart({
  deviceId,
  startDate,
  endDate,
}: ASRStatsChartProps) {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['asrStats', deviceId, startDate, endDate],
    queryFn: async () => {
      const { data } = await asrAPI.getResultStats({
        device_id: deviceId,
        start_date: startDate,
        end_date: endDate,
      });
      return data;
    },
    refetchInterval: 30000, // 30초마다 자동 갱신
  });

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
        <p className="text-gray-500 text-center">데이터를 불러올 수 없습니다.</p>
      </div>
    );
  }

  const statsCards = [
    {
      name: '총 인식 횟수',
      value: stats.total_count.toLocaleString(),
      icon: BarChart3,
      color: 'bg-blue-500',
    },
    {
      name: '응급 상황',
      value: stats.emergency_count.toLocaleString(),
      icon: AlertTriangle,
      color: 'bg-red-500',
    },
    {
      name: '총 음성 길이',
      value: `${stats.total_duration.toFixed(1)}초`,
      icon: Clock,
      color: 'bg-green-500',
    },
    {
      name: '평균 음성 길이',
      value: `${stats.average_duration.toFixed(2)}초`,
      icon: TrendingUp,
      color: 'bg-purple-500',
    },
  ];

  return (
    <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">ASR 통계</h3>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {statsCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <div
              key={stat.name}
              className="bg-gray-50 rounded-lg p-4 border border-gray-200"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-gray-600">{stat.name}</p>
                  <p className="mt-1 text-xl font-semibold text-gray-900">
                    {stat.value}
                  </p>
                </div>
                <div className={`p-2 rounded-lg ${stat.color}`}>
                  <Icon className="h-5 w-5 text-white" />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* 장비별 통계 */}
      {stats.device_stats && stats.device_stats.length > 0 && (
        <div className="mt-6">
          <h4 className="text-sm font-medium text-gray-700 mb-3">장비별 통계</h4>
          <div className="space-y-2">
            {stats.device_stats.map((device) => (
              <div
                key={device.device_id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <span className="text-sm font-medium text-gray-900">
                  {device.device_name}
                </span>
                <div className="flex items-center space-x-4 text-sm text-gray-600">
                  <span>{device.count}회</span>
                  <span>{device.total_duration.toFixed(1)}초</span>
                  {device.emergency_count > 0 && (
                    <span className="text-red-600 font-medium">
                      🚨 {device.emergency_count}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

