'use client';

import { useState } from 'react';
import { X, Trash2, AlertTriangle } from 'lucide-react';
import toast from 'react-hot-toast';
import { devicesAPI, Device } from '@/lib/api';

interface DeleteDeviceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  devices: Device[];
}

export default function DeleteDeviceModal({
  isOpen,
  onClose,
  onSuccess,
  devices,
}: DeleteDeviceModalProps) {
  const [selectedDeviceId, setSelectedDeviceId] = useState<number | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  if (!isOpen) return null;

  const selectedDevice = devices.find(d => d.id === selectedDeviceId);

  // 삭제 실행
  const handleDelete = async () => {
    if (!selectedDeviceId) {
      toast.error('삭제할 장비를 선택해주세요');
      return;
    }

    setIsDeleting(true);

    try {
      await devicesAPI.delete(selectedDeviceId);
      
      toast.success(`장비 "${selectedDevice?.device_name}"가 삭제되었습니다`);
      
      // 선택 초기화
      setSelectedDeviceId(null);
      
      // 성공 콜백 호출 (목록 새로고침)
      onSuccess();
      
      // 모달 닫기
      onClose();
    } catch (error: any) {
      console.error('장비 삭제 실패:', error);
      console.error('에러 상세:', error.response?.data || error.message);
      
      const errorMessage = error.response?.data?.detail || error.message || '장비 삭제에 실패했습니다';
      
      if (error.response?.status === 401 || error.response?.status === 403) {
        toast.error('인증 오류입니다. 로그인을 다시 시도해주세요.');
      } else if (error.response?.status === 404) {
        toast.error('장비를 찾을 수 없습니다');
      } else if (error.response?.status === 0 || !error.response) {
        toast.error('서버에 연결할 수 없습니다. 네트워크 연결을 확인해주세요.');
      } else {
        toast.error(errorMessage);
      }
    } finally {
      setIsDeleting(false);
    }
  };

  // ESC 키로 닫기
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape' && !isDeleting) {
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto" onKeyDown={handleKeyDown}>
      {/* 배경 오버레이 */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />

      {/* 모달 컨테이너 */}
      <div className="flex min-h-screen items-center justify-center p-4">
        <div
          className="relative bg-white rounded-lg shadow-xl w-full max-w-md"
          onClick={(e) => e.stopPropagation()}
        >
          {/* 헤더 */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <div className="flex items-center">
              <Trash2 className="h-6 w-6 text-red-600 mr-2" />
              <h2 className="text-xl font-semibold text-gray-900">
                장비 삭제
              </h2>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
              disabled={isDeleting}
              title="닫기 (ESC)"
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          {/* 내용 */}
          <div className="p-6">
            {/* 경고 메시지 */}
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex">
                <AlertTriangle className="h-5 w-5 text-red-600 mr-2 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-red-800">
                    주의: 이 작업은 되돌릴 수 없습니다
                  </p>
                  <p className="text-sm text-red-700 mt-1">
                    선택한 장비와 관련된 모든 데이터가 영구적으로 삭제됩니다.
                  </p>
                </div>
              </div>
            </div>

            {/* 장비 선택 */}
            <div>
              <label htmlFor="device_select" className="block text-sm font-medium text-gray-700 mb-2">
                삭제할 장비 선택 <span className="text-red-500">*</span>
              </label>
              <select
                id="device_select"
                value={selectedDeviceId || ''}
                onChange={(e) => setSelectedDeviceId(e.target.value ? Number(e.target.value) : null)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
                disabled={isDeleting}
              >
                <option value="">-- 장비를 선택하세요 --</option>
                {devices.map((device) => (
                  <option key={device.id} value={device.id}>
                    {device.device_name} ({device.device_id}) 
                    {device.is_online ? ' - 온라인' : ' - 오프라인'}
                  </option>
                ))}
              </select>
            </div>

            {/* 선택된 장비 정보 표시 */}
            {selectedDevice && (
              <div className="mt-4 p-4 bg-gray-50 border border-gray-200 rounded-lg">
                <h4 className="text-sm font-medium text-gray-900 mb-2">
                  삭제될 장비 정보
                </h4>
                <dl className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <dt className="text-gray-600">장비명:</dt>
                    <dd className="font-medium text-gray-900">{selectedDevice.device_name}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-gray-600">장비 ID:</dt>
                    <dd className="font-mono text-gray-900">{selectedDevice.device_id}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-gray-600">타입:</dt>
                    <dd className="text-gray-900">{selectedDevice.device_type}</dd>
                  </div>
                  {selectedDevice.location && (
                    <div className="flex justify-between">
                      <dt className="text-gray-600">위치:</dt>
                      <dd className="text-gray-900">{selectedDevice.location}</dd>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <dt className="text-gray-600">상태:</dt>
                    <dd>
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                        selectedDevice.is_online
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {selectedDevice.is_online ? '온라인' : '오프라인'}
                      </span>
                    </dd>
                  </div>
                </dl>
              </div>
            )}
          </div>

          {/* 버튼 */}
          <div className="flex justify-end space-x-3 px-6 py-4 bg-gray-50 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isDeleting}
            >
              취소
            </button>
            <button
              type="button"
              onClick={handleDelete}
              className="px-4 py-2 border border-transparent rounded-lg text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isDeleting || !selectedDeviceId}
            >
              {isDeleting ? (
                <span className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  삭제 중...
                </span>
              ) : (
                <span className="flex items-center">
                  <Trash2 className="h-4 w-4 mr-2" />
                  삭제
                </span>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
