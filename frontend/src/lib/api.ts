/**
 * API 클라이언트
 * Axios를 사용한 백엔드 API 통신
 */

import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Axios 인스턴스 생성
const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터 - 토큰 자동 추가
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    // TODO: 로그인 기능 수정 후 토큰 필수로 변경
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터 - 토큰 만료 시 자동 갱신
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    // TODO: 로그인 기능 수정 후 활성화
    // 임시: 401 오류를 무시하고 계속 진행
    if (error.response?.status === 401) {
      console.warn('인증 오류 무시 (임시):', error.message);
    }

    return Promise.reject(error);
  }
);

export default api;

// 타입 정의
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  role: 'admin' | 'operator' | 'viewer';
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_login_at: string | null;
}

export interface Device {
  id: number;
  device_id: string;
  device_name: string;
  device_type: string;
  ip_address: string | null;
  rtsp_url: string | null;
  mqtt_topic: string | null;
  is_online: boolean;
  registered_at: string;
  last_seen_at: string | null;
  location: string | null;
  description: string | null;
  status_report_interval: number;  // 상태 보고 주기 (초)
}

export interface DeviceStatus {
  id: number;
  device_id: number;
  battery_level: number | null;
  memory_usage: number | null;
  storage_usage: number | null;
  temperature: number | null;
  cpu_usage: number | null;
  camera_status: 'active' | 'paused' | 'stopped';
  mic_status: 'active' | 'paused' | 'stopped';
  recorded_at: string;
}

// API 함수들
export const authAPI = {
  login: (data: LoginRequest) =>
    api.post<LoginResponse>('/auth/login', data),
  
  logout: (refreshToken: string) =>
    api.post('/auth/logout', { refresh_token: refreshToken }),
  
  getCurrentUser: () =>
    api.get<User>('/auth/me'),
};

export interface DeviceCreateRequest {
  device_id: string;
  device_name: string;
  device_type: string;
  ip_address?: string;
  mqtt_topic?: string;
  location?: string;
  description?: string;
}

export interface DeviceUpdateRequest {
  device_name?: string;
  ip_address?: string;
  mqtt_topic?: string;
  location?: string;
  description?: string;
}

export const devicesAPI = {
  getList: (params?: { page?: number; page_size?: number; is_online?: boolean }) =>
    api.get<{ devices: Device[]; total: number; page: number; page_size: number }>('/devices/', { params }),
  
  getById: (id: number) =>
    api.get<Device>(`/devices/${id}`),
  
  create: (data: DeviceCreateRequest, config?: any) =>
    api.post<Device>('/devices/', data, config),
  
  update: (id: number, data: DeviceUpdateRequest) =>
    api.put<Device>(`/devices/${id}`, data),
  
  delete: (id: number) =>
    api.delete(`/devices/${id}`),
  
  getLatestStatus: (id: number) =>
    api.get<DeviceStatus>(`/devices/${id}/status/latest`),
  
  getStatusHistory: (id: number, limit = 10) =>
    api.get<{ statuses: DeviceStatus[]; total: number }>(`/devices/${id}/status`, {
      params: { limit },
    }),
};

export interface AudioFile {
  filename: string;
  size: number;
  uploaded_at: string;
  uploaded_by: string;
}

