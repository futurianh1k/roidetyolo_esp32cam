'use client';

import { useState, useEffect } from 'react';
import { Device, controlAPI, audioAPI, AudioFile } from '@/lib/api';
import toast from 'react-hot-toast';
import { Camera, Mic, Volume2, Monitor, Play, Pause, Square, Upload, Trash2 } from 'lucide-react';

interface DeviceControlProps {
  device: Device;
}

export default function DeviceControl({ device }: DeviceControlProps) {
  const [isLoading, setIsLoading] = useState<string | null>(null);
  const [displayText, setDisplayText] = useState('');
  const [selectedEmoji, setSelectedEmoji] = useState('smile');
  const [audioFiles, setAudioFiles] = useState<AudioFile[]>([]);
  const [selectedAudioFile, setSelectedAudioFile] = useState<string>('');
  const [volume, setVolume] = useState<number>(70);
  const [isUploading, setIsUploading] = useState(false);

  // 오디오 파일 목록 조회
  useEffect(() => {
    loadAudioFiles();
  }, []);

  const loadAudioFiles = async () => {
    try {
      const { data } = await audioAPI.list();
      setAudioFiles(data.files || []);
      if (data.files && data.files.length > 0 && !selectedAudioFile) {
        setSelectedAudioFile(data.files[0].filename);
      }
    } catch (error) {
      console.error('오디오 파일 목록 조회 실패:', error);
    }
  };

  const handleAudioUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // 파일 형식 확인
    const allowedTypes = ['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/ogg'];
    if (!allowedTypes.includes(file.type) && !file.name.match(/\.(mp3|wav|ogg)$/i)) {
      toast.error('지원하는 형식: MP3, WAV, OGG');
      return;
    }

    // 파일 크기 확인 (10MB)
    if (file.size > 10 * 1024 * 1024) {
      toast.error('파일 크기는 10MB 이하여야 합니다');
      return;
    }

    setIsUploading(true);
    try {
      const { data } = await audioAPI.upload(file);
      toast.success(`"${data.filename}" 업로드 완료`);
      loadAudioFiles(); // 목록 새로고침
      setSelectedAudioFile(data.filename);
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '파일 업로드에 실패했습니다';
      toast.error(errorMessage);
    } finally {
      setIsUploading(false);
      // 파일 입력 초기화
      e.target.value = '';
    }
  };

  const handleSpeakerControl = async (action: 'play' | 'stop') => {
    if (!device.is_online) {
      toast.error('장비가 오프라인 상태입니다');
      return;
    }

    if (action === 'play' && !selectedAudioFile) {
      toast.error('재생할 오디오 파일을 선택하세요');
      return;
    }

    setIsLoading(`speaker-${action}`);
    try {
      await controlAPI.speaker(device.id, action, selectedAudioFile, volume);
      toast.success(action === 'play' ? '오디오 재생 명령 전송' : '오디오 정지 명령 전송');
    } catch (error) {
      toast.error('스피커 제어 실패');
    } finally {
      setIsLoading(null);
    }
  };

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

  const handleDisplayControl = async (action: 'show_text' | 'show_emoji' | 'clear') => {
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
      if (action === 'show_emoji') {
        await controlAPI.display(device.id, action, undefined, selectedEmoji);
        toast.success('이모티콘 표시 명령 전송');
      } else {
        await controlAPI.display(device.id, action, displayText);
        toast.success(action === 'show_text' ? '텍스트 표시 명령 전송' : '화면 지우기 명령 전송');
        if (action === 'clear') {
          setDisplayText('');
        }
      }
    } catch (error) {
      toast.error('디스플레이 제어 실패');
    } finally {
      setIsLoading(null);
    }
  };

  // 이모티콘 목록
  const emojis = [
    { id: 'smile', label: '😊 웃음', icon: '😊' },
    { id: 'heart', label: '❤️ 하트', icon: '❤️' },
    { id: 'thumbs_up', label: '👍 좋아요', icon: '👍' },
    { id: 'check', label: '✅ 체크', icon: '✅' },
    { id: 'warning', label: '⚠️ 경고', icon: '⚠️' },
    { id: 'fire', label: '🔥 불', icon: '🔥' },
    { id: 'star', label: '⭐ 별', icon: '⭐' },
    { id: 'moon', label: '🌙 달', icon: '🌙' },
  ];

  type VariantType = 'default' | 'secondary' | 'danger';
  
  const ControlButton = ({ 
    onClick, 
    icon: Icon, 
    label, 
    loadingKey, 
    variant = 'default' as VariantType
  }: {
    onClick: () => void;
    icon: any;
    label: string;
    loadingKey: string;
    variant?: VariantType;
  }) => {
    const isButtonLoading = isLoading === loadingKey;
    const baseClasses = 'inline-flex items-center justify-center px-4 py-2 rounded-lg text-sm font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed';
    const variantClasses: Record<VariantType, string> = {
      default: 'bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500',
      secondary: 'bg-gray-200 text-gray-800 hover:bg-gray-300 focus:ring-gray-500',
      danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
    };

    return (
      <button
        onClick={onClick}
        disabled={!device.is_online || isButtonLoading}
        className={`${baseClasses} ${variantClasses[variant as VariantType]}`}
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

      {/* Speaker Control */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center mb-4">
          <Volume2 className="h-5 w-5 text-gray-600 mr-2" />
          <h2 className="text-lg font-semibold text-gray-900">스피커 제어</h2>
        </div>
        <div className="space-y-4">
          {/* 오디오 파일 업로드 */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">오디오 파일 업로드</label>
            <div className="flex items-center space-x-2">
              <label className="flex-1 cursor-pointer">
                <div className="flex items-center justify-center px-4 py-2 border-2 border-dashed border-gray-300 rounded-lg hover:border-primary-400 transition-colors">
                  <Upload className="h-4 w-4 mr-2 text-gray-600" />
                  <span className="text-sm text-gray-600">
                    {isUploading ? '업로드 중...' : '파일 선택 (MP3, WAV, OGG)'}
                  </span>
                </div>
                <input
                  type="file"
                  accept=".mp3,.wav,.ogg,audio/mpeg,audio/wav,audio/ogg"
                  onChange={handleAudioUpload}
                  className="hidden"
                  disabled={!device.is_online || isUploading}
                />
              </label>
            </div>
            <p className="text-xs text-gray-500">최대 10MB, MP3/WAV/OGG 형식</p>
          </div>

          {/* 오디오 파일 선택 */}
          {audioFiles.length > 0 && (
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">재생할 파일</label>
              <select
                value={selectedAudioFile}
                onChange={(e) => setSelectedAudioFile(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                disabled={!device.is_online}
              >
                {audioFiles.map((file) => (
                  <option key={file.filename} value={file.filename}>
                    {file.filename} ({(file.size / 1024).toFixed(1)} KB)
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* 볼륨 조절 */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              볼륨: {volume}%
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={volume}
              onChange={(e) => setVolume(Number(e.target.value))}
              className="w-full"
              disabled={!device.is_online}
            />
          </div>

          {/* 재생 버튼 */}
          <div className="flex space-x-3">
            <ControlButton
              onClick={() => handleSpeakerControl('play')}
              icon={Play}
              label="재생"
              loadingKey="speaker-play"
            />
            <ControlButton
              onClick={() => handleSpeakerControl('stop')}
              icon={Square}
              label="정지"
              loadingKey="speaker-stop"
              variant="danger"
            />
          </div>
        </div>
      </div>

      {/* Display Control */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center mb-4">
          <Monitor className="h-5 w-5 text-gray-600 mr-2" />
          <h2 className="text-lg font-semibold text-gray-900">디스플레이 제어</h2>
        </div>
        <div className="space-y-4">
          {/* 텍스트 표시 */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">텍스트 표시</label>
            <input
              type="text"
              value={displayText}
              onChange={(e) => setDisplayText(e.target.value)}
              placeholder="표시할 텍스트 입력..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              disabled={!device.is_online}
            />
            <ControlButton
              onClick={() => handleDisplayControl('show_text')}
              icon={Monitor}
              label="텍스트 표시"
              loadingKey="display-show_text"
            />
          </div>

          {/* 이모티콘 표시 */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">이모티콘 표시</label>
            <div className="grid grid-cols-4 gap-2">
              {emojis.map((emoji) => (
                <button
                  key={emoji.id}
                  onClick={() => setSelectedEmoji(emoji.id)}
                  className={`p-3 border-2 rounded-lg text-2xl text-center transition-all hover:scale-110 ${
                    selectedEmoji === emoji.id
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-primary-300'
                  }`}
                  disabled={!device.is_online}
                  title={emoji.label}
                >
                  {emoji.icon}
                </button>
              ))}
            </div>
            <ControlButton
              onClick={() => handleDisplayControl('show_emoji')}
              icon={Monitor}
              label="이모티콘 표시"
              loadingKey="display-show_emoji"
            />
          </div>

          {/* 화면 지우기 */}
          <div className="pt-2 border-t border-gray-200">
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

