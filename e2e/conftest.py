"""
E2E 테스트 Pytest 설정 및 Fixtures
"""

import os
import pytest
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 기본 설정
BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:3000")
BACKEND_URL = os.getenv("E2E_BACKEND_URL", "http://localhost:8000")
HEADLESS = os.getenv("E2E_HEADLESS", "true").lower() == "true"
SLOW_MODE = os.getenv("E2E_SLOW_MODE", "false").lower() == "true"
SCREENSHOT_DIR = os.getenv("E2E_SCREENSHOT_DIR", "screenshots")

# 테스트 사용자 정보
TEST_USERNAME = os.getenv("E2E_TEST_USERNAME", "testuser")
TEST_PASSWORD = os.getenv("E2E_TEST_PASSWORD", "TestPassword123!")


def pytest_configure(config):
    """Pytest 설정"""
    # 스크린샷 디렉토리 생성
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)


@pytest.fixture(scope="session")
def driver_options():
    """Chrome 드라이버 옵션"""
    options = Options()

    if HEADLESS:
        options.add_argument("--headless=new")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--lang=ko-KR")

    # 한국어 설정
    prefs = {
        "intl.accept_languages": "ko,ko-KR,en-US,en",
    }
    options.add_experimental_option("prefs", prefs)

    return options


@pytest.fixture(scope="function")
def driver(driver_options):
    """Selenium WebDriver 인스턴스"""
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=driver_options)
    driver.implicitly_wait(10)  # 암시적 대기

    yield driver

    driver.quit()


@pytest.fixture(scope="function")
def slow_driver(driver):
    """느린 모드 드라이버 (디버깅용)"""
    if SLOW_MODE:
        import time

        original_get = driver.get

        def slow_get(url):
            original_get(url)
            time.sleep(1)

        driver.get = slow_get

    return driver


@pytest.fixture
def base_url():
    """프론트엔드 기본 URL"""
    return BASE_URL


@pytest.fixture
def backend_url():
    """백엔드 API URL"""
    return BACKEND_URL


@pytest.fixture
def test_user():
    """테스트 사용자 정보"""
    return {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD,
    }


@pytest.fixture
def screenshot_on_failure(request, driver):
    """테스트 실패 시 스크린샷 저장"""
    yield

    if request.node.rep_call.failed:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_name = request.node.name
        screenshot_path = os.path.join(
            SCREENSHOT_DIR, f"failure_{test_name}_{timestamp}.png"
        )
        driver.save_screenshot(screenshot_path)
        print(f"\n스크린샷 저장: {screenshot_path}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """테스트 결과 리포트 후킹 (스크린샷용)"""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
