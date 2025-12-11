"""
대시보드 페이지 POM (Page Object Model)
"""
from selenium.webdriver.common.by import By
from base_page import BasePage


class DashboardPage(BasePage):
    """대시보드 페이지 객체"""
    
    # Locators
    USER_PROFILE_ICON = (By.ID, "user_profile_icon")
    LOGOUT_BUTTON = (By.ID, "logout_button")
    WELCOME_MESSAGE = (By.CLASS_NAME, "welcome_message")
    DEVICE_LIST = (By.CLASS_NAME, "device_item")
    ADD_DEVICE_BUTTON = (By.ID, "add_device_button")
    SETTINGS_LINK = (By.LINK_TEXT, "Settings")
    NOTIFICATION_BADGE = (By.CLASS_NAME, "notification_badge")
    
    # URL
    URL = "http://localhost:3000/dashboard"
    
    def __init__(self, driver):
        super().__init__(driver)
    
    def navigate_to_dashboard(self) -> None:
        """대시보드로 이동"""
        self.driver.get(self.URL)
    
    def get_welcome_message(self) -> str:
        """환영 메시지 가져오기"""
        return self.get_text(self.WELCOME_MESSAGE)
    
    def get_device_count(self) -> int:
        """기기 개수 가져오기"""
        devices = self.find_elements(self.DEVICE_LIST)
        return len(devices)
    
    def click_add_device_button(self) -> None:
        """기기 추가 버튼 클릭"""
        self.click(self.ADD_DEVICE_BUTTON)
    
    def click_settings_link(self) -> None:
        """설정 링크 클릭"""
        self.click(self.SETTINGS_LINK)
    
    def click_user_profile_icon(self) -> None:
        """사용자 프로필 아이콘 클릭"""
        self.click(self.USER_PROFILE_ICON)
    
    def click_logout_button(self) -> None:
        """로그아웃 버튼 클릭"""
        self.click(self.LOGOUT_BUTTON)
    
    def get_notification_count(self) -> int:
        """알림 개수 가져오기"""
        badge_text = self.get_text(self.NOTIFICATION_BADGE)
        return int(badge_text) if badge_text else 0
    
    def logout(self) -> None:
        """로그아웃"""
        self.click_user_profile_icon()
        self.click_logout_button()
    
    def is_dashboard_loaded(self) -> bool:
        """대시보드 로드 확인"""
        return self.is_element_visible(self.WELCOME_MESSAGE)
