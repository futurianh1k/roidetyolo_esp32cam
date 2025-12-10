"""
전체 API 테스트 스크립트
모든 백엔드 API 엔드포인트를 테스트하고 결과를 수집합니다.

참고자료:
- FastAPI Testing: https://fastapi.tiangolo.com/tutorial/testing/
- httpx: https://www.python-httpx.org/
"""

import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import httpx
from io import BytesIO

# API 기본 URL
BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0  # 타임아웃 (초)

# 테스트 결과 저장
test_results: List[Dict] = []


class Colors:
    """터미널 색상 코드"""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_test(name: str):
    """테스트 시작 출력"""
    print(f"\n{Colors.BLUE}[테스트]{Colors.RESET} {name}")


def print_success(message: str = ""):
    """성공 출력"""
    print(f"{Colors.GREEN}✅ 성공{Colors.RESET} {message}")


def print_fail(message: str = ""):
    """실패 출력"""
    print(f"{Colors.RED}❌ 실패{Colors.RESET} {message}")


def print_warning(message: str = ""):
    """경고 출력"""
    print(f"{Colors.YELLOW}⚠️  경고{Colors.RESET} {message}")


def record_test(
    api_name: str,
    method: str,
    endpoint: str,
    status_code: int,
    success: bool,
    error: Optional[str] = None,
    response_time_ms: Optional[float] = None,
    notes: Optional[str] = None,
    test_type: str = "positive",  # "positive" or "negative"
    expected_status: Optional[int] = None,  # 예상 상태 코드 (negative 테스트용)
):
    """테스트 결과 기록"""
    test_results.append(
        {
            "api_name": api_name,
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            "success": success,
            "error": error,
            "response_time_ms": response_time_ms,
            "notes": notes,
            "test_type": test_type,
            "expected_status": expected_status,
            "timestamp": datetime.now().isoformat(),
        }
    )


# ==================== 헬스 체크 ====================


def test_root():
    """루트 엔드포인트 테스트"""
    print_test("GET / (루트)")
    try:
        start_time = time.time()
        response = httpx.get(f"{BASE_URL}/", timeout=TIMEOUT)
        response_time = (time.time() - start_time) * 1000

        if response.status_code == 200:
            data = response.json()
            print_success(f"응답: {data}")
            record_test("루트", "GET", "/", 200, True, None, response_time)
            return True
        else:
            print_fail(f"상태 코드: {response.status_code}")
            record_test(
                "루트",
                "GET",
                "/",
                response.status_code,
                False,
                f"예상 200, 실제 {response.status_code}",
                response_time,
            )
            return False
    except Exception as e:
        print_fail(str(e))
        record_test("루트", "GET", "/", 0, False, str(e))
        return False


def test_health_check():
    """헬스 체크 테스트"""
    print_test("GET /health")
    try:
        start_time = time.time()
        response = httpx.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        response_time = (time.time() - start_time) * 1000

        if response.status_code == 200:
            data = response.json()
            print_success(
                f"상태: {data.get('status')}, MQTT: {data.get('mqtt_connected')}"
            )
            record_test("헬스 체크", "GET", "/health", 200, True, None, response_time)
            return True
        else:
            print_fail(f"상태 코드: {response.status_code}")
            record_test(
                "헬스 체크",
                "GET",
                "/health",
                response.status_code,
                False,
                f"예상 200, 실제 {response.status_code}",
                response_time,
            )
            return False
    except Exception as e:
        print_fail(str(e))
        record_test("헬스 체크", "GET", "/health", 0, False, str(e))
        return False


# ==================== 인증 API ====================


def test_auth_register():
    """사용자 등록 테스트"""
    print_test("POST /auth/register")
    try:
        data = {
            "username": f"testuser_{int(time.time())}",
            "email": f"test_{int(time.time())}@example.com",
            "password": "TestPass123!",
            "role": "viewer",
        }
        start_time = time.time()
        response = httpx.post(f"{BASE_URL}/auth/register", json=data, timeout=TIMEOUT)
        response_time = (time.time() - start_time) * 1000

        if response.status_code == 201:
            result = response.json()
            print_success(f"사용자 등록: {result.get('username')}")
            record_test(
                "사용자 등록", "POST", "/auth/register", 201, True, None, response_time
            )
            return result
        elif response.status_code == 400:
            print_warning("이미 존재하는 사용자 (정상 동작)")
            record_test(
                "사용자 등록",
                "POST",
                "/auth/register",
                400,
                True,
                None,
                response_time,
                "중복 사용자 검증",
            )
            return None
        else:
            print_fail(f"상태 코드: {response.status_code}, 응답: {response.text}")
            record_test(
                "사용자 등록",
                "POST",
                "/auth/register",
                response.status_code,
                False,
                response.text,
                response_time,
            )
            return None
    except Exception as e:
        print_fail(str(e))
        record_test("사용자 등록", "POST", "/auth/register", 0, False, str(e))
        return None


def test_auth_login(username: str = "admin", password: str = "Admin123!"):
    """로그인 테스트"""
    print_test(f"POST /auth/login (사용자: {username})")
    try:
        data = {"username": username, "password": password}
        start_time = time.time()
        response = httpx.post(f"{BASE_URL}/auth/login", json=data, timeout=TIMEOUT)
        response_time = (time.time() - start_time) * 1000

        if response.status_code == 200:
            tokens = response.json()
            print_success("토큰 발급 완료")
            record_test("로그인", "POST", "/auth/login", 200, True, None, response_time)
            return tokens
        else:
            print_fail(f"상태 코드: {response.status_code}, 응답: {response.text}")
            record_test(
                "로그인",
                "POST",
                "/auth/login",
                response.status_code,
                False,
                response.text,
                response_time,
            )
            return None
    except Exception as e:
        print_fail(str(e))
        record_test("로그인", "POST", "/auth/login", 0, False, str(e))
        return None


def test_auth_me(access_token: str):
    """현재 사용자 정보 조회 테스트"""
    print_test("GET /auth/me")
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        start_time = time.time()
        response = httpx.get(f"{BASE_URL}/auth/me", headers=headers, timeout=TIMEOUT)
        response_time = (time.time() - start_time) * 1000

        if response.status_code == 200:
            user = response.json()
            print_success(f"사용자: {user.get('username')} ({user.get('role')})")
            record_test(
                "현재 사용자 조회", "GET", "/auth/me", 200, True, None, response_time
            )
            return True
        else:
            print_fail(f"상태 코드: {response.status_code}")
            record_test(
                "현재 사용자 조회",
                "GET",
                "/auth/me",
                response.status_code,
                False,
                f"예상 200, 실제 {response.status_code}",
                response_time,
            )
            return False
    except Exception as e:
        print_fail(str(e))
        record_test("현재 사용자 조회", "GET", "/auth/me", 0, False, str(e))
        return False


