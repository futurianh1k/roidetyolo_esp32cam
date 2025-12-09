'use client';

import { Device, DeviceStatus as Status } from '@/lib/api';
import { Battery, Cpu, HardDrive, Thermometer, Camera, Mic, Monitor } from 'lucide-react';

interface DeviceStatusProps {
  device: Device;
  status: Status | null | undefined;
  isLoading: boolean;
}

export default function DeviceStatus({ device, status, isLoading }: DeviceStatusProps) {
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">장비 상태</h2>
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="animate-pulse flex items-center">
              <div className="rounded-full bg-gray-200 h-10 w-10"></div>
              <div className="ml-4 flex-1">
                <div className="h-4 bg-gray-200 rounded w-1/3 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // 상태 정보가 없을 때 (장비가 아직 연결되지 않음)
  if (!status) {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">장비 상태</h2>
          <div className="text-center py-8">
            <Monitor className="h-12 w-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-600">장비가 아직 연결되지 않았습니다</p>
            <p className="text-sm text-gray-500 mt-2">
              장비가 MQTT 브로커에 연결되면 상태가 표시됩니다
            </p>
          </div>
        </div>

        {/* Component Status - 연결 안됨 상태 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">컴포넌트 상태</h2>
          <div className="space-y-3">
            {[
              { icon: Camera, label: '카메라' },
              { icon: Mic, label: '마이크' },
            ].map((item) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.label}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center">
                    <Icon className="h-5 w-5 text-gray-400 mr-3" />
                    <span className="text-sm font-medium text-gray-600">
                      {item.label}
                    </span>
                  </div>
                  <span className="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                    대기 중
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  const statusItems = [
    {
      icon: Battery,
      label: '배터리',
      value: status?.battery_level ? `${status.battery_level}%` : 'N/A',
      color: status?.battery_level
        ? status.battery_level > 50
          ? 'text-green-600 bg-green-100'
          : status.battery_level > 20
          ? 'text-yellow-600 bg-yellow-100'
          : 'text-red-600 bg-red-100'
        : 'text-gray-600 bg-gray-100',
    },
    {
      icon: HardDrive,
      label: '메모리',
      value: status?.memory_usage
        ? `${(status.memory_usage / 1024).toFixed(1)} KB`
        : 'N/A',
      color: 'text-blue-600 bg-blue-100',
    },
    {
      icon: Thermometer,
      label: 'CPU 온도',
      value: status?.temperature ? `${status.temperature.toFixed(1)}°C` : 'N/A',
      color: status?.temperature
        ? status.temperature > 60
          ? 'text-red-600 bg-red-100'
          : 'text-green-600 bg-green-100'
        : 'text-gray-600 bg-gray-100',
    },
    {
      icon: Cpu,
      label: 'CPU 사용률',
      value: status?.cpu_usage ? `${status.cpu_usage}%` : 'N/A',
      color: 'text-purple-600 bg-purple-100',
    },
  ];

  const componentStatus = [
    {
      icon: Camera,
      label: '카메라',
      status: status?.camera_status || 'stopped',
    },
    {
      icon: Mic,
      label: '마이크',
      status: status?.mic_status || 'stopped',
    },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'paused':
        return 'bg-yellow-100 text-yellow-800';
      case 'stopped':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active':
        return '활성';
      case 'paused':
        return '일시정지';
      case 'stopped':
        return '정지';
      default:
        return '알 수 없음';
    }
  };

  return (
    <div className="space-y-6">
      {/* System Status */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">시스템 상태</h2>
        <div className="space-y-4">
          {statusItems.map((item) => {
            const Icon = item.icon;
            return (
              <div key={item.label} className="flex items-center">
                <div className={`p-2 rounded-lg ${item.color}`}>
                  <Icon className="h-6 w-6" />
                </div>
                <div className="ml-4 flex-1">
                  <p className="text-sm font-medium text-gray-900">{item.label}</p>
                  <p className="text-sm text-gray-600">{item.value}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Component Status */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">컴포넌트 상태</h2>
        <div className="space-y-3">
          {componentStatus.map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.label}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center">
                  <Icon className="h-5 w-5 text-gray-600 mr-3" />
                  <span className="text-sm font-medium text-gray-900">
                    {item.label}
                  </span>
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(
                    item.status
                  )}`}
                >
                  {getStatusText(item.status)}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

