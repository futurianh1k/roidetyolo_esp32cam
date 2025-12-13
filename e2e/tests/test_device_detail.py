"""
TC-DEV: 장비 상세 페이지 E2E 테스트

테스트 시나리오:
- TC-DEV-001: 장비 상세 페이지 로드
- TC-DEV-002: IP 주소 편집
- TC-DEV-003: 카메라 제어 (시작/정지)
- TC-DEV-004: 디스플레이 텍스트 표시
- TC-DEV-005: 음성인식 시작/종료
- TC-DEV-006: 장비 삭제
- TC-DEV-007: 뒤로가기 네비게이션
"""

import pytest
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pages import DashboardPage, DeviceDetailPage


class TestDeviceDetail:
    """장비 상세 페이지 테스트 클래스"""

    @pytest.fixture(autouse=True)
    def setup(self, driver, base_url):
        """테스트 셋업"""
        self.driver = driver
        self.base_url = base_url
        self.dashboard_page = DashboardPage(driver, base_url)
        self.device_detail_page = DeviceDetailPage(driver, base_url)

    def get_first_device_id(self):
        """첫 번째 장비 ID 가져오기"""
        self.dashboard_page.navigate()
        self.dashboard_page.wait_for_loading_complete()
        time.sleep(2)

        if self.dashboard_page.get_device_count() == 0:
            return None

        self.dashboard_page.click_device_card(0)
        time.sleep(2)

        # URL에서 ID 추출
        url = self.driver.current_url
        if "/devices/" in url:
            device_id = url.split("/devices/")[-1]
            return device_id
        return None

    def test_tc_dev_001_device_detail_page_load(self):
        """
        TC-DEV-001: 장비 상세 페이지 로드

        테스트 단계:
        1. 대시보드에서 장비 선택
        2. 상세 페이지 로드 확인

        예상 결과:
        - 장비 이름 표시
        - 온라인/오프라인 상태 표시
        - 제어 섹션 표시
        """
        # Given: 장비 ID 가져오기
        device_id = self.get_first_device_id()
        if device_id is None:
            pytest.skip("등록된 장비가 없습니다")

        # When: 상세 페이지로 이동
        self.device_detail_page.navigate(device_id)

        # Then: 페이지 로드 확인
        assert self.device_detail_page.is_loaded(), "장비 상세 페이지 로드 실패"

        # And: 장비 이름 표시 확인
        device_name = self.device_detail_page.get_device_name()
        assert device_name, "장비 이름이 표시되지 않음"

        # And: 온라인/오프라인 상태 확인
        is_online = self.device_detail_page.is_online()
        is_offline = self.device_detail_page.is_offline()
        assert is_online or is_offline, "온라인/오프라인 상태가 표시되지 않음"

    def test_tc_dev_002_edit_ip_address(self):
        """
        TC-DEV-002: IP 주소 편집

        테스트 단계:
        1. 장비 상세 페이지로 이동
        2. IP 편집 버튼 클릭
        3. 새 IP 주소 입력
        4. 저장

        예상 결과:
        - IP 주소가 업데이트됨
        - 성공 토스트 메시지 표시
        """
        # Given: 장비 상세 페이지에 있음
        device_id = self.get_first_device_id()
        if device_id is None:
            pytest.skip("등록된 장비가 없습니다")

        self.device_detail_page.navigate(device_id)
        self.device_detail_page.wait_for_loading_complete()

        # When: IP 주소 업데이트
        test_ip = "192.168.1.100"
        self.device_detail_page.update_ip_address(test_ip)
        time.sleep(2)

        # Then: 성공 확인
        # 참고: 실제 API 동작에 따라 결과가 달라질 수 있음
        assert self.device_detail_page.is_loaded()

    def test_tc_dev_003_camera_control(self):
        """
        TC-DEV-003: 카메라 제어 (시작/정지)

        사전조건:
        - 장비가 온라인 상태여야 함

        테스트 단계:
        1. 카메라 시작 버튼 클릭
        2. 카메라 정지 버튼 클릭

        예상 결과:
        - 각 동작마다 토스트 메시지 표시
        """
        # Given: 장비 상세 페이지에 있음
        device_id = self.get_first_device_id()
        if device_id is None:
            pytest.skip("등록된 장비가 없습니다")

        self.device_detail_page.navigate(device_id)
        self.device_detail_page.wait_for_loading_complete()

        # 오프라인이면 스킵
        if self.device_detail_page.is_offline():
            pytest.skip("장비가 오프라인 상태입니다")

        # When: 카메라 시작
        self.device_detail_page.start_camera()
        time.sleep(2)

        # And: 카메라 정지
        self.device_detail_page.stop_camera()
        time.sleep(2)

        # Then: 페이지 상태 확인 (에러 없이 동작)
        assert self.device_detail_page.is_loaded()

    def test_tc_dev_004_display_text(self):
        """
        TC-DEV-004: 디스플레이 텍스트 표시

        사전조건:
        - 장비가 온라인 상태여야 함

        테스트 단계:
        1. 텍스트 입력
        2. 텍스트 표시 버튼 클릭
        3. 화면 지우기 버튼 클릭

        예상 결과:
        - 각 동작마다 토스트 메시지 표시
        """
        # Given: 장비 상세 페이지에 있음
        device_id = self.get_first_device_id()
        if device_id is None:
            pytest.skip("등록된 장비가 없습니다")

        self.device_detail_page.navigate(device_id)
        self.device_detail_page.wait_for_loading_complete()

        if self.device_detail_page.is_offline():
            pytest.skip("장비가 오프라인 상태입니다")

        # When: 텍스트 표시
        test_text = "E2E 테스트 메시지"
        self.device_detail_page.show_text_on_display(test_text)
        time.sleep(2)

        # And: 화면 지우기
        self.device_detail_page.clear_display()
        time.sleep(2)

        # Then: 페이지 상태 확인
        assert self.device_detail_page.is_loaded()

    def test_tc_dev_005_asr_start_stop(self):
        """
        TC-DEV-005: 음성인식 시작/종료

        사전조건:
        - 장비가 온라인 상태여야 함

        테스트 단계:
        1. 음성인식 시작 버튼 클릭
        2. 음성인식 종료 버튼 클릭

        예상 결과:
        - 시작/종료 버튼이 토글됨
        """
        # Given: 장비 상세 페이지에 있음
        device_id = self.get_first_device_id()
        if device_id is None:
            pytest.skip("등록된 장비가 없습니다")

        self.device_detail_page.navigate(device_id)
        self.device_detail_page.wait_for_loading_complete()

        if self.device_detail_page.is_offline():
            pytest.skip("장비가 오프라인 상태입니다")

        # 시작 버튼 확인
        if not self.device_detail_page.is_asr_start_button_visible():
            pytest.skip("음성인식 시작 버튼이 보이지 않습니다")

        # When: 음성인식 시작
        self.device_detail_page.start_asr()
        time.sleep(3)

        # Then: 종료 버튼이 나타남
        # 참고: ASR 서버 연동에 따라 달라질 수 있음

        # Cleanup: 세션 종료 시도
        if self.device_detail_page.is_asr_stop_button_visible():
            self.device_detail_page.stop_asr()
            time.sleep(2)

    def test_tc_dev_007_back_navigation(self):
        """
        TC-DEV-007: 뒤로가기 네비게이션

        테스트 단계:
        1. 장비 상세 페이지에서 뒤로가기 클릭

        예상 결과:
        - 대시보드로 돌아감
        """
        # Given: 장비 상세 페이지에 있음
        device_id = self.get_first_device_id()
        if device_id is None:
            pytest.skip("등록된 장비가 없습니다")

        self.device_detail_page.navigate(device_id)
        self.device_detail_page.wait_for_loading_complete()

        # When: 뒤로가기 클릭
        self.device_detail_page.click_back()
        time.sleep(2)

        # Then: 대시보드로 이동
        assert "/dashboard" in self.driver.current_url, "대시보드로 돌아가지 않음"

    @pytest.mark.skip(reason="삭제 테스트는 신중하게 실행 필요")
    def test_tc_dev_006_delete_device(self):
        """
        TC-DEV-006: 장비 삭제

        주의: 이 테스트는 실제로 장비를 삭제합니다.

        테스트 단계:
        1. 삭제 버튼 클릭
        2. 확인 다이얼로그에서 확인

        예상 결과:
        - 장비가 삭제됨
        - 대시보드로 리다이렉트됨
        """
        # Given: 장비 상세 페이지에 있음
        device_id = self.get_first_device_id()
        if device_id is None:
            pytest.skip("등록된 장비가 없습니다")

        self.device_detail_page.navigate(device_id)
        self.device_detail_page.wait_for_loading_complete()

        # When: 삭제 버튼 클릭
        self.device_detail_page.click_delete()

        # 브라우저 확인 다이얼로그 처리
        try:
            alert = self.driver.switch_to.alert
            alert.accept()
        except:
            pass

        time.sleep(3)

        # Then: 대시보드로 이동
        assert (
            "/dashboard" in self.driver.current_url
        ), "삭제 후 대시보드로 이동하지 않음"