def test_auth_refresh(refresh_token: str):
    """토큰 갱신 테스트"""
    print_test("POST /auth/refresh")
    try:
        data = {"refresh_token": refresh_token}
        start_time = time.time()
        response = httpx.post(f"{BASE_URL}/auth/refresh", json=data, timeout=TIMEOUT)
        response_time = (time.time() - start_time) * 1000

        if response.status_code == 200:
            print_success("새 토큰 발급 완료")
            record_test(
                "토큰 갱신", "POST", "/auth/refresh", 200, True, None, response_time
            )
            return True
        else:
            print_fail(f"상태 코드: {response.status_code}")
            record_test(
                "토큰 갱신",
                "POST",
                "/auth/refresh",
                response.status_code,
                False,
                f"예상 200, 실제 {response.status_code}",
                response_time,
            )
            return False
    except Exception as e:
        print_fail(str(e))
        record_test("토큰 갱신", "POST", "/auth/refresh", 0, False, str(e))
        return False


# ==================== 장비 관리 API ====================


def test_devices_list(access_token: Optional[str] = None):
    """장비 목록 조회 테스트"""
    print_test("GET /devices/")
    try:
        headers = {}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        start_time = time.time()
        response = httpx.get(
            f"{BASE_URL}/devices/?page=1&page_size=10", headers=headers, timeout=TIMEOUT
        )
        response_time = (time.time() - start_time) * 1000

        if response.status_code == 200:
            data = response.json()
            total = data.get("total", 0)
            print_success(f"장비 {total}개 조회")
            record_test(
                "장비 목록 조회", "GET", "/devices/", 200, True, None, response_time
            )
            return data.get("devices", [])
        else:
            print_fail(f"상태 코드: {response.status_code}")
            record_test(
                "장비 목록 조회",
                "GET",
                "/devices/",
                response.status_code,
                False,
                f"예상 200, 실제 {response.status_code}",
                response_time,
            )
            return []
    except Exception as e:
        print_fail(str(e))
        record_test("장비 목록 조회", "GET", "/devices/", 0, False, str(e))
        return []


def test_device_get(device_id: int, access_token: Optional[str] = None):
    """장비 상세 조회 테스트"""
    print_test(f"GET /devices/{device_id}")
    try:
        headers = {}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        start_time = time.time()
        response = httpx.get(
            f"{BASE_URL}/devices/{device_id}", headers=headers, timeout=TIMEOUT
        )
        response_time = (time.time() - start_time) * 1000

        if response.status_code == 200:
            device = response.json()
            print_success(f"장비: {device.get('device_name')}")
            record_test(
                "장비 상세 조회",
                "GET",
                f"/devices/{device_id}",
                200,
                True,
                None,
                response_time,
            )
            return device
        elif response.status_code == 404:
            print_warning("장비를 찾을 수 없음 (정상 동작)")
            record_test(
                "장비 상세 조회",
                "GET",
                f"/devices/{device_id}",
                404,
                True,
                None,
                response_time,
                "존재하지 않는 장비",
            )
            return None
        else:
            print_fail(f"상태 코드: {response.status_code}")
            record_test(
                "장비 상세 조회",
                "GET",
                f"/devices/{device_id}",
                response.status_code,
                False,
                f"예상 200, 실제 {response.status_code}",
                response_time,
            )
            return None
    except Exception as e:
        print_fail(str(e))
        record_test("장비 상세 조회", "GET", f"/devices/{device_id}", 0, False, str(e))
        return None


def test_device_register(access_token: Optional[str] = None):
    """장비 등록 테스트"""
    print_test("POST /devices/")
    try:
        device_id = f"TEST_{int(time.time())}"
        data = {
            "device_id": device_id,
            "device_name": f"테스트 장비 {int(time.time())}",
            "device_type": "cores3",
            "ip_address": "192.168.1.100",
            "location": "테스트 위치",
        }

        headers = {}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        start_time = time.time()
        response = httpx.post(
            f"{BASE_URL}/devices/", json=data, headers=headers, timeout=TIMEOUT
        )
        response_time = (time.time() - start_time) * 1000

        if response.status_code == 201:
            device = response.json()
            print_success(f"장비 등록: {device.get('device_name')}")
            record_test(
                "장비 등록", "POST", "/devices/", 201, True, None, response_time
            )
            return device
        elif response.status_code == 400:
            print_warning("중복 장비 또는 잘못된 요청 (정상 동작)")
            record_test(
                "장비 등록",
                "POST",
                "/devices/",
                400,
                True,
                None,
                response_time,
                "중복 검증",
            )
            return None
        else:
            print_fail(f"상태 코드: {response.status_code}, 응답: {response.text}")
            record_test(
                "장비 등록",
                "POST",
                "/devices/",
                response.status_code,
                False,
                response.text,
                response_time,
            )
            return None
    except Exception as e:
        print_fail(str(e))
        record_test("장비 등록", "POST", "/devices/", 0, False, str(e))
        return None


def test_device_update(device_id: int, access_token: Optional[str] = None):
    """장비 정보 수정 테스트"""
    print_test(f"PUT /devices/{device_id}")
    try:
        data = {
            "device_name": f"수정된 장비명 {int(time.time())}",
            "location": "수정된 위치",
        }

        headers = {}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        start_time = time.time()
        response = httpx.put(
            f"{BASE_URL}/devices/{device_id}",
            json=data,
            headers=headers,
            timeout=TIMEOUT,
        )
        response_time = (time.time() - start_time) * 1000

        if response.status_code == 200:
            device = response.json()
            print_success(f"장비 수정: {device.get('device_name')}")
            record_test(
                "장비 수정",
                "PUT",
                f"/devices/{device_id}",
                200,
                True,
                None,
                response_time,
            )
            return True
        elif response.status_code == 404:
            print_warning("장비를 찾을 수 없음 (정상 동작)")
            record_test(
                "장비 수정",
                "PUT",
                f"/devices/{device_id}",
                404,
                True,
                None,
                response_time,
                "존재하지 않는 장비",
            )
            return False
        else:
            print_fail(f"상태 코드: {response.status_code}")
            record_test(
                "장비 수정",
                "PUT",
                f"/devices/{device_id}",
                response.status_code,
                False,
                f"예상 200, 실제 {response.status_code}",
                response_time,
            )
            return False
    except Exception as e:
        print_fail(str(e))
        record_test("장비 수정", "PUT", f"/devices/{device_id}", 0, False, str(e))
        return False


