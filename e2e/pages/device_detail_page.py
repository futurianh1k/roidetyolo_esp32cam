"""
Device Detail Page Object
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from .base_page import BasePage


class DeviceDetailPage(BasePage):
    """장비 상세 페이지"""

    # Locators - 헤더
    BACK_BUTTON = (By.CSS_SELECTOR, "button:has(svg[class*='arrow'])")
    DEVICE_NAME = (By.CSS_SELECTOR, "h1")
    DEVICE_ID_TEXT = (By.CSS_SELECTOR, ".text-sm.text-gray-600")
    ONLINE_STATUS = (By.XPATH, "//*[contains(@class, 'bg-green-100')]")
    OFFLINE_STATUS = (By.XPATH, "//*[contains(@class, 'bg-gray-100')]")

    # 버튼
    RESTART_BTN = (By.XPATH, "//button[contains(text(), '재시작')]")
    REFRESH_BTN = (By.XPATH, "//button[contains(text(), '새로고침')]")
    DELETE_BTN = (By.XPATH, "//button[contains(text(), '삭제')]")

    # 장비 정보 섹션
    IP_ADDRESS_DISPLAY = (By.CSS_SELECTOR, ".bg-gray-50.border-gray-200")
    IP_EDIT_BTN = (By.CSS_SELECTOR, "button:has(svg)")
    IP_INPUT = (By.CSS_SELECTOR, "input[placeholder*='192.168']")
    IP_SAVE_BTN = (By.CSS_SELECTOR, "button.bg-green-600")
    IP_CANCEL_BTN = (By.CSS_SELECTOR, "button.bg-gray-200")

    # 카메라 제어
    CAMERA_SECTION = (By.XPATH, "//h2[contains(text(), '카메라 제어')]")
    CAMERA_START_BTN = (
        By.XPATH,
        "//div[contains(.//h2, '카메라')]//button[contains(text(), '시작')]",
    )
    CAMERA_PAUSE_BTN = (
        By.XPATH,
        "//div[contains(.//h2, '카메라')]//button[contains(text(), '일시정지')]",
    )
    CAMERA_STOP_BTN = (
        By.XPATH,
        "//div[contains(.//h2, '카메라')]//button[contains(text(), '정지')]",
    )
    SINK_URL_INPUT = (By.CSS_SELECTOR, "input[placeholder*='http://']")

    # 마이크 제어
    MIC_SECTION = (By.XPATH, "//h2[contains(text(), '마이크 제어')]")
    MIC_START_BTN = (
        By.XPATH,
        "//div[contains(.//h2, '마이크')]//button[contains(text(), '시작')]",
    )
    MIC_STOP_BTN = (
        By.XPATH,
        "//div[contains(.//h2, '마이크')]//button[contains(text(), '정지')]",
    )
    MIC_WS_URL_INPUT = (By.CSS_SELECTOR, "input[placeholder*='ws://']")

    # 스피커 제어
    SPEAKER_SECTION = (By.XPATH, "//h2[contains(text(), '스피커 제어')]")
    SPEAKER_PLAY_BTN = (
        By.XPATH,
        "//div[contains(.//h2, '스피커')]//button[contains(text(), '재생')]",
    )
    SPEAKER_STOP_BTN = (
        By.XPATH,
        "//div[contains(.//h2, '스피커')]//button[contains(text(), '정지')]",
    )
    AUDIO_FILE_SELECT = (By.CSS_SELECTOR, "select")
    VOLUME_SLIDER = (By.CSS_SELECTOR, "input[type='range']")
    FILE_UPLOAD_INPUT = (By.CSS_SELECTOR, "input[type='file']")

    # 디스플레이 제어
    DISPLAY_SECTION = (By.XPATH, "//h2[contains(text(), '디스플레이 제어')]")
    DISPLAY_TEXT_INPUT = (By.CSS_SELECTOR, "input[placeholder*='표시할 텍스트']")
    DISPLAY_SHOW_TEXT_BTN = (By.XPATH, "//button[contains(text(), '텍스트 표시')]")
    DISPLAY_SHOW_EMOJI_BTN = (By.XPATH, "//button[contains(text(), '이모티콘 표시')]")
    DISPLAY_CLEAR_BTN = (By.XPATH, "//button[contains(text(), '화면 지우기')]")
    EMOJI_BUTTONS = (By.CSS_SELECTOR, "button.text-2xl")

    # 음성인식
    ASR_SECTION = (By.XPATH, "//h3[contains(text(), '음성인식')]")
    ASR_START_BTN = (By.XPATH, "//button[contains(text(), '음성인식 시작')]")
    ASR_STOP_BTN = (By.XPATH, "//button[contains(text(), '음성인식 종료')]")
    ASR_LANGUAGE_SELECT = (By.CSS_SELECTOR, "select")
    ASR_VAD_CHECKBOX = (By.CSS_SELECTOR, "input[type='checkbox']")
    ASR_CONNECTION_STATUS = (
        By.CSS_SELECTOR,
        ".text-green-600, .text-yellow-600, .text-red-600",
    )

    # 인식 결과 창
    RECOGNITION_WINDOW = (By.XPATH, "//*[contains(text(), '인식 결과')]")
    RECOGNITION_CLEAR_BTN = (By.XPATH, "//button[contains(text(), '지우기')]")

    # 상태
    DEVICE_STATUS_SECTION = (By.XPATH, "//h2[contains(text(), '장비 상태')]")

    # 토스트
    TOAST_MESSAGE = (By.CSS_SELECTOR, "[role='status'], [role='alert']")

    # 오프라인 경고
    OFFLINE_WARNING = (By.XPATH, "//*[contains(text(), '오프라인 상태')]")

    def __init__(self, driver, base_url="http://localhost:3000"):
        super().__init__(driver, base_url)

    def navigate(self, device_id):
        """장비 상세 페이지로 이동"""
        self.navigate_to(f"/devices/{device_id}")
        self.wait_for_loading_complete()
        return self

    def is_loaded(self):
        """페이지 로드 확인"""
        return self.is_element_present(*self.DEVICE_NAME, timeout=5)

    # === 기본 정보 ===
    def get_device_name(self):
        """장비 이름"""
        return self.get_text(*self.DEVICE_NAME)

    def is_online(self):
        """온라인 상태 확인"""
        return self.is_element_visible(*self.ONLINE_STATUS, timeout=3)

    def is_offline(self):
        """오프라인 상태 확인"""
        return self.is_element_visible(*self.OFFLINE_STATUS, timeout=3)

    def is_offline_warning_visible(self):
        """오프라인 경고 표시 여부"""
        return self.is_element_visible(*self.OFFLINE_WARNING, timeout=3)

    # === 네비게이션 ===
    def click_back(self):
        """뒤로가기"""
        self.click(*self.BACK_BUTTON)
        return self

    def click_refresh(self):
        """새로고침"""
        self.click(*self.REFRESH_BTN)
        return self

    def click_restart(self):
        """재시작"""
        self.click(*self.RESTART_BTN)
        return self

    def click_delete(self):
        """삭제"""
        self.click(*self.DELETE_BTN)
        return self

    # === IP 주소 편집 ===
    def click_edit_ip(self):
        """IP 편집 시작"""
        self.click(*self.IP_EDIT_BTN)
        return self

    def enter_ip_address(self, ip):
        """IP 주소 입력"""
        self.type_text(*self.IP_INPUT, ip)
        return self

    def save_ip_address(self):
        """IP 저장"""
        self.click(*self.IP_SAVE_BTN)
        return self

    def cancel_ip_edit(self):
        """IP 편집 취소"""
        self.click(*self.IP_CANCEL_BTN)
        return self

    def update_ip_address(self, ip):
        """IP 주소 업데이트 전체 플로우"""
        self.click_edit_ip()
        self.enter_ip_address(ip)
        self.save_ip_address()
        return self

    # === 카메라 제어 ===
    def start_camera(self):
        """카메라 시작"""
        self.click(*self.CAMERA_START_BTN)
        return self

    def stop_camera(self):
        """카메라 정지"""
        self.click(*self.CAMERA_STOP_BTN)
        return self

    def set_sink_url(self, url):
        """Sink URL 설정"""
        self.type_text(*self.SINK_URL_INPUT, url)
        return self

    # === 마이크 제어 ===
    def start_microphone(self):
        """마이크 시작"""
        self.click(*self.MIC_START_BTN)
        return self

    def stop_microphone(self):
        """마이크 정지"""
        self.click(*self.MIC_STOP_BTN)
        return self

    # === 디스플레이 제어 ===
    def show_text_on_display(self, text):
        """디스플레이에 텍스트 표시"""
        self.type_text(*self.DISPLAY_TEXT_INPUT, text)
        self.click(*self.DISPLAY_SHOW_TEXT_BTN)
        return self

    def show_emoji_on_display(self, emoji_index=0):
        """디스플레이에 이모지 표시"""
        emojis = self.driver.find_elements(*self.EMOJI_BUTTONS)
        if emoji_index < len(emojis):
            emojis[emoji_index].click()
        self.click(*self.DISPLAY_SHOW_EMOJI_BTN)
        return self

    def clear_display(self):
        """디스플레이 지우기"""
        self.click(*self.DISPLAY_CLEAR_BTN)
        return self

    # === 음성인식 ===
    def start_asr(self):
        """음성인식 시작"""
        self.click(*self.ASR_START_BTN)
        return self

    def stop_asr(self):
        """음성인식 종료"""
        self.click(*self.ASR_STOP_BTN)
        return self

    def is_asr_start_button_visible(self):
        """시작 버튼 표시 여부"""
        return self.is_element_visible(*self.ASR_START_BTN, timeout=3)

    def is_asr_stop_button_visible(self):
        """종료 버튼 표시 여부"""
        return self.is_element_visible(*self.ASR_STOP_BTN, timeout=3)

    # === 토스트 ===
    def get_toast_message(self):
        """토스트 메시지 가져오기"""
        if self.is_element_visible(*self.TOAST_MESSAGE, timeout=5):
            return self.get_text(*self.TOAST_MESSAGE)
        return None

    def wait_for_toast(self, timeout=5):
        """토스트 대기"""
        self.wait_for_element_visible(*self.TOAST_MESSAGE, timeout=timeout)
        return self
