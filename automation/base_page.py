"""
Base Page class for POM (Page Object Model) pattern
모든 페이지의 기본이 되는 클래스
"""
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from typing import Tuple, List
import time


class BasePage:
    """모든 페이지 객체의 기본 클래스"""
    
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)
        self.actions = ActionChains(self.driver)
    
    # 기본 액션 메서드
    def find_element(self, locator: Tuple[By, str]) -> WebElement:
        """요소 찾기"""
        return self.wait.until(EC.presence_of_element_located(locator))
    
    def find_elements(self, locator: Tuple[By, str]) -> List[WebElement]:
        """여러 요소 찾기"""
        return self.driver.find_elements(*locator)
    
    def click(self, locator: Tuple[By, str]) -> None:
        """클릭"""
        element = self.wait.until(EC.element_to_be_clickable(locator))
        element.click()
    
    def send_keys(self, locator: Tuple[By, str], text: str) -> None:
        """텍스트 입력"""
        element = self.find_element(locator)
        element.clear()
        element.send_keys(text)
    
    def get_text(self, locator: Tuple[By, str]) -> str:
        """텍스트 가져오기"""
        return self.find_element(locator).text
    
    def get_attribute(self, locator: Tuple[By, str], attribute: str) -> str:
        """속성값 가져오기"""
        return self.find_element(locator).get_attribute(attribute)
    
    def is_element_visible(self, locator: Tuple[By, str]) -> bool:
        """요소가 보이는지 확인"""
        try:
            self.wait.until(EC.visibility_of_element_located(locator))
            return True
        except:
            return False
    
    def is_element_present(self, locator: Tuple[By, str]) -> bool:
        """요소가 DOM에 있는지 확인"""
        try:
            self.wait.until(EC.presence_of_element_located(locator))
            return True
        except:
            return False
    
    def wait_for_element(self, locator: Tuple[By, str], timeout: int = 10) -> WebElement:
        """요소 로드 대기"""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(locator)
        )
    
    def scroll_to_element(self, locator: Tuple[By, str]) -> None:
        """요소로 스크롤"""
        element = self.find_element(locator)
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)
    
    def hover_over_element(self, locator: Tuple[By, str]) -> None:
        """요소 위에 마우스 오버"""
        element = self.find_element(locator)
        self.actions.move_to_element(element).perform()
    
    def double_click(self, locator: Tuple[By, str]) -> None:
        """더블클릭"""
        element = self.find_element(locator)
        self.actions.double_click(element).perform()
    
    def right_click(self, locator: Tuple[By, str]) -> None:
        """우클릭"""
        element = self.find_element(locator)
        self.actions.context_click(element).perform()
    
    def get_current_url(self) -> str:
        """현재 URL 가져오기"""
        return self.driver.current_url
    
    def get_page_title(self) -> str:
        """페이지 제목 가져오기"""
        return self.driver.title
    
    def switch_to_frame(self, locator: Tuple[By, str]) -> None:
        """iframe으로 전환"""
        frame = self.find_element(locator)
        self.driver.switch_to.frame(frame)
    
    def switch_to_default_content(self) -> None:
        """기본 콘텐츠로 복귀"""
        self.driver.switch_to.default_content()
    
    def accept_alert(self) -> None:
        """알림 창 수락"""
        self.wait.until(EC.alert_is_present())
        self.driver.switch_to.alert.accept()
    
    def dismiss_alert(self) -> None:
        """알림 창 취소"""
        self.wait.until(EC.alert_is_present())
        self.driver.switch_to.alert.dismiss()