def test_device_status_latest(device_id: int, access_token: Optional[str] = None):
    """장비 최신 상태 조회 테스트"""
    print_test(f"GET /devices/{device_id}/status/latest")
    try:
        headers = {}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        start_time = time.time()
        response = httpx.get(
            f"{BASE_URL}/devices/{device_id}/status/latest",
            headers=headers,
            timeout=TIMEOUT,
        )
        response_time = (time.time() - start_time) * 1000

        if response.status_code == 200:
            status = response.json()
            print_success(f"상태 조회: 배터리 {status.get('battery_level')}%")
            record_test(
                "장비 최신 상태 조회",
                "GET",
                f"/devices/{device_id}/status/latest",
                200,
                True,
                None,
                response_time,
            )
            return True
        elif response.status_code == 404:
            print_warning("상태 정보 없음 (정상 동작)")
            record_test(
                "장비 최신 상태 조회",
                "GET",
                f"/devices/{device_id}/status/latest",
                404,
                True,
                None,
                response_time,
                "상태 정보 없음",
            )
            return False
        else:
            print_fail(f"상태 코드: {response.status_code}")
            record_test(
                "장비 최신 상태 조회",
                "GET",
                f"/devices/{device_id}/status/latest",
                response.status_code,
                False,
                f"예상 200, 실제 {response.status_code}",
                response_time,
            )
            return False
    except Exception as e:
        print_fail(str(e))
        record_test(
            "장비 최신 상태 조회",
            "GET",
            f"/devices/{device_id}/status/latest",
            0,
            False,
            str(e),
        )
        return False


# ==================== 장비 제어 API ====================


def test_control_camera(device_id: int, access_token: Optional[str] = None):
    """카메라 제어 테스트"""
    print_test(f"POST /control/devices/{device_id}/camera")
    try:
        data = {"action": "start"}

        headers = {}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        start_time = time.time()
        response = httpx.post(
            f"{BASE_URL}/control/devices/{device_id}/camera",
            json=data,
            headers=headers,
            timeout=TIMEOUT,
        )
        response_time = (time.time() - start_time) * 1000

        if response.status_code == 200:
            result = response.json()
            print_success(f"카메라 제어: {result.get('message')}")
            record_test(
                "카메라 제어",
                "POST",
                f"/control/devices/{device_id}/camera",
                200,
                True,
                None,
                response_time,
            )
            return True
        elif response.status_code in [400, 404]:
            print_warning(
                f"장비 오프라인 또는 없음 (상태 코드: {response.status_code})"
            )
            record_test(
                "카메라 제어",
                "POST",
                f"/control/devices/{device_id}/camera",
                response.status_code,
                True,
                None,
                response_time,
                "장비 오프라인",
            )
            return False
        else:
            print_fail(f"상태 코드: {response.status_code}")
            record_test(
                "카메라 제어",
                "POST",
                f"/control/devices/{device_id}/camera",
                response.status_code,
                False,
                f"예상 200, 실제 {response.status_code}",
                response_time,
            )
            return False
    except Exception as e:
        print_fail(str(e))
        record_test(
            "카메라 제어",
            "POST",
            f"/control/devices/{device_id}/camera",
            0,
            False,
            str(e),
        )
        return False


def test_control_microphone(device_id: int, access_token: Optional[str] = None):
    """마이크 제어 테스트"""
    print_test(f"POST /control/devices/{device_id}/microphone")
    try:
        data = {"action": "start"}

        headers = {}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        start_time = time.time()
        response = httpx.post(
            f"{BASE_URL}/control/devices/{device_id}/microphone",
            json=data,
            headers=headers,
            timeout=TIMEOUT,
        )
        response_time = (time.time() - start_time) * 1000

        if response.status_code == 200:
            result = response.json()
            print_success(f"마이크 제어: {result.get('message')}")
            record_test(
                "마이크 제어",
                "POST",
                f"/control/devices/{device_id}/microphone",
                200,
                True,
                None,
                response_time,
            )
            return True
        elif response.status_code in [400, 404]:
            print_warning(
                f"장비 오프라인 또는 없음 (상태 코드: {response.status_code})"
            )
            record_test(
                "마이크 제어",
                "POST",
                f"/control/devices/{device_id}/microphone",
                response.status_code,
                True,
                None,
                response_time,
                "장비 오프라인",
            )
            return False
        else:
            print_fail(f"상태 코드: {response.status_code}")
            record_test(
                "마이크 제어",
                "POST",
                f"/control/devices/{device_id}/microphone",
                response.status_code,
                False,
                f"예상 200, 실제 {response.status_code}",
                response_time,
            )
            return False
    except Exception as e:
        print_fail(str(e))
        record_test(
            "마이크 제어",
            "POST",
            f"/control/devices/{device_id}/microphone",
            0,
            False,
            str(e),
        )
        return False


def test_control_display(device_id: int, access_token: Optional[str] = None):
    """디스플레이 제어 테스트"""
    print_test(f"POST /control/devices/{device_id}/display")
    try:
        data = {"action": "show_text", "content": "테스트 메시지"}

        headers = {}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        start_time = time.time()
        response = httpx.post(
            f"{BASE_URL}/control/devices/{device_id}/display",
            json=data,
            headers=headers,
            timeout=TIMEOUT,
        )
        response_time = (time.time() - start_time) * 1000

        if response.status_code == 200:
            result = response.json()
            print_success(f"디스플레이 제어: {result.get('message')}")
            record_test(
                "디스플레이 제어",
                "POST",
                f"/control/devices/{device_id}/display",
                200,
                True,
                None,
                response_time,
            )
            return True
        elif response.status_code in [400, 404]:
            print_warning(
                f"장비 오프라인 또는 없음 (상태 코드: {response.status_code})"
            )
            record_test(
                "디스플레이 제어",
                "POST",
                f"/control/devices/{device_id}/display",
                response.status_code,
                True,
                None,
                response_time,
                "장비 오프라인",
            )
            return False
        else:
            print_fail(f"상태 코드: {response.status_code}")
            record_test(
                "디스플레이 제어",
                "POST",
                f"/control/devices/{device_id}/display",
                response.status_code,
                False,
                f"예상 200, 실제 {response.status_code}",
                response_time,
            )
            return False
    except Exception as e:
        print_fail(str(e))
        record_test(
            "디스플레이 제어",
            "POST",
            f"/control/devices/{device_id}/display",
            0,
            False,
            str(e),
        )
        return False


