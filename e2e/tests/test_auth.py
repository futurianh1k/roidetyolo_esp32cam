"""
TC-AUTH: 인증 관련 E2E 테스트

테스트 시나리오:
- TC-AUTH-001: 로그인 성공
- TC-AUTH-002: 로그인 실패 (잘못된 비밀번호)
- TC-AUTH-003: 로그아웃
- TC-AUTH-004: 비로그인 상태 대시보드 접근
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pages import LoginPage, DashboardPage


class TestAuthentication:
    """인증 테스트 클래스"""

    @pytest.fixture(autouse=True)
    def setup(self, driver, base_url):
        """테스트 셋업"""
        self.driver = driver
        self.base_url = base_url
        self.login_page = LoginPage(driver, base_url)
        self.dashboard_page = DashboardPage(driver, base_url)

    @pytest.mark.skip(reason="인증 기능 현재 비활성화 - TODO: 활성화 후 테스트")
    def test_tc_auth_001_login_success(self, test_user):
        """
        TC-AUTH-001: 로그인 성공

        사전조건:
        - 테스트 사용자 계정이 존재해야 함

        테스트 단계:
        1. 로그인 페이지로 이동
        2. 유효한 사용자명 입력
        3. 유효한 비밀번호 입력
        4. 로그인 버튼 클릭

        예상 결과:
        - 대시보드로 리다이렉트됨
        - 사용자 정보가 표시됨
        """
        # Given: 로그인 페이지에 있음
        self.login_page.navigate()
        assert self.login_page.is_loaded(), "로그인 페이지 로드 실패"

        # When: 유효한 자격 증명으로 로그인
        self.login_page.login(test_user["username"], test_user["password"])
        self.login_page.wait_for_login_complete(timeout=15)

        # Then: 대시보드로 이동됨
        assert "/dashboard" in self.driver.current_url, "대시보드로 리다이렉트 실패"
        assert self.dashboard_page.is_loaded(), "대시보드 로드 실패"

    @pytest.mark.skip(reason="인증 기능 현재 비활성화 - TODO: 활성화 후 테스트")
    def test_tc_auth_002_login_failure_wrong_password(self, test_user):
        """
        TC-AUTH-002: 로그인 실패 (잘못된 비밀번호)

        테스트 단계:
        1. 로그인 페이지로 이동
        2. 유효한 사용자명 입력
        3. 잘못된 비밀번호 입력
        4. 로그인 버튼 클릭

        예상 결과:
        - 로그인 실패 에러 메시지 표시
        - 로그인 페이지에 남아있음
        """
        # Given: 로그인 페이지에 있음
        self.login_page.navigate()

        # When: 잘못된 비밀번호로 로그인 시도
        self.login_page.login(test_user["username"], "WrongPassword123!")

        # Then: 에러 메시지 표시
        error_message = self.login_page.get_error_message()
        assert error_message is not None, "에러 메시지가 표시되지 않음"
        assert "/login" in self.driver.current_url, "로그인 페이지에 남아있지 않음"

    @pytest.mark.skip(reason="인증 기능 현재 비활성화 - TODO: 활성화 후 테스트")
    def test_tc_auth_003_logout(self, test_user):
        """
        TC-AUTH-003: 로그아웃

        사전조건:
        - 로그인된 상태

        테스트 단계:
        1. 대시보드에서 로그아웃 버튼 클릭

        예상 결과:
        - 로그인 페이지로 리다이렉트됨
        """
        # Given: 로그인된 상태
        self.login_page.navigate()
        self.login_page.login(test_user["username"], test_user["password"])
        self.login_page.wait_for_login_complete()

        # When: 로그아웃
        self.dashboard_page.click_logout()

        # Then: 로그인 페이지로 이동
        self.dashboard_page.wait_for_url_contains("/login", timeout=10)
        assert "/login" in self.driver.current_url

    def test_tc_auth_004_dashboard_without_login(self):
        """
        TC-AUTH-004: 비로그인 상태 대시보드 접근

        현재 상태:
        - 인증이 비활성화되어 있어 바로 접근 가능

        테스트 단계:
        1. 비로그인 상태로 대시보드 접근

        예상 결과 (현재):
        - 대시보드에 접근 가능 (인증 비활성화 상태)

        예상 결과 (인증 활성화 후):
        - 로그인 페이지로 리다이렉트됨
        """
        # Given: 비로그인 상태

        # When: 대시보드 접근
        self.dashboard_page.navigate()

        # Then: 현재는 접근 가능 (인증 비활성화 상태)
        # TODO: 인증 활성화 후 아래 assertion으로 변경
        # assert "/login" in self.driver.current_url
        assert (
            self.dashboard_page.is_loaded()
        ), "대시보드 로드 실패 (인증 비활성화 상태에서)"
