/**
 * API 클라이언트 테스트
 */
import axios from 'axios';
import api, { devicesAPI, authAPI } from '@/lib/api';

// Axios 모킹
jest.mock('axios', () => {
  const mockAxiosInstance = {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
  };
  return {
    create: jest.fn(() => mockAxiosInstance),
    ...mockAxiosInstance,
  };
});

describe('API Client', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('기본 설정', () => {
    it('API 인스턴스가 생성되어야 함', () => {
      expect(api).toBeDefined();
    });
  });
});

describe('devicesAPI', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getList', () => {
    it('장비 목록 API를 호출해야 함', async () => {
      const mockResponse = {
        data: {
          devices: [{ id: 1, device_id: 'test', device_name: 'Test' }],
          total: 1,
          page: 1,
          page_size: 10,
        },
      };

      (api.get as jest.Mock).mockResolvedValueOnce(mockResponse);

      const result = await devicesAPI.getList({ page: 1, page_size: 10 });

      expect(api.get).toHaveBeenCalledWith('/devices/', {
        params: { page: 1, page_size: 10 },
      });
      expect(result.data.devices).toHaveLength(1);
    });
  });

  describe('getById', () => {
    it('특정 장비 조회 API를 호출해야 함', async () => {
      const mockDevice = { id: 1, device_id: 'test', device_name: 'Test' };
      (api.get as jest.Mock).mockResolvedValueOnce({ data: mockDevice });

      const result = await devicesAPI.getById(1);

      expect(api.get).toHaveBeenCalledWith('/devices/1');
      expect(result.data.device_id).toBe('test');
    });
  });

  describe('create', () => {
    it('장비 생성 API를 호출해야 함', async () => {
      const newDevice = {
        device_id: 'new_device',
        device_name: 'New Device',
        device_type: 'camera',
      };
      const mockResponse = { data: { id: 1, ...newDevice } };

      (api.post as jest.Mock).mockResolvedValueOnce(mockResponse);

      const result = await devicesAPI.create(newDevice);

      expect(api.post).toHaveBeenCalledWith('/devices/', newDevice, undefined);
      expect(result.data.device_id).toBe('new_device');
    });
  });

  describe('update', () => {
    it('장비 수정 API를 호출해야 함', async () => {
      const updateData = { device_name: 'Updated Name' };
      const mockResponse = { data: { id: 1, device_name: 'Updated Name' } };

      (api.put as jest.Mock).mockResolvedValueOnce(mockResponse);

      const result = await devicesAPI.update(1, updateData);

      expect(api.put).toHaveBeenCalledWith('/devices/1', updateData);
      expect(result.data.device_name).toBe('Updated Name');
    });
  });

  describe('delete', () => {
    it('장비 삭제 API를 호출해야 함', async () => {
      (api.delete as jest.Mock).mockResolvedValueOnce({ data: null });

      await devicesAPI.delete(1);

      expect(api.delete).toHaveBeenCalledWith('/devices/1');
    });
  });
});

describe('authAPI', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('login', () => {
    it('로그인 API를 호출해야 함', async () => {
      const credentials = { username: 'testuser', password: 'testpass' };
      const mockResponse = {
        data: {
          access_token: 'access-token',
          refresh_token: 'refresh-token',
          token_type: 'bearer',
        },
      };

      (api.post as jest.Mock).mockResolvedValueOnce(mockResponse);

      const result = await authAPI.login(credentials);

      expect(api.post).toHaveBeenCalledWith('/auth/login', credentials);
      expect(result.data.access_token).toBe('access-token');
    });
  });

  describe('getCurrentUser', () => {
    it('현재 사용자 정보 API를 호출해야 함', async () => {
      const mockUser = { id: 1, username: 'testuser', email: 'test@example.com' };
      (api.get as jest.Mock).mockResolvedValueOnce({ data: mockUser });

      const result = await authAPI.getCurrentUser();

      expect(api.get).toHaveBeenCalledWith('/auth/me');
      expect(result.data.username).toBe('testuser');
    });
  });
});