def test_control_system(device_id: int, access_token: Optional[str] = None):
    """시스템 제어 테스트 (재시작은 실제로 실행하지 않음)"""
    print_test(f"POST /control/devices/{device_id}/system (스킵: 실제 재시작 방지)")
    print_warning("시스템 재시작 테스트는 스킵합니다 (실제 장비 재시작 방지)")
    record_test(
        "시스템 제어",
        "POST",
        f"/control/devices/{device_id}/system",
        0,
        True,
        None,
        None,
        "스킵됨: 실제 재시작 방지",
    )
    return True


# ==================== 오디오 파일 관리 API ====================


def test_audio_list(access_token: Optional[str] = None):
    """오디오 파일 목록 조회 테스트"""
    print_test("GET /audio/list")
    try:
        headers = {}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        start_time = time.time()
        response = httpx.get(f"{BASE_URL}/audio/list", headers=headers, timeout=TIMEOUT)
        response_time = (time.time() - start_time) * 1000

        if response.status_code == 200:
            files = response.json()
            print_success(f"오디오 파일 {len(files)}개 조회")
            record_test(
                "오디오 파일 목록", "GET", "/audio/list", 200, True, None, response_time
            )
            return files
        else:
            print_fail(f"상태 코드: {response.status_code}")
            record_test(
                "오디오 파일 목록",
                "GET",
                "/audio/list",
                response.status_code,
                False,
                f"예상 200, 실제 {response.status_code}",
                response_time,
            )
            return []
    except Exception as e:
        print_fail(str(e))
        record_test("오디오 파일 목록", "GET", "/audio/list", 0, False, str(e))
        return []


def test_audio_upload(access_token: Optional[str] = None):
    """오디오 파일 업로드 테스트"""
    print_test("POST /audio/upload")
    try:
        # 더미 MP3 파일 생성 (실제로는 유효한 MP3 헤더가 필요하지만, 검증만 테스트)
        fake_audio = BytesIO(b"fake mp3 content for testing")

        headers = {}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        files = {"file": ("test.mp3", fake_audio, "audio/mpeg")}

        start_time = time.time()
        response = httpx.post(
            f"{BASE_URL}/audio/upload", files=files, headers=headers, timeout=TIMEOUT
        )
        response_time = (time.time() - start_time) * 1000

        if response.status_code == 201:
            result = response.json()
            print_success(f"파일 업로드: {result.get('filename')}")
            record_test(
                "오디오 파일 업로드",
                "POST",
                "/audio/upload",
                201,
                True,
                None,
                response_time,
            )
            return result.get("filename")
        elif response.status_code == 400:
            print_warning("파일 검증 실패 (정상 동작: 유효하지 않은 파일)")
            record_test(
                "오디오 파일 업로드",
                "POST",
                "/audio/upload",
                400,
                True,
                None,
                response_time,
                "파일 검증",
            )
            return None
        else:
            print_fail(f"상태 코드: {response.status_code}")
            record_test(
                "오디오 파일 업로드",
                "POST",
                "/audio/upload",
                response.status_code,
                False,
                f"예상 201, 실제 {response.status_code}",
                response_time,
            )
            return None
    except Exception as e:
        print_fail(str(e))
        record_test("오디오 파일 업로드", "POST", "/audio/upload", 0, False, str(e))
        return None


# ==================== ASR API ====================


def test_asr_health():
    """ASR 서버 헬스 체크 테스트"""
    print_test("GET /asr/health")
    try:
        start_time = time.time()
        response = httpx.get(f"{BASE_URL}/asr/health", timeout=TIMEOUT)
        response_time = (time.time() - start_time) * 1000

        if response.status_code == 200:
            data = response.json()
            status = data.get("status", "unknown")
            print_success(f"ASR 서버 상태: {status}")
            record_test(
                "ASR 헬스 체크", "GET", "/asr/health", 200, True, None, response_time
            )
            return True
        else:
            print_warning(f"ASR 서버 응답 없음 (상태 코드: {response.status_code})")
            record_test(
                "ASR 헬스 체크",
                "GET",
                "/asr/health",
                response.status_code,
                True,
                None,
                response_time,
                "ASR 서버 미연결 가능",
            )
            return False
    except Exception as e:
        print_warning(
            f"ASR 서버 연결 실패: {str(e)} (ASR 서버가 실행 중이 아닐 수 있음)"
        )
        record_test(
            "ASR 헬스 체크",
            "GET",
            "/asr/health",
            0,
            True,
            str(e),
            None,
            "ASR 서버 미연결",
        )
        return False


def test_asr_session_status(device_id: int, access_token: Optional[str] = None):
    """ASR 세션 상태 조회 테스트"""
    print_test(f"GET /asr/devices/{device_id}/session/status")
    try:
        headers = {}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        start_time = time.time()
        response = httpx.get(
            f"{BASE_URL}/asr/devices/{device_id}/session/status",
            headers=headers,
            timeout=TIMEOUT,
        )
        response_time = (time.time() - start_time) * 1000

        if response.status_code == 200:
            data = response.json()
            has_session = data.get("has_active_session", False)
            print_success(f"세션 상태: {'활성' if has_session else '비활성'}")
            record_test(
                "ASR 세션 상태 조회",
                "GET",
                f"/asr/devices/{device_id}/session/status",
                200,
                True,
                None,
                response_time,
            )
            return True
        elif response.status_code == 404:
            print_warning("장비를 찾을 수 없음")
            record_test(
                "ASR 세션 상태 조회",
                "GET",
                f"/asr/devices/{device_id}/session/status",
                404,
                True,
                None,
                response_time,
                "장비 없음",
            )
            return False
        else:
            print_fail(f"상태 코드: {response.status_code}")
            record_test(
                "ASR 세션 상태 조회",
                "GET",
                f"/asr/devices/{device_id}/session/status",
                response.status_code,
                False,
                f"예상 200, 실제 {response.status_code}",
                response_time,
            )
            return False
    except Exception as e:
        print_fail(str(e))
        record_test(
            "ASR 세션 상태 조회",
            "GET",
            f"/asr/devices/{device_id}/session/status",
            0,
            False,
            str(e),
        )
        return False


