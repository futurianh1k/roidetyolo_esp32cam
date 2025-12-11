"""
POM을 사용한 테스트 예제
"""
import pytest
import sys
from pathlib import Path

# 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from config import DriverFactory, TestConfig
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from pages.settings_page import SettingsPage
from pom_analyzer import POMAnalyzer


class TestLogin:
    """로그인 테스트"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """테스트 전후 설정"""
        self.driver = DriverFactory.create_driver(TestConfig.BROWSER)
        yield
        DriverFactory.close_driver(self.driver)
    
    def test_successful_login(self):
        """성공적인 로그인"""
        login_page = LoginPage(self.driver)
        login_page.navigate_to_login_page()
        
        assert login_page.is_login_page_loaded(), "로그인 페이지가 로드되지 않음"
        
        login_page.login(TestConfig.TEST_USERNAME, TestConfig.TEST_PASSWORD)
        
        # 대시보드로 이동 확인
        dashboard_page = DashboardPage(self.driver)
        assert dashboard_page.is_dashboard_loaded(), "대시보드로 이동하지 않음"
    
    def test_invalid_login(self):
        """잘못된 로그인"""
        login_page = LoginPage(self.driver)
        login_page.navigate_to_login_page()
        
        login_page.login("invaliduser", "wrongpassword")
        
        assert login_page.is_error_message_visible(), "에러 메시지가 표시되지 않음"
        error_msg = login_page.get_error_message()
        assert "잘못" in error_msg or "실패" in error_msg, f"예상치 못한 에러 메시지: {error_msg}"
    
    def test_empty_fields_login(self):
        """빈 필드로 로그인"""
        login_page = LoginPage(self.driver)
        login_page.navigate_to_login_page()
        
        login_page.click_login_button()
        
        assert login_page.is_error_message_visible(), "유효성 검사 에러가 표시되지 않음"


class TestDashboard:
    """대시보드 테스트"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """테스트 전후 설정"""
        self.driver = DriverFactory.create_driver(TestConfig.BROWSER)
        yield
        DriverFactory.close_driver(self.driver)
    
    def test_dashboard_elements(self):
        """대시보드 요소 확인"""
        dashboard_page = DashboardPage(self.driver)
        dashboard_page.navigate_to_dashboard()
        
        assert dashboard_page.is_dashboard_loaded(), "대시보드가 로드되지 않음"
        
        welcome_msg = dashboard_page.get_welcome_message()
        assert welcome_msg, "환영 메시지가 없음"
        
        device_count = dashboard_page.get_device_count()
        assert device_count >= 0, f"유효하지 않은 기기 개수: {device_count}"


class TestSettings:
    """설정 페이지 테스트"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """테스트 전후 설정"""
        self.driver = DriverFactory.create_driver(TestConfig.BROWSER)
        yield
        DriverFactory.close_driver(self.driver)
    
    def test_update_profile(self):
        """프로필 업데이트"""
        settings_page = SettingsPage(self.driver)
        settings_page.navigate_to_settings()
        
        assert settings_page.is_settings_page_loaded(), "설정 페이지가 로드되지 않음"
        
        settings_page.click_account_tab()
        settings_page.update_full_name("Test User")
        settings_page.update_email("test@example.com")
        settings_page.save_changes()
        
        success_msg = settings_page.get_success_message()
        assert "성공" in success_msg or "저장" in success_msg, "성공 메시지가 없음"


class TestPOMAnalysis:
    """POM 분석 테스트"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """테스트 전후 설정"""
        self.driver = DriverFactory.create_driver(TestConfig.BROWSER)
        yield
        DriverFactory.close_driver(self.driver)
    
    def test_analyze_login_page(self):
        """로그인 페이지 분석"""
        login_page = LoginPage(self.driver)
        login_page.navigate_to_login_page()
        
        analyzer = POMAnalyzer(self.driver)
        results = analyzer.analyze_page_elements("LoginPage")
        
        assert results["url"], "URL이 없음"
        assert results["elements"], "요소가 없음"
        assert len(results["inputs"]) > 0, "입력 필드가 없음"
        assert len(results["buttons"]) > 0, "버튼이 없음"
    
    def test_generate_pom_code(self):
        """POM 코드 자동 생성"""
        login_page = LoginPage(self.driver)
        login_page.navigate_to_login_page()
        
        analyzer = POMAnalyzer(self.driver)
        analyzer.analyze_page_elements("LoginPage")
        
        pom_code = analyzer.generate_pom_code("LoginPage", "LoginPage")
        
        assert "class LoginPage" in pom_code, "클래스 정의가 없음"
        assert "Locators" in pom_code, "로케이터 섹션이 없음"
        
        # 코드 파일로 저장
        output_file = Path(__file__).parent / "generated" / "login_page_generated.py"
        output_file.parent.mkdir(exist_ok=True)
        output_file.write_text(pom_code, encoding='utf-8')
    
    def test_find_interactive_elements(self):
        """상호작용 요소 찾기"""
        login_page = LoginPage(self.driver)
        login_page.navigate_to_login_page()
        
        analyzer = POMAnalyzer(self.driver)
        interactive = analyzer.find_interactive_elements()
        
        assert "buttons" in interactive, "버튼 정보가 없음"
        assert "inputs" in interactive, "입력 정보가 없음"
        assert "links" in interactive, "링크 정보가 없음"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
