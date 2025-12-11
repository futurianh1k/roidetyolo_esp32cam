"""
웹드라이버 설정 및 기본 구성
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
import os
from dotenv import load_dotenv

load_dotenv()


class DriverFactory:
    """웹드라이버 생성 팩토리"""
    
    @staticmethod
    def create_driver(browser: str = "chrome"):
        """
        웹드라이버 생성
        
        Args:
            browser: 브라우저 타입 (chrome, firefox, edge)
        
        Returns:
            WebDriver 인스턴스
        """
        if browser.lower() == "chrome":
            options = webdriver.ChromeOptions()
            # options.add_argument("--headless")  # 헤드리스 모드
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options
            )
        
        elif browser.lower() == "firefox":
            options = webdriver.FirefoxOptions()
            # options.add_argument("--headless")  # 헤드리스 모드
            
            driver = webdriver.Firefox(
                service=Service(GeckoDriverManager().install()),
                options=options
            )
        
        elif browser.lower() == "edge":
            options = webdriver.EdgeOptions()
            driver = webdriver.Edge(options=options)
        
        else:
            raise ValueError(f"Unsupported browser: {browser}")
        
        driver.implicitly_wait(10)
        driver.maximize_window()
        
        return driver
    
    @staticmethod
    def close_driver(driver) -> None:
        """웹드라이버 종료"""
        if driver:
            driver.quit()


class TestConfig:
    """테스트 설정"""
    
    # 기본 URL
    BASE_URL = os.getenv("BASE_URL", "http://localhost:3000")
    
    # 테스트 계정
    TEST_USERNAME = os.getenv("TEST_USERNAME", "testuser")
    TEST_PASSWORD = os.getenv("TEST_PASSWORD", "testpassword")
    
    # 브라우저 설정
    BROWSER = os.getenv("BROWSER", "chrome")
    
    # 대기 시간
    EXPLICIT_WAIT = 10
    IMPLICIT_WAIT = 10
    
    # 로그 설정
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    SCREENSHOT_ON_FAILURE = True