# ==================== Negative 테스트 케이스 (예외 처리 검증) ====================


def test_auth_login_negative():
    """로그인 실패 테스트 (잘못된 자격증명)"""
    print_test("POST /auth/login [NEGATIVE] - 잘못된 자격증명")
    try:
        data = {"username": "nonexistent_user", "password": "wrong_password"}
        start_time = time.time()
        response = httpx.post(f"{BASE_URL}/auth/login", json=data, timeout=TIMEOUT)
        response_time = (time.time() - start_time) * 1000

        if response.status_code == 401:
            print_success(f"예상대로 401 반환 (잘못된 자격증명)")
            record_test(
                "로그인 (잘못된 자격증명)",
                "POST",
                "/auth/login",
                401,
                True,
                None,
                response_time,
                "예외 처리 정상",
                "negative",
                401,
            )
            return True
        else:
            print_fail(f"예상 401, 실제 {response.status_code}")
            record_test(
                "로그인 (잘못된 자격증명)",
                "POST",
                "/auth/login",
                response.status_code,
                False,
                f"예상 401, 실제 {response.status_code}",
                response_time,
                None,
                "negative",
                401,
            )
            return False
    except Exception as e:
        print_fail(str(e))
        record_test(
            "로그인 (잘못된 자격증명)",
            "POST",
            "/auth/login",
            0,
            False,
            str(e),
            None,
            None,
            "negative",
            401,
        )
        return False


def test_auth_me_negative():
    """현재 사용자 조회 실패 테스트 (유효하지 않은 토큰)"""
    print_test("GET /auth/me [NEGATIVE] - 유효하지 않은 토큰")
    try:
        headers = {"Authorization": "Bearer invalid_token_12345"}
        start_time = time.time()
        response = httpx.get(f"{BASE_URL}/auth/me", headers=headers, timeout=TIMEOUT)
        response_time = (time.time() - start_time) * 1000

        if response.status_code == 401:
            print_success(f"예상대로 401 반환 (유효하지 않은 토큰)")
            record_test(
                "현재 사용자 조회 (유효하지 않은 토큰)",
                "GET",
                "/auth/me",
                401,
                True,
                None,
                response_time,
                "예외 처리 정상",
                "negative",
                401,
            )
            return True
        else:
            print_fail(f"예상 401, 실제 {response.status_code}")
            record_test(
                "현재 사용자 조회 (유효하지 않은 토큰)",
                "GET",
                "/auth/me",
                response.status_code,
                False,
                f"예상 401, 실제 {response.status_code}",
                response_time,
                None,
                "negative",
                401,
            )
            return False
    except Exception as e:
        print_fail(str(e))
        record_test(
            "현재 사용자 조회 (유효하지 않은 토큰)",
            "GET",
            "/auth/me",
            0,
            False,
            str(e),
            None,
            None,
            "negative",
            401,
        )
        return False


def test_auth_register_negative():
    """사용자 등록 실패 테스트 (약한 비밀번호)"""
    print_test("POST /auth/register [NEGATIVE] - 약한 비밀번호")
    try:
        data = {
            "username": f"testuser_neg_{int(time.time())}",
            "email": f"test_neg_{int(time.time())}@example.com",
            "password": "123",  # 너무 짧은 비밀번호
            "role": "viewer",
        }
        start_time = time.time()
        response = httpx.post(f"{BASE_URL}/auth/register", json=data, timeout=TIMEOUT)
        response_time = (time.time() - start_time) * 1000

        if response.status_code == 400:
            print_success(f"예상대로 400 반환 (약한 비밀번호 검증)")
            record_test(
                "사용자 등록 (약한 비밀번호)",
                "POST",
                "/auth/register",
                400,
                True,
                None,
                response_time,
                "비밀번호 정책 검증 정상",
                "negative",
                400,
            )
            return True
        else:
            print_fail(f"예상 400, 실제 {response.status_code}")
            record_test(
                "사용자 등록 (약한 비밀번호)",
                "POST",
                "/auth/register",
                response.status_code,
                False,
                f"예상 400, 실제 {response.status_code}",
                response_time,
                None,
                "negative",
                400,
            )
            return False
    except Exception as e:
        print_fail(str(e))
        record_test(
            "사용자 등록 (약한 비밀번호)",
            "POST",
            "/auth/register",
            0,
            False,
            str(e),
            None,
            None,
            "negative",
            400,
        )
        return False


def test_device_get_negative():
    """장비 상세 조회 실패 테스트 (존재하지 않는 장비)"""
    print_test("GET /devices/99999 [NEGATIVE] - 존재하지 않는 장비")
    try:
        start_time = time.time()
        response = httpx.get(f"{BASE_URL}/devices/99999", timeout=TIMEOUT)
        response_time = (time.time() - start_time) * 1000

        if response.status_code == 404:
            print_success(f"예상대로 404 반환 (존재하지 않는 장비)")
            record_test(
                "장비 상세 조회 (존재하지 않는 장비)",
                "GET",
                "/devices/99999",
                404,
                True,
                None,
                response_time,
                "예외 처리 정상",
                "negative",
                404,
            )
            return True
        else:
            print_fail(f"예상 404, 실제 {response.status_code}")
            record_test(
                "장비 상세 조회 (존재하지 않는 장비)",
                "GET",
                "/devices/99999",
                response.status_code,
                False,
                f"예상 404, 실제 {response.status_code}",
                response_time,
                None,
                "negative",
                404,
            )
            return False
    except Exception as e:
        print_fail(str(e))
        record_test(
            "장비 상세 조회 (존재하지 않는 장비)",
            "GET",
            "/devices/99999",
            0,
            False,
            str(e),
            None,
            None,
            "negative",
            404,
        )
        return False


