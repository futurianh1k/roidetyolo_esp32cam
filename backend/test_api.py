"""
API 테스트 스크립트
백엔드 인증 시스템 테스트
"""
import sys
import requests
from pathlib import Path

# API 기본 URL
BASE_URL = "http://localhost:8000"


def test_health_check():
    """헬스 체크 테스트"""
    print("\n[1] 헬스 체크 테스트...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print(f"✅ 성공: {response.json()}")
            return True
        else:
            print(f"❌ 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 오류: {e}")
        return False


def test_register():
    """사용자 등록 테스트"""
    print("\n[2] 사용자 등록 테스트...")
    try:
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPass123!",
            "role": "viewer"
        }
        response = requests.post(f"{BASE_URL}/auth/register", json=data)
        if response.status_code == 201:
            print(f"✅ 성공: {response.json()['username']} 등록됨")
            return True
        elif response.status_code == 400:
            print(f"⚠️  이미 존재하는 사용자입니다")
            return True
        else:
            print(f"❌ 실패: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 오류: {e}")
        return False


def test_login():
    """로그인 테스트"""
    print("\n[3] 로그인 테스트...")
    try:
        data = {
            "username": "admin",
            "password": "Admin123!"
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=data)
        if response.status_code == 200:
            tokens = response.json()
            print(f"✅ 성공: Access Token 발급됨")
            return tokens
        else:
            print(f"❌ 실패: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 오류: {e}")
        return None


def test_get_current_user(access_token):
    """현재 사용자 정보 조회 테스트"""
    print("\n[4] 현재 사용자 정보 조회 테스트...")
    try:
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        if response.status_code == 200:
            user = response.json()
            print(f"✅ 성공: {user['username']} ({user['role']})")
            return True
        else:
            print(f"❌ 실패: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 오류: {e}")
        return False


def test_refresh_token(refresh_token):
    """토큰 갱신 테스트"""
    print("\n[5] 토큰 갱신 테스트...")
    try:
        data = {
            "refresh_token": refresh_token
        }
        response = requests.post(f"{BASE_URL}/auth/refresh", json=data)
        if response.status_code == 200:
            print(f"✅ 성공: 새 토큰 발급됨")
            return True
        else:
            print(f"❌ 실패: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 오류: {e}")
        return False


def run_tests():
    """전체 테스트 실행"""
    print("=" * 60)
    print("Core S3 Management System - API 테스트")
    print("=" * 60)
    
    results = []
    
    # 1. 헬스 체크
    results.append(test_health_check())
    
    # 2. 사용자 등록
    results.append(test_register())
    
    # 3. 로그인
    tokens = test_login()
    if tokens:
        results.append(True)
        
        # 4. 현재 사용자 정보
        results.append(test_get_current_user(tokens["access_token"]))
        
        # 5. 토큰 갱신
        results.append(test_refresh_token(tokens["refresh_token"]))
    else:
        results.append(False)
        results.append(False)
        results.append(False)
    
    # 결과 요약
    print("\n" + "=" * 60)
    print(f"테스트 결과: {sum(results)}/{len(results)} 성공")
    print("=" * 60)
    
    return all(results)


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

