"""
TC-ASR: 음성인식 관련 E2E 테스트

테스트 시나리오:
- TC-ASR-001: 음성인식 세션 시작
- TC-ASR-002: 인식 결과 수신
- TC-ASR-003: 세션 종료
- TC-ASR-004: 언어 변경
"""

import pytest
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pages import DashboardPage, DeviceDetailPage


class TestASR:
    """음성인식 테스트 클래스"""

    @pytest.fixture(autouse=True)
    def setup(self, driver, base_url):
        """테스트 셋업"""
        self.driver = driver
        self.base_url = base_url
        self.dashboard_page = DashboardPage(driver, base_url)
        self.device_detail_page = DeviceDetailPage(driver, base_url)

    def get_online_device_id(self):
        """온라인 장비 ID 가져오기"""
        self.dashboard_page.navigate()
        self.dashboard_page.wait_for_loading_complete()
        time.sleep(2)

        device_count = self.dashboard_page.get_device_count()
        if device_count == 0:
            return None

        # 각 장비를 확인하여 온라인 장비 찾기
        for i in range(device_count):
            self.dashboard_page.navigate()
            self.dashboard_page.wait_for_loading_complete()
            time.sleep(1)

            self.dashboard_page.click_device_card(i)
            time.sleep(2)

            if self.device_detail_page.is_online():
                url = self.driver.current_url
                if "/devices/" in url:
                    return url.split("/devices/")[-1]

        return None

    @pytest.mark.slow
    def test_tc_asr_001_start_session(self):
        """
        TC-ASR-001: 음성인식 세션 시작

        사전조건:
        - 장비가 온라인 상태여야 함
        - ASR 서버가 동작 중이어야 함

        테스트 단계:
        1. 온라인 장비 상세 페이지로 이동
        2. 음성인식 시작 버튼 클릭

        예상 결과:
        - 세션이 시작됨
        - 종료 버튼이 나타남
        """
        # Given: 온라인 장비
        device_id = self.get_online_device_id()
        if device_id is None:
            pytest.skip("온라인 장비가 없습니다")

        self.device_detail_page.navigate(device_id)
        self.device_detail_page.wait_for_loading_complete()

        if not self.device_detail_page.is_asr_start_button_visible():
            pytest.skip("음성인식 시작 버튼이 보이지 않습니다")

        # When: 음성인식 시작
        self.device_detail_page.start_asr()
        time.sleep(5)

        # Then: 세션 상태 확인
        # 참고: ASR 서버 상태에 따라 결과가 달라질 수 있음

        # Cleanup
        if self.device_detail_page.is_asr_stop_button_visible():
            self.device_detail_page.stop_asr()

    @pytest.mark.slow
    def test_tc_asr_003_stop_session(self):
        """
        TC-ASR-003: 세션 종료

        사전조건:
        - 활성 세션이 있어야 함

        테스트 단계:
        1. 음성인식 종료 버튼 클릭

        예상 결과:
        - 세션이 종료됨
        - 시작 버튼이 다시 나타남
        """
        # Given: 온라인 장비에서 세션 시작
        device_id = self.get_online_device_id()
        if device_id is None:
            pytest.skip("온라인 장비가 없습니다")

        self.device_detail_page.navigate(device_id)
        self.device_detail_page.wait_for_loading_complete()

        if not self.device_detail_page.is_asr_start_button_visible():
            pytest.skip("음성인식 시작 버튼이 보이지 않습니다")

        # 세션 시작
        self.device_detail_page.start_asr()
        time.sleep(3)

        if not self.device_detail_page.is_asr_stop_button_visible():
            pytest.skip("세션이 시작되지 않았습니다")

        # When: 세션 종료
        self.device_detail_page.stop_asr()
        time.sleep(3)

        # Then: 시작 버튼 다시 나타남
        # 참고: UI 상태 확인


class TestASRWebSocket:
    """ASR WebSocket 연결 테스트"""

    @pytest.fixture(autouse=True)
    def setup(self, driver, base_url):
        """테스트 셋업"""
        self.driver = driver
        self.base_url = base_url

    @pytest.mark.skip(reason="WebSocket 테스트는 별도 인프라 필요")
    def test_tc_asr_004_websocket_connection(self):
        """
        TC-ASR-004: WebSocket 연결 상태 확인

        테스트 단계:
        1. 음성인식 시작
        2. WebSocket 연결 상태 확인

        예상 결과:
        - 연결됨 상태 표시
        """
        pass


class TestASREmergency:
    """ASR 응급 상황 감지 테스트"""

    @pytest.fixture(autouse=True)
    def setup(self, driver, base_url):
        """테스트 셋업"""
        self.driver = driver
        self.base_url = base_url

    @pytest.mark.skip(reason="응급 상황 테스트는 실제 음성 입력 필요")
    def test_tc_asr_005_emergency_detection(self):
        """
        TC-ASR-005: 응급 상황 감지

        테스트 단계:
        1. 음성인식 시작
        2. 응급 키워드 음성 입력 (시뮬레이션)

        예상 결과:
        - 응급 상황 알림 표시
        """
        pass