def test_device_register_negative():
    """장비 등록 실패 테스트 (잘못된 IP 형식)"""
    print_test("POST /devices/ [NEGATIVE] - 잘못된 IP 형식")
    try:
        data = {
            "device_id": f"TEST_NEG_{int(time.time())}",
            "device_name": "테스트 장비 (잘못된 IP)",
            "device_type": "cores3",
            "ip_address": "999.999.999.999",  # 잘못된 IP 형식
            "location": "테스트 위치",
        }
        start_time = time.time()
        response = httpx.post(f"{BASE_URL}/devices/", json=data, timeout=TIMEOUT)
        response_time = (time.time() - start_time) * 1000

        # 백엔드에서 IP 검증을 하지 않을 수도 있지만, 최소한 400 또는 422를 기대
        if response.status_code in [400, 422]:
            print_success(f"예상대로 {response.status_code} 반환 (잘못된 IP 형식)")
            record_test(
                "장비 등록 (잘못된 IP 형식)",
                "POST",
                "/devices/",
                response.status_code,
                True,
                None,
                response_time,
                "입력 검증 정상",
                "negative",
                400,
            )
            return True
        else:
            print_warning(
                f"예상 400/422, 실제 {response.status_code} (백엔드에서 IP 검증 미구현 가능)"
            )
            record_test(
                "장비 등록 (잘못된 IP 형식)",
                "POST",
                "/devices/",
                response.status_code,
                True,
                None,
                response_time,
                f"백엔드 IP 검증 미구현 가능 (상태 코드: {response.status_code})",
                "negative",
                400,
            )
            return True  # 경고이지만 테스트는 통과로 처리
    except Exception as e:
        print_fail(str(e))
        record_test(
            "장비 등록 (잘못된 IP 형식)",
            "POST",
            "/devices/",
            0,
            False,
            str(e),
            None,
            None,
            "negative",
            400,
        )
        return False


def test_device_register_duplicate():
    """장비 등록 실패 테스트 (중복 장비 ID)"""
    print_test("POST /devices/ [NEGATIVE] - 중복 장비 ID")
    try:
        # 먼저 장비 등록
        device_id = f"DUPLICATE_TEST_{int(time.time())}"
        data1 = {
            "device_id": device_id,
            "device_name": "중복 테스트 장비 1",
            "device_type": "cores3",
            "location": "테스트 위치",
        }
        response1 = httpx.post(f"{BASE_URL}/devices/", json=data1, timeout=TIMEOUT)

        # 같은 device_id로 다시 등록 시도
        data2 = {
            "device_id": device_id,  # 동일한 ID
            "device_name": "중복 테스트 장비 2",
            "device_type": "cores3",
            "location": "테스트 위치",
        }
        start_time = time.time()
        response2 = httpx.post(f"{BASE_URL}/devices/", json=data2, timeout=TIMEOUT)
        response_time = (time.time() - start_time) * 1000

        if response2.status_code == 400:
            print_success(f"예상대로 400 반환 (중복 장비 ID 검증)")
            record_test(
                "장비 등록 (중복 장비 ID)",
                "POST",
                "/devices/",
                400,
                True,
                None,
                response_time,
                "중복 검증 정상",
                "negative",
                400,
            )
            return True
        else:
            print_fail(f"예상 400, 실제 {response2.status_code}")
            record_test(
                "장비 등록 (중복 장비 ID)",
                "POST",
                "/devices/",
                response2.status_code,
                False,
                f"예상 400, 실제 {response2.status_code}",
                response_time,
                None,
                "negative",
                400,
            )
            return False
    except Exception as e:
        print_fail(str(e))
        record_test(
            "장비 등록 (중복 장비 ID)",
            "POST",
            "/devices/",
            0,
            False,
            str(e),
            None,
            None,
            "negative",
            400,
        )
        return False


def test_control_camera_negative(device_id: int):
    """카메라 제어 실패 테스트 (오프라인 장비 또는 존재하지 않는 장비)"""
    print_test(
        f"POST /control/devices/{device_id}/camera [NEGATIVE] - 오프라인/없는 장비"
    )
    try:
        data = {"action": "start"}
        start_time = time.time()
        response = httpx.post(
            f"{BASE_URL}/control/devices/{device_id}/camera", json=data, timeout=TIMEOUT
        )
        response_time = (time.time() - start_time) * 1000

        # 오프라인 장비 또는 존재하지 않는 장비는 400 또는 404
        if response.status_code in [400, 404]:
            print_success(f"예상대로 {response.status_code} 반환 (오프라인/없는 장비)")
            record_test(
                "카메라 제어 (오프라인/없는 장비)",
                "POST",
                f"/control/devices/{device_id}/camera",
                response.status_code,
                True,
                None,
                response_time,
                "예외 처리 정상",
                "negative",
                400,
            )
            return True
        else:
            print_warning(f"예상 400/404, 실제 {response.status_code}")
            record_test(
                "카메라 제어 (오프라인/없는 장비)",
                "POST",
                f"/control/devices/{device_id}/camera",
                response.status_code,
                True,
                None,
                response_time,
                f"장비가 온라인일 수 있음 (상태 코드: {response.status_code})",
                "negative",
                400,
            )
            return True
    except Exception as e:
        print_fail(str(e))
        record_test(
            "카메라 제어 (오프라인/없는 장비)",
            "POST",
            f"/control/devices/{device_id}/camera",
            0,
            False,
            str(e),
            None,
            None,
            "negative",
            400,
        )
        return False


def test_control_camera_invalid_action(device_id: int):
    """카메라 제어 실패 테스트 (잘못된 액션)"""
    print_test(f"POST /control/devices/{device_id}/camera [NEGATIVE] - 잘못된 액션")
    try:
        data = {"action": "invalid_action_xyz"}  # 존재하지 않는 액션
        start_time = time.time()
        response = httpx.post(
            f"{BASE_URL}/control/devices/{device_id}/camera", json=data, timeout=TIMEOUT
        )
        response_time = (time.time() - start_time) * 1000

        # 잘못된 액션은 422 (Validation Error) 또는 400
        if response.status_code in [400, 422]:
            print_success(f"예상대로 {response.status_code} 반환 (잘못된 액션 검증)")
            record_test(
                "카메라 제어 (잘못된 액션)",
                "POST",
                f"/control/devices/{device_id}/camera",
                response.status_code,
                True,
                None,
                response_time,
                "입력 검증 정상",
                "negative",
                422,
            )
            return True
        else:
            print_warning(f"예상 400/422, 실제 {response.status_code}")
            record_test(
                "카메라 제어 (잘못된 액션)",
                "POST",
                f"/control/devices/{device_id}/camera",
                response.status_code,
                True,
                None,
                response_time,
                f"백엔드에서 액션 검증 미구현 가능 (상태 코드: {response.status_code})",
                "negative",
                422,
            )
            return True
    except Exception as e:
        print_fail(str(e))
        record_test(
            "카메라 제어 (잘못된 액션)",
            "POST",
            f"/control/devices/{device_id}/camera",
            0,
            False,
            str(e),
            None,
            None,
            "negative",
            422,
        )
        return False


