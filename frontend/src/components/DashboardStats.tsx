'use client';

import { Monitor, Wifi, WifiOff } from 'lucide-react';

interface DashboardStatsProps {
  totalDevices: number;
  onlineDevices: number;
  offlineDevices: number;
}

export default function DashboardStats({
  totalDevices,
  onlineDevices,
  offlineDevices,
}: DashboardStatsProps) {
  const stats = [
    {
      name: '전체 장비',
      value: totalDevices,
      icon: Monitor,
      color: 'bg-blue-500',
    },
    {
      name: '온라인',
      value: onlineDevices,
      icon: Wifi,
      color: 'bg-green-500',
    },
    {
      name: '오프라인',
      value: offlineDevices,
      icon: WifiOff,
      color: 'bg-gray-400',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {stats.map((stat) => {
        const Icon = stat.icon;
        return (
          <div
            key={stat.name}
            className="bg-white rounded-lg shadow p-6 border border-gray-200"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                <p className="mt-2 text-3xl font-semibold text-gray-900">
                  {stat.value}
                </p>
              </div>
              <div className={`p-3 rounded-lg ${stat.color}`}>
                <Icon className="h-8 w-8 text-white" />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

