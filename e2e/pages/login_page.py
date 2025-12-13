"""
Login Page Object
"""

from selenium.webdriver.common.by import By
from .base_page import BasePage


class LoginPage(BasePage):
    """로그인 페이지"""

    # Locators
    USERNAME_INPUT = (By.CSS_SELECTOR, "input[type='text'], input[name='username']")
    PASSWORD_INPUT = (By.CSS_SELECTOR, "input[type='password']")
    LOGIN_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    ERROR_MESSAGE = (By.CSS_SELECTOR, ".text-red-500, .text-red-600, [role='alert']")
    LOADING_SPINNER = (By.CSS_SELECTOR, ".animate-spin")
    PAGE_TITLE = (By.XPATH, "//h1 | //h2")

    def __init__(self, driver, base_url="http://localhost:3000"):
        super().__init__(driver, base_url)
        self.path = "/login"

    def navigate(self):
        """로그인 페이지로 이동"""
        self.navigate_to(self.path)
        self.wait_for_loading_complete()
        return self

    def is_loaded(self):
        """페이지 로드 확인"""
        return self.is_element_present(*self.LOGIN_BUTTON)

    def enter_username(self, username):
        """사용자명 입력"""
        self.type_text(*self.USERNAME_INPUT, username)
        return self

    def enter_password(self, password):
        """비밀번호 입력"""
        self.type_text(*self.PASSWORD_INPUT, password)
        return self

    def click_login(self):
        """로그인 버튼 클릭"""
        self.click(*self.LOGIN_BUTTON)
        return self

    def login(self, username, password):
        """로그인 수행"""
        self.enter_username(username)
        self.enter_password(password)
        self.click_login()
        return self

    def wait_for_login_complete(self, timeout=10):
        """로그인 완료 대기 (대시보드로 리다이렉트)"""
        self.wait_for_url_contains("/dashboard", timeout)
        return self

    def get_error_message(self):
        """에러 메시지 가져오기"""
        if self.is_element_visible(*self.ERROR_MESSAGE, timeout=3):
            return self.get_text(*self.ERROR_MESSAGE)
        return None

    def is_login_button_enabled(self):
        """로그인 버튼 활성화 여부"""
        button = self.wait_for_element(*self.LOGIN_BUTTON)
        return button.is_enabled()