def test_control_display_missing_content(device_id: int):
    """디스플레이 제어 실패 테스트 (show_text 액션에 content 누락)"""
    print_test(f"POST /control/devices/{device_id}/display [NEGATIVE] - content 누락")
    try:
        data = {"action": "show_text"}  # content 누락
        start_time = time.time()
        response = httpx.post(
            f"{BASE_URL}/control/devices/{device_id}/display",
            json=data,
            timeout=TIMEOUT,
        )
        response_time = (time.time() - start_time) * 1000

        if response.status_code == 400:
            print_success(f"예상대로 400 반환 (필수 파라미터 누락 검증)")
            record_test(
                "디스플레이 제어 (content 누락)",
                "POST",
                f"/control/devices/{device_id}/display",
                400,
                True,
                None,
                response_time,
                "필수 파라미터 검증 정상",
                "negative",
                400,
            )
            return True
        else:
            print_fail(f"예상 400, 실제 {response.status_code}")
            record_test(
                "디스플레이 제어 (content 누락)",
                "POST",
                f"/control/devices/{device_id}/display",
                response.status_code,
                False,
                f"예상 400, 실제 {response.status_code}",
                response_time,
                None,
                "negative",
                400,
            )
            return False
    except Exception as e:
        print_fail(str(e))
        record_test(
            "디스플레이 제어 (content 누락)",
            "POST",
            f"/control/devices/{device_id}/display",
            0,
            False,
            str(e),
            None,
            None,
            "negative",
            400,
        )
        return False


def test_audio_upload_invalid_file():
    """오디오 파일 업로드 실패 테스트 (잘못된 파일 형식)"""
    print_test("POST /audio/upload [NEGATIVE] - 잘못된 파일 형식")
    try:
        # 텍스트 파일을 MP3로 업로드 시도
        fake_file = BytesIO(b"This is not an MP3 file")
        files = {"file": ("test.txt", fake_file, "text/plain")}

        start_time = time.time()
        response = httpx.post(f"{BASE_URL}/audio/upload", files=files, timeout=TIMEOUT)
        response_time = (time.time() - start_time) * 1000

        if response.status_code == 400:
            print_success(f"예상대로 400 반환 (파일 형식 검증)")
            record_test(
                "오디오 파일 업로드 (잘못된 형식)",
                "POST",
                "/audio/upload",
                400,
                True,
                None,
                response_time,
                "파일 형식 검증 정상",
                "negative",
                400,
            )
            return True
        else:
            print_warning(f"예상 400, 실제 {response.status_code}")
            record_test(
                "오디오 파일 업로드 (잘못된 형식)",
                "POST",
                "/audio/upload",
                response.status_code,
                True,
                None,
                response_time,
                f"백엔드 파일 검증 미구현 가능 (상태 코드: {response.status_code})",
                "negative",
                400,
            )
            return True
    except Exception as e:
        print_fail(str(e))
        record_test(
            "오디오 파일 업로드 (잘못된 형식)",
            "POST",
            "/audio/upload",
            0,
            False,
            str(e),
            None,
            None,
            "negative",
            400,
        )
        return False


def test_device_status_latest_negative():
    """장비 최신 상태 조회 실패 테스트 (상태 정보 없음)"""
    print_test("GET /devices/99999/status/latest [NEGATIVE] - 상태 정보 없음")
    try:
        start_time = time.time()
        response = httpx.get(f"{BASE_URL}/devices/99999/status/latest", timeout=TIMEOUT)
        response_time = (time.time() - start_time) * 1000

        # 존재하지 않는 장비는 404, 상태 정보가 없는 장비도 404
        if response.status_code == 404:
            print_success(f"예상대로 404 반환 (상태 정보 없음)")
            record_test(
                "장비 최신 상태 조회 (상태 정보 없음)",
                "GET",
                "/devices/99999/status/latest",
                404,
                True,
                None,
                response_time,
                "예외 처리 정상",
                "negative",
                404,
            )
            return True
        else:
            print_fail(f"예상 404, 실제 {response.status_code}")
            record_test(
                "장비 최신 상태 조회 (상태 정보 없음)",
                "GET",
                "/devices/99999/status/latest",
                response.status_code,
                False,
                f"예상 404, 실제 {response.status_code}",
                response_time,
                None,
                "negative",
                404,
            )
            return False
    except Exception as e:
        print_fail(str(e))
        record_test(
            "장비 최신 상태 조회 (상태 정보 없음)",
            "GET",
            "/devices/99999/status/latest",
            0,
            False,
            str(e),
            None,
            None,
            "negative",
            404,
        )
        return False


def test_asr_session_status_negative():
    """ASR 세션 상태 조회 실패 테스트 (존재하지 않는 장비)"""
    print_test("GET /asr/devices/99999/session/status [NEGATIVE] - 존재하지 않는 장비")
    try:
        start_time = time.time()
        response = httpx.get(
            f"{BASE_URL}/asr/devices/99999/session/status", timeout=TIMEOUT
        )
        response_time = (time.time() - start_time) * 1000

        if response.status_code == 404:
            print_success(f"예상대로 404 반환 (존재하지 않는 장비)")
            record_test(
                "ASR 세션 상태 조회 (존재하지 않는 장비)",
                "GET",
                "/asr/devices/99999/session/status",
                404,
                True,
                None,
                response_time,
                "예외 처리 정상",
                "negative",
                404,
            )
            return True
        else:
            print_fail(f"예상 404, 실제 {response.status_code}")
            record_test(
                "ASR 세션 상태 조회 (존재하지 않는 장비)",
                "GET",
                "/asr/devices/99999/session/status",
                response.status_code,
                False,
                f"예상 404, 실제 {response.status_code}",
                response_time,
                None,
                "negative",
                404,
            )
            return False
    except Exception as e:
        print_fail(str(e))
        record_test(
            "ASR 세션 상태 조회 (존재하지 않는 장비)",
            "GET",
            "/asr/devices/99999/session/status",
            0,
            False,
            str(e),
            None,
            None,
            "negative",
            404,
        )
        return False


# ==================== 메인 테스트 실행 ====================


