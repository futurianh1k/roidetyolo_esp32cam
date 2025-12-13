"""
Dashboard Page Object
"""

from selenium.webdriver.common.by import By
from .base_page import BasePage


class DashboardPage(BasePage):
    """대시보드 페이지"""

    # Locators
    PAGE_TITLE = (By.XPATH, "//h1[contains(text(), 'Core S3 Management')]")
    USER_INFO = (By.CSS_SELECTOR, ".text-sm.text-gray-600")

    # 버튼
    REGISTER_DEVICE_BTN = (By.XPATH, "//button[contains(text(), '장비 등록')]")
    DELETE_DEVICE_BTN = (By.XPATH, "//button[contains(text(), '장비 삭제')]")
    REFRESH_BTN = (By.XPATH, "//button[contains(text(), '새로고침')]")
    LOGOUT_BTN = (By.XPATH, "//button[contains(text(), '로그아웃')]")

    # 통계
    STATS_TOTAL = (By.XPATH, "//*[contains(text(), '전체 장비')]//following-sibling::*")
    STATS_ONLINE = (By.XPATH, "//*[contains(text(), '온라인')]//following-sibling::*")
    STATS_OFFLINE = (
        By.XPATH,
        "//*[contains(text(), '오프라인')]//following-sibling::*",
    )

    # 장비 목록
    DEVICE_CARDS = (By.CSS_SELECTOR, "[class*='grid'] > div")
    DEVICE_CARD_LINK = (By.CSS_SELECTOR, "[class*='cursor-pointer'], [onclick]")
    EMPTY_STATE = (By.XPATH, "//*[contains(text(), '등록된 장비가 없습니다')]")

    # 모달
    REGISTER_MODAL = (By.CSS_SELECTOR, "[role='dialog'], .fixed.inset-0")
    DELETE_MODAL = (By.CSS_SELECTOR, "[role='dialog'], .fixed.inset-0")
    MODAL_CLOSE_BTN = (By.CSS_SELECTOR, "button[aria-label='Close'], button:has(svg)")

    # 장비 등록 모달 필드
    DEVICE_ID_INPUT = (
        By.CSS_SELECTOR,
        "input[name='device_id'], input[placeholder*='장비 ID']",
    )
    DEVICE_NAME_INPUT = (
        By.CSS_SELECTOR,
        "input[name='device_name'], input[placeholder*='장비 이름']",
    )
    DEVICE_TYPE_SELECT = (By.CSS_SELECTOR, "select[name='device_type']")
    IP_ADDRESS_INPUT = (
        By.CSS_SELECTOR,
        "input[name='ip_address'], input[placeholder*='IP']",
    )
    LOCATION_INPUT = (
        By.CSS_SELECTOR,
        "input[name='location'], input[placeholder*='위치']",
    )
    SUBMIT_BTN = (By.CSS_SELECTOR, "button[type='submit']")

    # 토스트 메시지
    TOAST_SUCCESS = (By.CSS_SELECTOR, "[role='status']")
    TOAST_ERROR = (By.CSS_SELECTOR, ".toast-error, [role='alert']")

    def __init__(self, driver, base_url="http://localhost:3000"):
        super().__init__(driver, base_url)
        self.path = "/dashboard"

    def navigate(self):
        """대시보드로 이동"""
        self.navigate_to(self.path)
        self.wait_for_loading_complete()
        return self

    def is_loaded(self):
        """페이지 로드 확인"""
        return self.is_element_present(*self.PAGE_TITLE, timeout=5)

    def get_page_heading(self):
        """페이지 제목 가져오기"""
        return self.get_text(*self.PAGE_TITLE)

    def get_user_info(self):
        """사용자 정보 가져오기"""
        return self.get_text(*self.USER_INFO)

    # === 통계 관련 ===
    def get_total_devices_count(self):
        """전체 장비 수"""
        text = self.get_text(*self.STATS_TOTAL)
        return int(text) if text.isdigit() else 0

    def get_online_devices_count(self):
        """온라인 장비 수"""
        text = self.get_text(*self.STATS_ONLINE)
        return int(text) if text.isdigit() else 0

    def get_offline_devices_count(self):
        """오프라인 장비 수"""
        text = self.get_text(*self.STATS_OFFLINE)
        return int(text) if text.isdigit() else 0

    # === 장비 목록 ===
    def get_device_cards(self):
        """장비 카드 목록"""
        if self.is_element_present(*self.DEVICE_CARDS):
            return self.driver.find_elements(*self.DEVICE_CARDS)
        return []

    def get_device_count(self):
        """표시된 장비 수"""
        return len(self.get_device_cards())

    def is_empty_state_visible(self):
        """빈 상태 표시 여부"""
        return self.is_element_visible(*self.EMPTY_STATE, timeout=3)

    def click_device_card(self, index=0):
        """장비 카드 클릭"""
        cards = self.get_device_cards()
        if index < len(cards):
            cards[index].click()
        return self

    # === 버튼 액션 ===
    def click_register_device(self):
        """장비 등록 버튼 클릭"""
        self.click(*self.REGISTER_DEVICE_BTN)
        return self

    def click_delete_device(self):
        """장비 삭제 버튼 클릭"""
        self.click(*self.DELETE_DEVICE_BTN)
        return self

    def click_refresh(self):
        """새로고침 버튼 클릭"""
        self.click(*self.REFRESH_BTN)
        return self

    def click_logout(self):
        """로그아웃 버튼 클릭"""
        self.click(*self.LOGOUT_BTN)
        return self

    # === 장비 등록 모달 ===
    def is_register_modal_open(self):
        """등록 모달 열림 확인"""
        return self.is_element_visible(*self.REGISTER_MODAL, timeout=3)

    def fill_device_form(
        self, device_id, device_name, device_type="camera", ip_address="", location=""
    ):
        """장비 등록 폼 작성"""
        self.type_text(*self.DEVICE_ID_INPUT, device_id)
        self.type_text(*self.DEVICE_NAME_INPUT, device_name)

        if device_type:
            select = self.wait_for_element(*self.DEVICE_TYPE_SELECT)
            select.send_keys(device_type)

        if ip_address:
            self.type_text(*self.IP_ADDRESS_INPUT, ip_address)

        if location:
            self.type_text(*self.LOCATION_INPUT, location)

        return self

    def submit_device_form(self):
        """장비 등록 폼 제출"""
        self.click(*self.SUBMIT_BTN)
        return self

    def register_device(self, device_id, device_name, **kwargs):
        """장비 등록 전체 플로우"""
        self.click_register_device()
        self.fill_device_form(device_id, device_name, **kwargs)
        self.submit_device_form()
        return self

    # === 토스트 메시지 ===
    def is_success_toast_visible(self):
        """성공 토스트 표시 여부"""
        return self.is_element_visible(*self.TOAST_SUCCESS, timeout=5)

    def get_toast_message(self):
        """토스트 메시지 내용"""
        if self.is_element_visible(*self.TOAST_SUCCESS, timeout=3):
            return self.get_text(*self.TOAST_SUCCESS)
        return None
