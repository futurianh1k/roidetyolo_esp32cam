"""
로그인 페이지 POM (Page Object Model)
"""
from selenium.webdriver.common.by import By
from base_page import BasePage


class LoginPage(BasePage):
    """로그인 페이지 객체"""
    
    # Locators
    USERNAME_INPUT = (By.ID, "username")
    PASSWORD_INPUT = (By.ID, "password")
    LOGIN_BUTTON = (By.ID, "login_button")
    ERROR_MESSAGE = (By.CLASS_NAME, "error_message")
    REMEMBER_ME_CHECKBOX = (By.ID, "remember_me")
    FORGOT_PASSWORD_LINK = (By.LINK_TEXT, "Forgot Password?")
    
    # URL
    URL = "http://localhost:3000/login"
    
    def __init__(self, driver):
        super().__init__(driver)
    
    def navigate_to_login_page(self) -> None:
        """로그인 페이지로 이동"""
        self.driver.get(self.URL)
    
    def enter_username(self, username: str) -> None:
        """사용자명 입력"""
        self.send_keys(self.USERNAME_INPUT, username)
    
    def enter_password(self, password: str) -> None:
        """비밀번호 입력"""
        self.send_keys(self.PASSWORD_INPUT, password)
    
    def click_login_button(self) -> None:
        """로그인 버튼 클릭"""
        self.click(self.LOGIN_BUTTON)
    
    def login(self, username: str, password: str) -> None:
        """로그인 실행"""
        self.enter_username(username)
        self.enter_password(password)
        self.click_login_button()
    
    def get_error_message(self) -> str:
        """에러 메시지 가져오기"""
        return self.get_text(self.ERROR_MESSAGE)
    
    def is_error_message_visible(self) -> bool:
        """에러 메시지 표시 여부"""
        return self.is_element_visible(self.ERROR_MESSAGE)
    
    def check_remember_me(self) -> None:
        """'로그인 유지' 체크박스 선택"""
        self.click(self.REMEMBER_ME_CHECKBOX)
    
    def click_forgot_password_link(self) -> None:
        """비밀번호 찾기 링크 클릭"""
        self.click(self.FORGOT_PASSWORD_LINK)
    
    def is_login_page_loaded(self) -> bool:
        """로그인 페이지 로드 확인"""
        return self.is_element_visible(self.LOGIN_BUTTON)
