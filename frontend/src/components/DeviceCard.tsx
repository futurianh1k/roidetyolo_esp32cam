'use client';

import { Device } from '@/lib/api';
import { Wifi, WifiOff, MapPin, Calendar, ChevronRight } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { ko } from 'date-fns/locale';

interface DeviceCardProps {
  device: Device;
  onClick: () => void;
}

export default function DeviceCard({ device, onClick }: DeviceCardProps) {
  const lastSeenText = device.last_seen_at
    ? formatDistanceToNow(new Date(device.last_seen_at), {
        addSuffix: true,
        locale: ko,
      })
    : '없음';

  return (
    <div
      onClick={onClick}
      className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow cursor-pointer border border-gray-200 overflow-hidden"
    >
      {/* Status Bar */}
      <div
        className={`h-2 ${
          device.is_online ? 'bg-green-500' : 'bg-gray-400'
        }`}
      ></div>

      <div className="p-6">
        {/* Header */}
        <div className="flex justify-between items-start mb-4">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 mb-1">
              {device.device_name}
            </h3>
            <p className="text-sm text-gray-500">{device.device_id}</p>
          </div>
          <div className="flex items-center space-x-2">
            {device.is_online ? (
              <div className="flex items-center text-green-600">
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

        {/* Info */}
        <div className="space-y-2 mb-4">
          {device.location && (
            <div className="flex items-center text-sm text-gray-600">
              <MapPin className="h-4 w-4 mr-2" />
              {device.location}
            </div>
          )}
          <div className="flex items-center text-sm text-gray-600">
            <Calendar className="h-4 w-4 mr-2" />
            최근 연결: {lastSeenText}
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-between items-center pt-4 border-t border-gray-200">
          <div className="text-sm">
            <span className="text-gray-500">타입: </span>
            <span className="text-gray-900 font-medium">{device.device_type}</span>
          </div>
          <ChevronRight className="h-5 w-5 text-gray-400" />
        </div>
      </div>
    </div>
  );
}