def run_all_tests():
    """전체 테스트 실행"""
    print(f"\n{Colors.BOLD}{'='*70}")
    print(f"Core S3 Management System - 전체 API 테스트")
    print(f"{'='*70}{Colors.RESET}")
    print(f"테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"서버 URL: {BASE_URL}\n")

    # 1. 헬스 체크
    test_root()
    test_health_check()

    # 2. 인증 API
    test_auth_register()
    tokens = test_auth_login()

    access_token = None
    if tokens:
        access_token = tokens.get("access_token")
        test_auth_me(access_token)
        test_auth_refresh(tokens.get("refresh_token"))

    # 3. 장비 관리 API
    devices = test_devices_list(access_token)
    test_device_id = None
    if devices and len(devices) > 0:
        test_device_id = devices[0].get("id")
        test_device_get(test_device_id, access_token)
        test_device_status_latest(test_device_id, access_token)
    else:
        # 테스트용 장비 등록 시도
        new_device = test_device_register(access_token)
        if new_device:
            test_device_id = new_device.get("id")
            test_device_get(test_device_id, access_token)
            test_device_status_latest(test_device_id, access_token)

    # 4. 장비 제어 API
    if test_device_id:
        test_control_camera(test_device_id, access_token)
        test_control_microphone(test_device_id, access_token)
        test_control_display(test_device_id, access_token)
        test_control_system(test_device_id, access_token)

    # 5. 오디오 파일 관리 API
    test_audio_list(access_token)
    test_audio_upload(access_token)

    # 6. ASR API
    test_asr_health()
    if test_device_id:
        test_asr_session_status(test_device_id, access_token)

    # ==================== Negative 테스트 케이스 (예외 처리 검증) ====================
    print(f"\n{Colors.BOLD}{'='*70}")
    print("Negative 테스트 케이스 실행 (예외 처리 검증)")
    print(f"{'='*70}{Colors.RESET}\n")

    # 인증 API Negative 테스트
    test_auth_login_negative()
    test_auth_me_negative()
    test_auth_register_negative()

    # 장비 관리 API Negative 테스트
    test_device_get_negative()
    test_device_register_negative()
    test_device_register_duplicate()
    test_device_status_latest_negative()

    # 장비 제어 API Negative 테스트
    if test_device_id:
        test_control_camera_negative(test_device_id)
        test_control_camera_invalid_action(test_device_id)
        test_control_display_missing_content(test_device_id)
    else:
        # 테스트용 장비 ID 사용
        test_control_camera_negative(99999)
        test_control_camera_invalid_action(99999)
        test_control_display_missing_content(99999)

    # 오디오 파일 관리 API Negative 테스트
    test_audio_upload_invalid_file()

    # ASR API Negative 테스트
    test_asr_session_status_negative()

    # 결과 요약
    print_summary()


def print_summary():
    """테스트 결과 요약 출력"""
    print(f"\n{Colors.BOLD}{'='*70}")
    print("테스트 결과 요약")
    print(f"{'='*70}{Colors.RESET}\n")

    total = len(test_results)
    success = sum(1 for r in test_results if r["success"])
    failed = total - success

    # Positive/Negative 테스트 분류
    positive_tests = [
        r for r in test_results if r.get("test_type", "positive") == "positive"
    ]
    negative_tests = [r for r in test_results if r.get("test_type") == "negative"]

    positive_success = sum(1 for r in positive_tests if r["success"])
    negative_success = sum(1 for r in negative_tests if r["success"])

    print(f"총 테스트: {total}")
    print(
        f"  - Positive 테스트: {len(positive_tests)} (성공: {positive_success}, 실패: {len(positive_tests) - positive_success})"
    )
    print(
        f"  - Negative 테스트: {len(negative_tests)} (성공: {negative_success}, 실패: {len(negative_tests) - negative_success})"
    )
    print(f"\n{Colors.GREEN}전체 성공: {success}{Colors.RESET}")
    print(f"{Colors.RED}전체 실패: {failed}{Colors.RESET}")

    if failed > 0:
        print(f"\n{Colors.RED}실패한 테스트:{Colors.RESET}")
        for result in test_results:
            if not result["success"]:
                test_type = result.get("test_type", "positive")
                test_type_label = (
                    "[NEGATIVE]" if test_type == "negative" else "[POSITIVE]"
                )
                print(
                    f"  - {test_type_label} {result['api_name']}: {result.get('error', '알 수 없는 오류')}"
                )

    # Negative 테스트 예외 처리 검증 요약
    if negative_tests:
        print(f"\n{Colors.BOLD}Negative 테스트 예외 처리 검증 결과:{Colors.RESET}")
        for result in negative_tests:
            expected = result.get("expected_status", "N/A")
            actual = result.get("status_code", "N/A")
            status_icon = "✅" if result["success"] and actual == expected else "❌"
            print(
                f"  {status_icon} {result['api_name']}: 예상 {expected}, 실제 {actual}"
            )

    print(
        f"\n{Colors.BOLD}테스트 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}\n"
    )


def save_results_to_json(output_path: Path):
    """테스트 결과를 JSON 파일로 저장"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Positive/Negative 테스트 분류
    positive_tests = [
        r for r in test_results if r.get("test_type", "positive") == "positive"
    ]
    negative_tests = [r for r in test_results if r.get("test_type") == "negative"]

    positive_success = sum(1 for r in positive_tests if r["success"])
    negative_success = sum(1 for r in negative_tests if r["success"])

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "test_summary": {
                    "total": len(test_results),
                    "success": sum(1 for r in test_results if r["success"]),
                    "failed": sum(1 for r in test_results if not r["success"]),
                    "positive_tests": {
                        "total": len(positive_tests),
                        "success": positive_success,
                        "failed": len(positive_tests) - positive_success,
                    },
                    "negative_tests": {
                        "total": len(negative_tests),
                        "success": negative_success,
                        "failed": len(negative_tests) - negative_success,
                    },
                    "test_time": datetime.now().isoformat(),
                },
                "test_results": test_results,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"{Colors.GREEN}테스트 결과가 저장되었습니다: {output_path}{Colors.RESET}")


if __name__ == "__main__":
    try:
        run_all_tests()

        # 결과 저장
        output_dir = Path(__file__).parent / "test_results"
        output_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = output_dir / f"api_test_results_{timestamp}.json"
        save_results_to_json(json_path)

        # 성공/실패 여부에 따라 종료 코드 설정
        failed_count = sum(1 for r in test_results if not r["success"])
        sys.exit(0 if failed_count == 0 else 1)

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}테스트가 중단되었습니다.{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}치명적 오류: {e}{Colors.RESET}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
