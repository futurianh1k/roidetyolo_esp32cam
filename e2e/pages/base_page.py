"""
Base Page Object - 모든 페이지의 공통 기능
"""

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException


class BasePage:
    """페이지 오브젝트 기본 클래스"""

    def __init__(self, driver, base_url="http://localhost:3000"):
        self.driver = driver
        self.base_url = base_url
        self.timeout = 10

    def navigate_to(self, path=""):
        """지정된 경로로 이동"""
        url = f"{self.base_url}{path}"
        self.driver.get(url)
        return self

    def wait_for_element(self, by, locator, timeout=None):
        """요소가 나타날 때까지 대기"""
        timeout = timeout or self.timeout
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, locator))
        )

    def wait_for_element_visible(self, by, locator, timeout=None):
        """요소가 보일 때까지 대기"""
        timeout = timeout or self.timeout
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located((by, locator))
        )

    def wait_for_element_clickable(self, by, locator, timeout=None):
        """요소가 클릭 가능할 때까지 대기"""
        timeout = timeout or self.timeout
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, locator))
        )

    def wait_for_text(self, text, timeout=None):
        """특정 텍스트가 페이지에 나타날 때까지 대기"""
        timeout = timeout or self.timeout
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//*[contains(text(), '{text}')]")
            )
        )

    def wait_for_url_contains(self, text, timeout=None):
        """URL에 특정 텍스트가 포함될 때까지 대기"""
        timeout = timeout or self.timeout
        return WebDriverWait(self.driver, timeout).until(EC.url_contains(text))

    def click(self, by, locator):
        """요소 클릭"""
        element = self.wait_for_element_clickable(by, locator)
        element.click()
        return self

    def type_text(self, by, locator, text, clear=True):
        """텍스트 입력"""
        element = self.wait_for_element(by, locator)
        if clear:
            element.clear()
        element.send_keys(text)
        return self

    def get_text(self, by, locator):
        """요소의 텍스트 가져오기"""
        element = self.wait_for_element(by, locator)
        return element.text

    def is_element_present(self, by, locator, timeout=3):
        """요소가 존재하는지 확인"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, locator))
            )
            return True
        except TimeoutException:
            return False

    def is_element_visible(self, by, locator, timeout=3):
        """요소가 보이는지 확인"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((by, locator))
            )
            return True
        except TimeoutException:
            return False

    def get_page_title(self):
        """페이지 타이틀 가져오기"""
        return self.driver.title

    def get_current_url(self):
        """현재 URL 가져오기"""
        return self.driver.current_url

    def refresh(self):
        """페이지 새로고침"""
        self.driver.refresh()
        return self

    def take_screenshot(self, name):
        """스크린샷 저장"""
        self.driver.save_screenshot(f"screenshots/{name}.png")
        return self

    def wait_for_loading_complete(self, timeout=10):
        """로딩 완료 대기 (로딩 스피너 사라질 때까지)"""
        try:
            # 로딩 스피너가 사라질 때까지 대기
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located(
                    (By.XPATH, "//*[contains(@class, 'animate-spin')]")
                )
            )
        except TimeoutException:
            pass  # 로딩 스피너가 처음부터 없을 수 있음
        return self
