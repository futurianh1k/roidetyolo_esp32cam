'use client';

import { useState } from 'react';
import { Device, controlAPI } from '@/lib/api';
import toast from 'react-hot-toast';
import { Camera, Mic, Volume2, Monitor, Play, Pause, Square } from 'lucide-react';

interface DeviceControlProps {
  device: Device;
}

export default function DeviceControl({ device }: DeviceControlProps) {
  const [isLoading, setIsLoading] = useState<string | null>(null);
  const [displayText, setDisplayText] = useState('');

  const handleCameraControl = async (action: 'start' | 'pause' | 'stop') => {
    if (!device.is_online) {
      toast.error('장비가 오프라인 상태입니다');
      return;
    }

    setIsLoading(`camera-${action}`);
    try {
      await controlAPI.camera(device.id, action);
      toast.success(`카메라 ${action === 'start' ? '시작' : action === 'pause' ? '일시정지' : '정지'} 명령 전송`);
    } catch (error) {
      toast.error('카메라 제어 실패');
    } finally {
      setIsLoading(null);
    }
  };

  const handleMicControl = async (action: 'start' | 'pause' | 'stop') => {
    if (!device.is_online) {
      toast.error('장비가 오프라인 상태입니다');
      return;
    }

    setIsLoading(`mic-${action}`);
    try {
      await controlAPI.microphone(device.id, action);
      toast.success(`마이크 ${action === 'start' ? '시작' : action === 'pause' ? '일시정지' : '정지'} 명령 전송`);
    } catch (error) {
      toast.error('마이크 제어 실패');
    } finally {
      setIsLoading(null);
    }
  };

  const handleDisplayControl = async (action: 'show_text' | 'clear') => {
    if (!device.is_online) {
      toast.error('장비가 오프라인 상태입니다');
      return;
    }

    if (action === 'show_text' && !displayText.trim()) {
      toast.error('표시할 텍스트를 입력하세요');
      return;
    }

    setIsLoading(`display-${action}`);
    try {
      await controlAPI.display(device.id, action, displayText);
      toast.success(action === 'show_text' ? '텍스트 표시 명령 전송' : '화면 지우기 명령 전송');
      if (action === 'clear') {
        setDisplayText('');
      }
    } catch (error) {
      toast.error('디스플레이 제어 실패');
    } finally {
      setIsLoading(null);
    }
  };

  const ControlButton = ({ onClick, icon: Icon, label, loadingKey, variant = 'default' }: any) => {
    const isButtonLoading = isLoading === loadingKey;
    const baseClasses = 'inline-flex items-center justify-center px-4 py-2 rounded-lg text-sm font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed';
    const variantClasses = {
      default: 'bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500',
      secondary: 'bg-gray-200 text-gray-800 hover:bg-gray-300 focus:ring-gray-500',
      danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
    };

    return (
      <button
        onClick={onClick}
        disabled={!device.is_online || isButtonLoading}
        className={`${baseClasses} ${variantClasses[variant]}`}
      >
        {isButtonLoading ? (
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
        ) : (
          <Icon className="h-4 w-4 mr-2" />
        )}
        {label}
      </button>
    );
  };

  return (
    <div className="space-y-6">
      {/* Camera Control */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center mb-4">
          <Camera className="h-5 w-5 text-gray-600 mr-2" />
          <h2 className="text-lg font-semibold text-gray-900">카메라 제어</h2>
        </div>
        <div className="flex space-x-3">
          <ControlButton
            onClick={() => handleCameraControl('start')}
            icon={Play}
            label="시작"
            loadingKey="camera-start"
          />
          <ControlButton
            onClick={() => handleCameraControl('pause')}
            icon={Pause}
            label="일시정지"
            loadingKey="camera-pause"
            variant="secondary"
          />
          <ControlButton
            onClick={() => handleCameraControl('stop')}
            icon={Square}
            label="정지"
            loadingKey="camera-stop"
            variant="danger"
          />
        </div>
      </div>

      {/* Microphone Control */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center mb-4">
          <Mic className="h-5 w-5 text-gray-600 mr-2" />
          <h2 className="text-lg font-semibold text-gray-900">마이크 제어</h2>
        </div>
        <div className="flex space-x-3">
          <ControlButton
            onClick={() => handleMicControl('start')}
            icon={Play}
            label="시작"
            loadingKey="mic-start"
          />
          <ControlButton
            onClick={() => handleMicControl('pause')}
            icon={Pause}
            label="일시정지"
            loadingKey="mic-pause"
            variant="secondary"
          />
          <ControlButton
            onClick={() => handleMicControl('stop')}
            icon={Square}
            label="정지"
            loadingKey="mic-stop"
            variant="danger"
          />
        </div>
      </div>

      {/* Display Control */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center mb-4">
          <Monitor className="h-5 w-5 text-gray-600 mr-2" />
          <h2 className="text-lg font-semibold text-gray-900">디스플레이 제어</h2>
        </div>
        <div className="space-y-3">
          <input
            type="text"
            value={displayText}
            onChange={(e) => setDisplayText(e.target.value)}
            placeholder="표시할 텍스트 입력..."
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            disabled={!device.is_online}
          />
          <div className="flex space-x-3">
            <ControlButton
              onClick={() => handleDisplayControl('show_text')}
              icon={Monitor}
              label="텍스트 표시"
              loadingKey="display-show_text"
            />
            <ControlButton
              onClick={() => handleDisplayControl('clear')}
              icon={Square}
              label="화면 지우기"
              loadingKey="display-clear"
              variant="secondary"
            />
          </div>
        </div>
      </div>

      {/* Info */}
      {!device.is_online && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-sm text-yellow-800">
            ⚠️ 장비가 오프라인 상태입니다. 제어 기능을 사용할 수 없습니다.
          </p>
        </div>
      )}
    </div>
  );
}

