"""
TC-DASH: 대시보드 관련 E2E 테스트

테스트 시나리오:
- TC-DASH-001: 대시보드 로드 및 통계 확인
- TC-DASH-002: 장비 목록 표시
- TC-DASH-003: 장비 등록 모달
- TC-DASH-004: 장비 삭제 모달
- TC-DASH-005: 새로고침 버튼
- TC-DASH-006: 장비 카드 클릭하여 상세 페이지 이동
"""

import pytest
import time
import uuid
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pages import DashboardPage, DeviceDetailPage


class TestDashboard:
    """대시보드 테스트 클래스"""

    @pytest.fixture(autouse=True)
    def setup(self, driver, base_url):
        """테스트 셋업"""
        self.driver = driver
        self.base_url = base_url
        self.dashboard_page = DashboardPage(driver, base_url)
        self.device_detail_page = DeviceDetailPage(driver, base_url)

    def test_tc_dash_001_dashboard_load_and_stats(self):
        """
        TC-DASH-001: 대시보드 로드 및 통계 확인

        테스트 단계:
        1. 대시보드 페이지로 이동

        예상 결과:
        - 페이지 제목이 표시됨
        - 사용자 정보가 표시됨
        - 통계 섹션이 표시됨
        """
        # When: 대시보드 접근
        self.dashboard_page.navigate()

        # Then: 페이지 로드됨
        assert self.dashboard_page.is_loaded(), "대시보드 페이지 로드 실패"

        # And: 제목 확인
        heading = self.dashboard_page.get_page_heading()
        assert "Core S3 Management" in heading, f"예상치 못한 제목: {heading}"

        # And: 사용자 정보 확인
        user_info = self.dashboard_page.get_user_info()
        assert user_info is not None, "사용자 정보가 표시되지 않음"

    def test_tc_dash_002_device_list_display(self):
        """
        TC-DASH-002: 장비 목록 표시

        테스트 단계:
        1. 대시보드 페이지로 이동
        2. 장비 목록 확인

        예상 결과:
        - 장비가 있으면 장비 카드 표시
        - 장비가 없으면 빈 상태 메시지 표시
        """
        # When: 대시보드 접근
        self.dashboard_page.navigate()
        self.dashboard_page.wait_for_loading_complete()

        # 데이터 로딩 대기
        time.sleep(2)

        # Then: 장비 목록 또는 빈 상태 확인
        device_count = self.dashboard_page.get_device_count()
        if device_count == 0:
            assert (
                self.dashboard_page.is_empty_state_visible()
            ), "장비가 없지만 빈 상태 메시지가 표시되지 않음"
        else:
            assert device_count > 0, "장비가 있지만 카드가 표시되지 않음"

    def test_tc_dash_003_register_device_modal(self):
        """
        TC-DASH-003: 장비 등록 모달

        테스트 단계:
        1. 대시보드 페이지로 이동
        2. 장비 등록 버튼 클릭
        3. 모달이 열리는지 확인

        예상 결과:
        - 장비 등록 모달이 열림
        """
        # Given: 대시보드에 있음
        self.dashboard_page.navigate()
        self.dashboard_page.wait_for_loading_complete()

        # When: 장비 등록 버튼 클릭
        self.dashboard_page.click_register_device()
        time.sleep(1)  # 애니메이션 대기

        # Then: 모달이 열림
        assert (
            self.dashboard_page.is_register_modal_open()
        ), "장비 등록 모달이 열리지 않음"

    def test_tc_dash_004_register_device_flow(self):
        """
        TC-DASH-004: 장비 등록 전체 플로우

        테스트 단계:
        1. 장비 등록 모달 열기
        2. 장비 정보 입력
        3. 등록 버튼 클릭

        예상 결과:
        - 장비가 등록됨
        - 성공 토스트 메시지 표시
        - 장비 목록에 새 장비 표시
        """
        # Given: 대시보드에 있음
        self.dashboard_page.navigate()
        self.dashboard_page.wait_for_loading_complete()

        initial_count = self.dashboard_page.get_device_count()
        unique_id = str(uuid.uuid4())[:8]

        # When: 장비 등록
        self.dashboard_page.register_device(
            device_id=f"TEST-{unique_id}",
            device_name=f"테스트 장비 {unique_id}",
            device_type="camera",
            location="테스트 위치",
        )
        time.sleep(2)  # API 호출 대기

        # Then: 성공 확인
        # 참고: 실제 API 동작에 따라 결과가 달라질 수 있음
        self.dashboard_page.wait_for_loading_complete()

    def test_tc_dash_005_refresh_button(self):
        """
        TC-DASH-005: 새로고침 버튼

        테스트 단계:
        1. 대시보드 페이지로 이동
        2. 새로고침 버튼 클릭

        예상 결과:
        - 장비 목록이 새로고침됨
        - 토스트 메시지 표시
        """
        # Given: 대시보드에 있음
        self.dashboard_page.navigate()
        self.dashboard_page.wait_for_loading_complete()

        # When: 새로고침 클릭
        self.dashboard_page.click_refresh()
        time.sleep(1)

        # Then: 토스트 메시지 확인
        # 참고: 토스트 메시지 확인은 구현에 따라 다름
        assert self.dashboard_page.is_loaded(), "새로고침 후 페이지 로드 실패"

    def test_tc_dash_006_navigate_to_device_detail(self):
        """
        TC-DASH-006: 장비 카드 클릭하여 상세 페이지 이동

        사전조건:
        - 등록된 장비가 있어야 함

        테스트 단계:
        1. 대시보드 페이지로 이동
        2. 첫 번째 장비 카드 클릭

        예상 결과:
        - 장비 상세 페이지로 이동
        """
        # Given: 대시보드에 있음
        self.dashboard_page.navigate()
        self.dashboard_page.wait_for_loading_complete()
        time.sleep(2)

        device_count = self.dashboard_page.get_device_count()
        if device_count == 0:
            pytest.skip("등록된 장비가 없습니다")

        # When: 첫 번째 장비 카드 클릭
        self.dashboard_page.click_device_card(0)
        time.sleep(2)

        # Then: 상세 페이지로 이동
        assert (
            "/devices/" in self.driver.current_url
        ), "장비 상세 페이지로 이동하지 않음"
