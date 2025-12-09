'use client';

import { useState } from 'react';
import { X } from 'lucide-react';
import toast from 'react-hot-toast';
import { devicesAPI, DeviceCreateRequest } from '@/lib/api';

interface RegisterDeviceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function RegisterDeviceModal({
  isOpen,
  onClose,
  onSuccess,
}: RegisterDeviceModalProps) {
  const [formData, setFormData] = useState<DeviceCreateRequest>({
    device_id: '',
    device_name: '',
    device_type: 'CoreS3',
    ip_address: '',
    location: '',
    description: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  if (!isOpen) return null;

  // 폼 검증
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    // device_id 검증
    if (!formData.device_id.trim()) {
      newErrors.device_id = '장비 ID는 필수입니다';
    } else if (!/^[a-zA-Z0-9_-]+$/.test(formData.device_id)) {
      newErrors.device_id = '영문, 숫자, 언더스코어(_), 하이픈(-)만 사용 가능합니다';
    } else if (formData.device_id.length < 3 || formData.device_id.length > 50) {
      newErrors.device_id = '장비 ID는 3-50자여야 합니다';
    }

    // device_name 검증
    if (!formData.device_name.trim()) {
      newErrors.device_name = '장비명은 필수입니다';
    } else if (formData.device_name.length > 100) {
      newErrors.device_name = '장비명은 100자 이하여야 합니다';
    }

    // ip_address 검증
    if (formData.ip_address && formData.ip_address.trim()) {
      const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/;
      if (!ipRegex.test(formData.ip_address)) {
        newErrors.ip_address = '올바른 IP 주소 형식이 아닙니다 (예: 192.168.1.100)';
      } else {
        // 각 옥텟이 0-255 범위인지 확인
        const octets = formData.ip_address.split('.');
        if (octets.some(octet => parseInt(octet) > 255 || parseInt(octet) < 0)) {
          newErrors.ip_address = 'IP 주소의 각 숫자는 0-255 사이여야 합니다';
        }
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // 폼 제출
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      toast.error('입력 정보를 확인해주세요');
      return;
    }

    setIsSubmitting(true);

    try {
      // API 요청 데이터 준비 (빈 문자열은 undefined로)
      const requestData: DeviceCreateRequest = {
        device_id: formData.device_id.trim(),
        device_name: formData.device_name.trim(),
        device_type: formData.device_type || 'CoreS3',
        ip_address: formData.ip_address?.trim() || undefined,
        location: formData.location?.trim() || undefined,
        description: formData.description?.trim() || undefined,
      };

      const { data } = await devicesAPI.create(requestData);

      toast.success(`장비 "${data.device_name}"가 등록되었습니다`);
      
      // 폼 초기화
      setFormData({
        device_id: '',
        device_name: '',
        device_type: 'CoreS3',
        ip_address: '',
        location: '',
        description: '',
      });
      setErrors({});

      // 성공 콜백 호출 (목록 새로고침)
      onSuccess();
      
      // 모달 닫기
      onClose();
    } catch (error: any) {
      console.error('장비 등록 실패:', error);
      
      const errorMessage = error.response?.data?.detail || '장비 등록에 실패했습니다';
      
      if (errorMessage.includes('이미 등록된')) {
        toast.error('이미 등록된 장비 ID입니다');
        setErrors({ device_id: '이미 사용 중인 ID입니다' });
      } else {
        toast.error(errorMessage);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // 입력 변경 핸들러
  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    
    // 에러 메시지 지우기
    if (errors[name]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  // ESC 키로 닫기
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
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
            <h2 className="text-xl font-semibold text-gray-900">
              장비 등록
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
              disabled={isSubmitting}
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          {/* 폼 */}
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            {/* 장비 ID */}
            <div>
              <label htmlFor="device_id" className="block text-sm font-medium text-gray-700 mb-1">
                장비 ID <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                id="device_id"
                name="device_id"
                value={formData.device_id}
                onChange={handleChange}
                placeholder="core_s3_001"
                className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                  errors.device_id ? 'border-red-500' : 'border-gray-300'
                }`}
                disabled={isSubmitting}
                required
              />
              {errors.device_id && (
                <p className="mt-1 text-sm text-red-500">{errors.device_id}</p>
              )}
              <p className="mt-1 text-xs text-gray-500">
                영문, 숫자, 언더스코어(_), 하이픈(-) 사용 가능 (3-50자)
              </p>
            </div>

            {/* 장비명 */}
            <div>
              <label htmlFor="device_name" className="block text-sm font-medium text-gray-700 mb-1">
                장비명 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                id="device_name"
                name="device_name"
                value={formData.device_name}
                onChange={handleChange}
                placeholder="Core S3 Camera"
                className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                  errors.device_name ? 'border-red-500' : 'border-gray-300'
                }`}
                disabled={isSubmitting}
                required
              />
              {errors.device_name && (
                <p className="mt-1 text-sm text-red-500">{errors.device_name}</p>
              )}
            </div>

            {/* 장비 타입 */}
            <div>
              <label htmlFor="device_type" className="block text-sm font-medium text-gray-700 mb-1">
                장비 타입
              </label>
              <select
                id="device_type"
                name="device_type"
                value={formData.device_type}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                disabled={isSubmitting}
              >
                <option value="CoreS3">M5Stack Core S3</option>
                <option value="ESP32CAM">ESP32-CAM</option>
                <option value="Other">기타</option>
              </select>
            </div>

            {/* IP 주소 */}
            <div>
              <label htmlFor="ip_address" className="block text-sm font-medium text-gray-700 mb-1">
                IP 주소
              </label>
              <input
                type="text"
                id="ip_address"
                name="ip_address"
                value={formData.ip_address}
                onChange={handleChange}
                placeholder="192.168.1.100"
                className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                  errors.ip_address ? 'border-red-500' : 'border-gray-300'
                }`}
                disabled={isSubmitting}
              />
              {errors.ip_address && (
                <p className="mt-1 text-sm text-red-500">{errors.ip_address}</p>
              )}
              <p className="mt-1 text-xs text-gray-500">
                장비의 네트워크 IP 주소 (선택사항)
              </p>
            </div>

            {/* 위치 */}
            <div>
              <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-1">
                설치 위치
              </label>
              <input
                type="text"
                id="location"
                name="location"
                value={formData.location}
                onChange={handleChange}
                placeholder="1층 사무실"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                disabled={isSubmitting}
              />
            </div>

            {/* 설명 */}
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
                설명
              </label>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleChange}
                placeholder="장비에 대한 간단한 설명..."
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
                disabled={isSubmitting}
              />
            </div>

            {/* 버튼 */}
            <div className="flex justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                disabled={isSubmitting}
              >
                취소
              </button>
              <button
                type="submit"
                className="px-4 py-2 border border-transparent rounded-lg text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <span className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    등록 중...
                  </span>
                ) : (
                  '등록'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
