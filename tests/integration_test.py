"""
통합 테스트 스크립트
백엔드/프론트엔드/펌웨어 간 통신 테스트

사용법:
    python integration_test.py

사전 요구사항:
    - 백엔드 서버 실행 중 (http://localhost:8000)
    - MQTT 브로커 실행 중 (localhost:1883)
    - 펌웨어가 장비에 플래시되어 있음 (선택사항)
"""

import os
import sys
import json
import time
import requests
from datetime import datetime

# Windows 콘솔에서 UTF-8 출력 설정
if sys.platform == "win32":
    os.system("chcp 65001 > nul")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 설정 - 환경변수 또는 기본값 사용
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
DEVICE_ID = int(os.environ.get("DEVICE_ID", "1"))


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


def print_header(text):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}")


def print_success(text):
    print(f"{Colors.GREEN}[OK] {text}{Colors.RESET}")


def print_error(text):
    print(f"{Colors.RED}[FAIL] {text}{Colors.RESET}")


def print_warning(text):
    print(f"{Colors.YELLOW}[WARN] {text}{Colors.RESET}")


def print_info(text):
    print(f"   {text}")


class IntegrationTest:
    def __init__(self):
        self.results = []
        self.backend_url = BACKEND_URL

    def run_all_tests(self):
        """모든 통합 테스트 실행"""
        print_header("통합 테스트 시작")
        print(f"Backend URL: {self.backend_url}")
        print(f"Device ID: {DEVICE_ID}")
        print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 테스트 실행
        self.test_backend_health()
        self.test_device_list()
        self.test_device_detail()
        self.test_device_status_post()
        self.test_device_status_get()
        self.test_device_control_camera()
        self.test_device_control_microphone()
        self.test_device_control_display()

        # 결과 요약
        self.print_summary()

    def add_result(self, name, success, message=""):
        self.results.append({"name": name, "success": success, "message": message})

    def test_backend_health(self):
        """백엔드 서버 상태 확인"""
        print_header("1. 백엔드 서버 상태 확인")

        try:
            response = requests.get(f"{self.backend_url}/", timeout=5)
            if response.status_code == 200:
                print_success("백엔드 서버 정상 동작")
                print_info(f"응답: {response.json()}")
                self.add_result("백엔드 서버 상태", True)
            else:
                print_error(f"서버 응답 오류: {response.status_code}")
                self.add_result(
                    "백엔드 서버 상태", False, f"Status: {response.status_code}"
                )
        except requests.exceptions.ConnectionError:
            print_error("백엔드 서버에 연결할 수 없습니다")
            print_warning(
                "서버를 시작하세요: cd backend && uvicorn app.main:app --reload --host 0.0.0.0"
            )
            self.add_result("백엔드 서버 상태", False, "Connection Error")
        except Exception as e:
            print_error(f"오류: {e}")
            self.add_result("백엔드 서버 상태", False, str(e))

    def test_device_list(self):
        """장비 목록 조회"""
        print_header("2. 장비 목록 조회")

        try:
            response = requests.get(f"{self.backend_url}/devices/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print_success(f"장비 목록 조회 성공: {data.get('total', 0)}개")
                devices = data.get("devices", [])
                for device in devices[:5]:  # 최대 5개만 표시
                    status = "[Online]" if device.get("is_online") else "[Offline]"
                    print_info(
                        f"  - [{device.get('id')}] {device.get('device_name')} {status}"
                    )
                self.add_result("장비 목록 조회", True)
            else:
                print_error(f"장비 목록 조회 실패: {response.status_code}")
                self.add_result(
                    "장비 목록 조회", False, f"Status: {response.status_code}"
                )
        except Exception as e:
            print_error(f"오류: {e}")
            self.add_result("장비 목록 조회", False, str(e))

    def test_device_detail(self):
        """장비 상세 조회"""
        print_header("3. 장비 상세 조회")

        try:
            response = requests.get(
                f"{self.backend_url}/devices/{DEVICE_ID}", timeout=5
            )
            if response.status_code == 200:
                device = response.json()
                print_success(f"장비 상세 조회 성공")
                print_info(f"  ID: {device.get('id')}")
                print_info(f"  이름: {device.get('device_name')}")
                print_info(f"  타입: {device.get('device_type')}")
                print_info(f"  온라인: {device.get('is_online')}")
                print_info(f"  IP: {device.get('ip_address')}")
                print_info(f"  마지막 연결: {device.get('last_seen_at')}")
                self.add_result("장비 상세 조회", True)
            elif response.status_code == 404:
                print_warning(f"장비 {DEVICE_ID}를 찾을 수 없습니다")
                self.add_result("장비 상세 조회", False, "Not Found")
            else:
                print_error(f"장비 상세 조회 실패: {response.status_code}")
                self.add_result(
                    "장비 상세 조회", False, f"Status: {response.status_code}"
                )
        except Exception as e:
            print_error(f"오류: {e}")
            self.add_result("장비 상세 조회", False, str(e))

    def test_device_status_post(self):
        """장비 상태 기록 (펌웨어 → 백엔드 시뮬레이션)"""
        print_header("4. 장비 상태 기록 테스트 (펌웨어 시뮬레이션)")

        status_data = {
            "battery_level": 85,
            "memory_usage": 150000,
            "storage_usage": None,
            "temperature": 42.5,
            "cpu_usage": 25,
            "camera_status": "active",
            "mic_status": "stopped",
        }

        try:
            response = requests.post(
                f"{self.backend_url}/devices/{DEVICE_ID}/status",
                json=status_data,
                timeout=5,
            )
            if response.status_code in [200, 201]:
                print_success("장비 상태 기록 성공")
                print_info(f"전송 데이터: {json.dumps(status_data, indent=2)}")
                self.add_result("장비 상태 기록", True)
            else:
                print_error(f"장비 상태 기록 실패: {response.status_code}")
                print_info(f"응답: {response.text}")
                self.add_result(
                    "장비 상태 기록", False, f"Status: {response.status_code}"
                )
        except Exception as e:
            print_error(f"오류: {e}")
            self.add_result("장비 상태 기록", False, str(e))

    def test_device_status_get(self):
        """장비 최신 상태 조회"""
        print_header("5. 장비 최신 상태 조회")

        try:
            response = requests.get(
                f"{self.backend_url}/devices/{DEVICE_ID}/status/latest", timeout=5
            )
            if response.status_code == 200:
                status = response.json()
                print_success("장비 최신 상태 조회 성공")
                print_info(f"  배터리: {status.get('battery_level')}%")
                print_info(f"  메모리: {status.get('memory_usage')} bytes")
                print_info(f"  온도: {status.get('temperature')}°C")
                print_info(f"  CPU: {status.get('cpu_usage')}%")
                print_info(f"  카메라: {status.get('camera_status')}")
                print_info(f"  마이크: {status.get('mic_status')}")
                print_info(f"  기록시간: {status.get('recorded_at')}")
                self.add_result("장비 최신 상태 조회", True)
            elif response.status_code == 404:
                print_warning("상태 기록이 없습니다")
                self.add_result("장비 최신 상태 조회", False, "No status found")
            else:
                print_error(f"상태 조회 실패: {response.status_code}")
                self.add_result(
                    "장비 최신 상태 조회", False, f"Status: {response.status_code}"
                )
        except Exception as e:
            print_error(f"오류: {e}")
            self.add_result("장비 최신 상태 조회", False, str(e))

    def test_device_control_camera(self):
        """카메라 제어 명령 테스트"""
        print_header("6. 카메라 제어 명령 테스트")

        control_data = {"action": "start"}

        try:
            response = requests.post(
                f"{self.backend_url}/control/devices/{DEVICE_ID}/camera",
                json=control_data,
                timeout=5,
            )
            if response.status_code == 200:
                print_success("카메라 시작 명령 전송 성공")
                print_info(f"응답: {response.json()}")
                self.add_result("카메라 제어", True)
            else:
                print_error(f"카메라 제어 실패: {response.status_code}")
                print_info(f"응답: {response.text}")
                self.add_result("카메라 제어", False, f"Status: {response.status_code}")
        except Exception as e:
            print_error(f"오류: {e}")
            self.add_result("카메라 제어", False, str(e))

    def test_device_control_microphone(self):
        """마이크 제어 명령 테스트"""
        print_header("7. 마이크(ASR) 제어 명령 테스트")

        control_data = {"action": "start_asr", "language": "ko"}

        try:
            response = requests.post(
                f"{self.backend_url}/control/devices/{DEVICE_ID}/microphone",
                json=control_data,
                timeout=5,
            )
            if response.status_code == 200:
                print_success("마이크 ASR 시작 명령 전송 성공")
                print_info(f"응답: {response.json()}")
                self.add_result("마이크 제어", True)
            else:
                print_error(f"마이크 제어 실패: {response.status_code}")
                print_info(f"응답: {response.text}")
                self.add_result("마이크 제어", False, f"Status: {response.status_code}")
        except Exception as e:
            print_error(f"오류: {e}")
            self.add_result("마이크 제어", False, str(e))

    def test_device_control_display(self):
        """디스플레이 제어 명령 테스트"""
        print_header("8. 디스플레이 제어 명령 테스트")

        control_data = {"action": "show_text", "content": "통합 테스트 메시지"}

        try:
            response = requests.post(
                f"{self.backend_url}/control/devices/{DEVICE_ID}/display",
                json=control_data,
                timeout=5,
            )
            if response.status_code == 200:
                print_success("디스플레이 텍스트 표시 명령 전송 성공")
                print_info(f"응답: {response.json()}")
                self.add_result("디스플레이 제어", True)
            else:
                print_error(f"디스플레이 제어 실패: {response.status_code}")
                print_info(f"응답: {response.text}")
                self.add_result(
                    "디스플레이 제어", False, f"Status: {response.status_code}"
                )
        except Exception as e:
            print_error(f"오류: {e}")
            self.add_result("디스플레이 제어", False, str(e))

    def print_summary(self):
        """테스트 결과 요약"""
        print_header("테스트 결과 요약")

        passed = sum(1 for r in self.results if r["success"])
        failed = len(self.results) - passed

        print(f"\n총 테스트: {len(self.results)}개")
        print(f"{Colors.GREEN}성공: {passed}개{Colors.RESET}")
        print(f"{Colors.RED}실패: {failed}개{Colors.RESET}")
        print()

        for result in self.results:
            status = (
                f"{Colors.GREEN}[OK]{Colors.RESET}"
                if result["success"]
                else f"{Colors.RED}[FAIL]{Colors.RESET}"
            )
            message = f" - {result['message']}" if result["message"] else ""
            print(f"  {status} {result['name']}{message}")

        print()
        if failed == 0:
            print_success("모든 테스트 통과!")
        else:
            print_warning(f"{failed}개 테스트 실패")


if __name__ == "__main__":
    test = IntegrationTest()
    test.run_all_tests()