export const audioAPI = {
  list: () =>
    api.get<{ files: AudioFile[] }>('/audio/list'),
  
  upload: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<{ filename: string; message: string }>('/audio/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  
  delete: (filename: string) =>
    api.delete(`/audio/${filename}`),
  
  getUrl: (filename: string) =>
    `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/audio/${filename}`,
};

export const controlAPI = {
  camera: (
    deviceId: number,
    action: 'start' | 'pause' | 'stop',
    sinkUrl?: string,
    streamMode?: 'mjpeg_stills' | 'realtime_websocket' | 'realtime_rtsp',
    frameInterval?: number
  ) =>
    api.post(`/control/devices/${deviceId}/camera`, {
      action,
      sink_url: sinkUrl,
      stream_mode: streamMode,
      frame_interval: frameInterval,
    }),
  
  microphone: (deviceId: number, action: 'start' | 'pause' | 'stop' | 'start_asr' | 'stop_asr', wsUrl?: string) =>
    api.post(`/control/devices/${deviceId}/microphone`, { 
      action,
      ws_url: wsUrl
    }),
  
  speaker: (deviceId: number, action: 'play' | 'stop', audioFile?: string, volume?: number) =>
    api.post(`/control/devices/${deviceId}/speaker`, { 
      action, 
      audio_file: audioFile,
      volume: volume 
    }),
  
  playAlarm: (
    deviceId: number,
    alarmType: 'beep' | 'alert' | 'notification' | 'emergency',
    repeat: number = 1
  ) =>
    api.post(`/control/devices/${deviceId}/speaker`, {
      action: 'play_alarm',
      alarm_type: alarmType,
      repeat,
    }),
  
  playBeep: (
    deviceId: number,
    frequency: number = 1000,
    duration: number = 200,
    volume: number = 80
  ) =>
    api.post(`/control/devices/${deviceId}/speaker`, {
      action: 'play_beep',
      frequency,
      duration,
      volume,
    }),
  
  display: (deviceId: number, action: 'show_text' | 'show_emoji' | 'clear', content?: string, emojiId?: string) =>
    api.post(`/control/devices/${deviceId}/display`, { action, content, emoji_id: emojiId }),
  
  system: (deviceId: number, action: 'restart' | 'wake' | 'sleep') =>
    api.post(`/control/devices/${deviceId}/system`, { action }),
  
  setReportInterval: (deviceId: number, intervalSeconds: number) =>
    api.post(`/control/devices/${deviceId}/system`, {
      action: 'set_interval',
      interval: intervalSeconds,
    }),
};

// ASR (음성인식) 타입 정의
export interface ASRSessionStartRequest {
  language?: string;
  vad_enabled?: boolean;
}

export interface ASRSessionStartResponse {
  session_id: string;
  device_id: number;
  device_name: string;
  ws_url: string;
  status: string;
  message: string;
}

export interface ASRSessionStopRequest {
  session_id: string;
}

export interface ASRSessionStopResponse {
  session_id: string;
  device_id: number;
  status: string;
  segments_count: number;
}

export interface ASRSessionStatus {
  session_id: string;
  is_active: boolean;
  is_processing: boolean;
  segments_count: number;
  last_result: string | null;
  created_at: string;
}

export interface ASRSessionStatusResponse {
  device_id: number;
  device_name: string;
  has_active_session: boolean;
  session: ASRSessionStatus | null;
}

export interface RecognitionResult {
  type: string;
  device_id: number;
  device_name: string;
  session_id: string;
  text: string;
  timestamp: string;
  duration: number;
  is_emergency: boolean;
  emergency_keywords: string[];
}

// ASR API 함수들
export const asrAPI = {
  startSession: (deviceId: number, request: ASRSessionStartRequest) =>
    api.post<ASRSessionStartResponse>(`/asr/devices/${deviceId}/session/start`, request),
  
  stopSession: (deviceId: number, request: ASRSessionStopRequest) =>
    api.post<ASRSessionStopResponse>(`/asr/devices/${deviceId}/session/stop`, request),
  
  getSessionStatus: (deviceId: number) =>
    api.get<ASRSessionStatusResponse>(`/asr/devices/${deviceId}/session/status`),
  
  listAllSessions: () =>
    api.get<{ total: number; local_sessions: Record<number, string>; asr_server_sessions: any }>('/asr/sessions'),
  
  healthCheck: () =>
    api.get<{ status: string; asr_server?: any; error?: string }>('/asr/health'),
  
  // ASR 결과 조회
  getResults: (params?: {
    device_id?: number;
    session_id?: string;
    is_emergency?: boolean;
    text_query?: string;
    start_date?: string;
    end_date?: string;
    page?: number;
    page_size?: number;
  }) =>
    api.get<{
      total: number;
      page: number;
      page_size: number;
      results: Array<{
        id: number;
        device_id: number;
        device_name: string;
        session_id: string;
        text: string;
        timestamp: string;
        duration: number;
        is_emergency: boolean;
        emergency_keywords: string[];
        created_at: string;
      }>;
    }>('/asr/results', { params }),
  
  getResultStats: (params?: {
    device_id?: number;
    start_date?: string;
    end_date?: string;
  }) =>
    api.get<{
      total_count: number;
      emergency_count: number;
      total_duration: number;
      average_duration: number;
      device_stats: Array<{
        device_id: number;
        device_name: string;
        count: number;
        total_duration: number;
        emergency_count: number;
      }>;
    }>('/asr/results/stats', { params }),
  
  // 응급 상황 알림 조회
  getEmergencyAlerts: (params?: {
    device_id?: number;
    priority?: 'low' | 'medium' | 'high' | 'critical';
    status?: 'pending' | 'sent' | 'failed' | 'acknowledged';
    start_date?: string;
    end_date?: string;
    page?: number;
    page_size?: number;
  }) =>
    api.get<{
      total: number;
      page: number;
      page_size: number;
      alerts: Array<{
        id: number;
        device_id: number;
        device_name: string;
        asr_result_id: number | null;
        recognized_text: string;
        emergency_keywords: string[];
        priority: string;
        status: string;
        api_endpoint: string | null;
        api_response: string | null;
        sent_at: string | null;
        created_at: string;
        acknowledged_at: string | null;
        acknowledged_by: number | null;
        acknowledged_by_username: string | null;
      }>;
    }>('/asr/emergency-alerts', { params }),
  
  getEmergencyAlertStats: (params?: {
    device_id?: number;
    start_date?: string;
    end_date?: string;
  }) =>
    api.get<{
      total_count: number;
      by_priority: Record<string, number>;
      by_status: Record<string, number>;
      by_device: Array<{
        device_id: number;
        device_name: string;
        count: number;
      }>;
      recent_alerts: Array<{
        id: number;
        device_id: number;
        priority: string;
        status: string;
        created_at: string;
      }>;
    }>('/asr/emergency-alerts/stats', { params }),
  
  acknowledgeAlert: (alertId: number) =>
    api.post<{
      status: string;
      message: string;
      alert_id: number;
    }>(`/asr/emergency-alerts/${alertId}/acknowledge`),
};

