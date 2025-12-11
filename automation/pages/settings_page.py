"""
설정 페이지 POM (Page Object Model)
"""
from selenium.webdriver.common.by import By
from base_page import BasePage


class SettingsPage(BasePage):
    """설정 페이지 객체"""
    
    # Locators
    ACCOUNT_TAB = (By.ID, "account_tab")
    SECURITY_TAB = (By.ID, "security_tab")
    NOTIFICATIONS_TAB = (By.ID, "notifications_tab")
    
    # Account settings
    FULL_NAME_INPUT = (By.ID, "full_name")
    EMAIL_INPUT = (By.ID, "email")
    SAVE_CHANGES_BUTTON = (By.ID, "save_changes_button")
    SUCCESS_MESSAGE = (By.CLASS_NAME, "success_message")
    
    # Security settings
    CURRENT_PASSWORD_INPUT = (By.ID, "current_password")
    NEW_PASSWORD_INPUT = (By.ID, "new_password")
    CONFIRM_PASSWORD_INPUT = (By.ID, "confirm_password")
    CHANGE_PASSWORD_BUTTON = (By.ID, "change_password_button")
    
    # Notification settings
    EMAIL_NOTIFICATIONS_CHECKBOX = (By.ID, "email_notifications")
    PUSH_NOTIFICATIONS_CHECKBOX = (By.ID, "push_notifications")
    
    # URL
    URL = "http://localhost:3000/settings"
    
    def __init__(self, driver):
        super().__init__(driver)
    
    def navigate_to_settings(self) -> None:
        """설정 페이지로 이동"""
        self.driver.get(self.URL)
    
    # Account tab methods
    def click_account_tab(self) -> None:
        """계정 탭 클릭"""
        self.click(self.ACCOUNT_TAB)
    
    def update_full_name(self, full_name: str) -> None:
        """전체 이름 업데이트"""
        self.send_keys(self.FULL_NAME_INPUT, full_name)
    
    def update_email(self, email: str) -> None:
        """이메일 업데이트"""
        self.send_keys(self.EMAIL_INPUT, email)
    
    def save_changes(self) -> None:
        """변경사항 저장"""
        self.click(self.SAVE_CHANGES_BUTTON)
    
    def get_success_message(self) -> str:
        """성공 메시지 가져오기"""
        return self.get_text(self.SUCCESS_MESSAGE)
    
    # Security tab methods
    def click_security_tab(self) -> None:
        """보안 탭 클릭"""
        self.click(self.SECURITY_TAB)
    
    def change_password(self, current_pwd: str, new_pwd: str, confirm_pwd: str) -> None:
        """비밀번호 변경"""
        self.send_keys(self.CURRENT_PASSWORD_INPUT, current_pwd)
        self.send_keys(self.NEW_PASSWORD_INPUT, new_pwd)
        self.send_keys(self.CONFIRM_PASSWORD_INPUT, confirm_pwd)
        self.click(self.CHANGE_PASSWORD_BUTTON)
    
    # Notification tab methods
    def click_notifications_tab(self) -> None:
        """알림 탭 클릭"""
        self.click(self.NOTIFICATIONS_TAB)
    
    def enable_email_notifications(self) -> None:
        """이메일 알림 활성화"""
        element = self.find_element(self.EMAIL_NOTIFICATIONS_CHECKBOX)
        if not element.is_selected():
            self.click(self.EMAIL_NOTIFICATIONS_CHECKBOX)
    
    def disable_email_notifications(self) -> None:
        """이메일 알림 비활성화"""
        element = self.find_element(self.EMAIL_NOTIFICATIONS_CHECKBOX)
        if element.is_selected():
            self.click(self.EMAIL_NOTIFICATIONS_CHECKBOX)
    
    def is_settings_page_loaded(self) -> bool:
        """설정 페이지 로드 확인"""
        return self.is_element_visible(self.ACCOUNT_TAB)
