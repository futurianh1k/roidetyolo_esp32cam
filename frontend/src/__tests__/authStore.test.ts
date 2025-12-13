/**
 * Auth Store 테스트
 */
import { act, renderHook } from '@testing-library/react';
import { useAuthStore } from '@/store/authStore';

describe('useAuthStore', () => {
  // 각 테스트 전에 스토어 초기화
  beforeEach(() => {
    const { result } = renderHook(() => useAuthStore());
    act(() => {
      result.current.clearAuth();
    });
    localStorage.clear();
  });

  describe('초기 상태', () => {
    it('초기 상태는 비인증 상태여야 함', () => {
      const { result } = renderHook(() => useAuthStore());

      expect(result.current.user).toBeNull();
      expect(result.current.accessToken).toBeNull();
      expect(result.current.refreshToken).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });
  });

  describe('setAuth', () => {
    it('인증 정보 설정 시 상태가 업데이트되어야 함', () => {
      const { result } = renderHook(() => useAuthStore());

      const mockUser = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        role: 'operator' as const,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        last_login_at: null,
      };

      act(() => {
        result.current.setAuth(mockUser, 'access-token', 'refresh-token');
      });

      expect(result.current.user).toEqual(mockUser);
      expect(result.current.accessToken).toBe('access-token');
      expect(result.current.refreshToken).toBe('refresh-token');
      expect(result.current.isAuthenticated).toBe(true);
    });

    it('토큰이 localStorage에 저장되어야 함', () => {
      const { result } = renderHook(() => useAuthStore());

      const mockUser = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        role: 'viewer' as const,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        last_login_at: null,
      };

      act(() => {
        result.current.setAuth(mockUser, 'my-access', 'my-refresh');
      });

      expect(localStorage.setItem).toHaveBeenCalledWith('access_token', 'my-access');
      expect(localStorage.setItem).toHaveBeenCalledWith('refresh_token', 'my-refresh');
    });
  });

  describe('clearAuth', () => {
    it('인증 정보 삭제 시 상태가 초기화되어야 함', () => {
      const { result } = renderHook(() => useAuthStore());

      // 먼저 인증 설정
      const mockUser = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        role: 'admin' as const,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        last_login_at: null,
      };

      act(() => {
        result.current.setAuth(mockUser, 'token', 'refresh');
      });

      // 인증 삭제
      act(() => {
        result.current.clearAuth();
      });

      expect(result.current.user).toBeNull();
      expect(result.current.accessToken).toBeNull();
      expect(result.current.refreshToken).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });

    it('localStorage에서 토큰이 삭제되어야 함', () => {
      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.clearAuth();
      });

      expect(localStorage.removeItem).toHaveBeenCalledWith('access_token');
      expect(localStorage.removeItem).toHaveBeenCalledWith('refresh_token');
    });
  });

  describe('setUser', () => {
    it('사용자 정보만 업데이트되어야 함', () => {
      const { result } = renderHook(() => useAuthStore());

      const mockUser = {
        id: 2,
        username: 'updateduser',
        email: 'updated@example.com',
        role: 'operator' as const,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
        last_login_at: '2024-01-02T00:00:00Z',
      };

      act(() => {
        result.current.setUser(mockUser);
      });

      expect(result.current.user).toEqual(mockUser);
    });
  });
});
