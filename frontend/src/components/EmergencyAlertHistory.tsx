'use client';

import { useQuery } from '@tanstack/react-query';
import { asrAPI } from '@/lib/api';
import { AlertTriangle, CheckCircle, XCircle, Clock } from 'lucide-react';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';

interface EmergencyAlertHistoryProps {
  deviceId?: number;
  limit?: number;
}

export default function EmergencyAlertHistory({
  deviceId,
  limit = 10,
}: EmergencyAlertHistoryProps) {
  const { data: alertsData, isLoading } = useQuery({
    queryKey: ['emergencyAlerts', deviceId, limit],
    queryFn: async () => {
      const { data } = await asrAPI.getEmergencyAlerts({
        device_id: deviceId,
        page: 1,
        page_size: limit,
      });
      return data;
    },
    refetchInterval: 10000, // 10초마다 자동 갱신
  });

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
        </div>
      </div>
    );
  }

  const alerts = alertsData?.alerts || [];

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical':
        return 'bg-red-600 text-white';
      case 'high':
        return 'bg-orange-500 text-white';
      case 'medium':
        return 'bg-yellow-500 text-white';
      case 'low':
        return 'bg-blue-500 text-white';
      default:
        return 'bg-gray-500 text-white';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'sent':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'acknowledged':
        return <CheckCircle className="h-4 w-4 text-blue-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          <AlertTriangle className="h-5 w-5 text-red-500 mr-2" />
          응급 상황 이력
        </h3>
        {alertsData && (
          <span className="text-sm text-gray-500">
            총 {alertsData.total}건
          </span>
        )}
      </div>

      {alerts.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <AlertTriangle className="h-12 w-12 text-gray-300 mx-auto mb-2" />
          <p>응급 상황 이력이 없습니다.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${getPriorityColor(
                        alert.priority
                      )}`}
                    >
                      {alert.priority.toUpperCase()}
                    </span>
                    {getStatusIcon(alert.status)}
                    <span className="text-xs text-gray-500">
                      {alert.device_name}
                    </span>
                  </div>
                  <p className="text-sm font-medium text-gray-900 mb-1">
                    {alert.recognized_text}
                  </p>
                  {alert.emergency_keywords.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {alert.emergency_keywords.map((keyword, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs"
                        >
                          {keyword}
                        </span>
                      ))}
                    </div>
                  )}
                  <p className="text-xs text-gray-500 mt-2">
                    {format(new Date(alert.created_at), 'yyyy-MM-dd HH:mm:ss', {
                      locale: ko,
                    })}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

