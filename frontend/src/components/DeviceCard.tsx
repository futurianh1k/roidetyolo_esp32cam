'use client';

import { Device, DeviceStatus } from '@/lib/api';
import { Wifi, WifiOff, MapPin, Calendar, ChevronRight, Battery, Thermometer, Cpu, Camera, Mic } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { ko } from 'date-fns/locale';

interface DeviceCardProps {
  device: Device;
  status?: DeviceStatus | null;
  isOnline?: boolean;
  onClick: () => void;
}

export default function DeviceCard({ device, status, isOnline, onClick }: DeviceCardProps) {
  // isOnline prop이 있으면 사용, 없으면 device.is_online 사용
  const deviceOnline = isOnline !== undefined ? isOnline : device.is_online;
  
  const lastSeenText = device.last_seen_at
    ? formatDistanceToNow(new Date(device.last_seen_at), {
        addSuffix: true,
        locale: ko,
      })
    : '없음';

  // 배터리 색상
  const getBatteryColor = (level: number) => {
    if (level > 50) return 'text-green-500';
    if (level > 20) return 'text-yellow-500';
    return 'text-red-500';
  };

  // 온도 색상
  const getTempColor = (temp: number) => {
    if (temp > 60) return 'text-red-500';
    if (temp > 45) return 'text-yellow-500';
    return 'text-blue-500';
  };

  // 컴포넌트 상태 색상
  const getComponentStatusColor = (statusValue: string) => {
    switch (statusValue) {
      case 'active':
        return 'text-green-500';
      case 'paused':
        return 'text-yellow-500';
      default:
        return 'text-gray-400';
    }
  };

  return (
    <div
      onClick={onClick}
      className="bg-white rounded-lg shadow hover:shadow-lg transition-all cursor-pointer border border-gray-200 overflow-hidden group"
    >
      {/* Status Bar */}
      <div
        className={`h-2 transition-colors ${
          deviceOnline ? 'bg-green-500' : 'bg-gray-400'
        }`}
      ></div>

      <div className="p-6">
        {/* Header */}
        <div className="flex justify-between items-start mb-4">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 mb-1 group-hover:text-primary-600 transition-colors">
              {device.device_name}
            </h3>
            <p className="text-sm text-gray-500 font-mono">{device.device_id}</p>
          </div>
          <div className="flex items-center space-x-2">
            {deviceOnline ? (
              <div className="flex items-center text-green-600">
                <span className="relative flex h-3 w-3 mr-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                </span>
                <Wifi className="h-5 w-5" />
                <span className="text-sm ml-1">온라인</span>
              </div>
            ) : (
              <div className="flex items-center text-gray-400">
                <WifiOff className="h-5 w-5" />
                <span className="text-sm ml-1">오프라인</span>
              </div>
            )}
          </div>
        </div>

        {/* 실시간 상태 표시 (온라인이고 상태 데이터가 있을 때만) */}
        {deviceOnline && status && (
          <div className="grid grid-cols-4 gap-2 mb-4 py-3 px-2 bg-gray-50 rounded-lg">
            {/* 배터리 */}
            {status.battery_level !== null && status.battery_level !== undefined && (
              <div className="flex flex-col items-center">
                <Battery className={`h-4 w-4 ${getBatteryColor(status.battery_level)}`} />
                <span className="text-xs text-gray-600 mt-1">{status.battery_level}%</span>
              </div>
            )}
            
            {/* 온도 */}
            {status.temperature !== null && status.temperature !== undefined && (
              <div className="flex flex-col items-center">
                <Thermometer className={`h-4 w-4 ${getTempColor(status.temperature)}`} />
                <span className="text-xs text-gray-600 mt-1">{status.temperature.toFixed(1)}°C</span>
              </div>
            )}
            
            {/* 카메라 상태 */}
            <div className="flex flex-col items-center">
              <Camera className={`h-4 w-4 ${getComponentStatusColor(status.camera_status)}`} />
              <span className="text-xs text-gray-600 mt-1">
                {status.camera_status === 'active' ? 'ON' : 'OFF'}
              </span>
            </div>
            
            {/* 마이크 상태 */}
            <div className="flex flex-col items-center">
              <Mic className={`h-4 w-4 ${getComponentStatusColor(status.mic_status)}`} />
              <span className="text-xs text-gray-600 mt-1">
                {status.mic_status === 'active' ? 'ON' : 'OFF'}
              </span>
            </div>
          </div>
        )}

        {/* Info */}
        <div className="space-y-2 mb-4">
          {device.location && (
            <div className="flex items-center text-sm text-gray-600">
              <MapPin className="h-4 w-4 mr-2 text-gray-400" />
              {device.location}
            </div>
          )}
          {device.ip_address && (
            <div className="flex items-center text-sm text-gray-600">
              <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded">
                {device.ip_address}
              </span>
            </div>
          )}
          <div className="flex items-center text-sm text-gray-600">
            <Calendar className="h-4 w-4 mr-2 text-gray-400" />
            최근 연결: {lastSeenText}
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-between items-center pt-4 border-t border-gray-200">
          <div className="text-sm">
            <span className="text-gray-500">타입: </span>
            <span className="text-gray-900 font-medium">{device.device_type}</span>
          </div>
          <ChevronRight className="h-5 w-5 text-gray-400 group-hover:text-primary-600 transition-colors" />
        </div>
      </div>
    </div>
  );
}

