# POM (Page Object Model) 분석 도구 사용 가이드

## 📋 개요

이 프로젝트는 Selenium과 Python을 사용하여 웹 사이트의 **Page Object Model (POM)** 패턴을 구현하고 분석하는 도구입니다.

## 🏗️ 프로젝트 구조

```
automation/
├── base_page.py              # 모든 페이지의 기본 클래스
├── config.py                 # 설정 및 드라이버 팩토리
├── pom_analyzer.py           # POM 분석 및 코드 생성
├── analyze.py                # 단독 실행 분석 스크립트
├── pages/                    # 페이지 객체 모음
│   ├── login_page.py        # 로그인 페이지 POM
│   ├── dashboard_page.py    # 대시보드 페이지 POM
│   └── settings_page.py     # 설정 페이지 POM
├── tests/                    # 테스트 파일
│   └── test_pom.py          # POM 테스트
└── requirements.txt          # 의존성
```

## 🚀 설치 및 실행

### 1. 의존성 설치

```bash
cd automation
pip install -r requirements.txt
```

### 2. 환경 변수 설정 (.env 파일)

```
BASE_URL=http://localhost:3000
TEST_USERNAME=testuser
TEST_PASSWORD=testpassword
BROWSER=chrome
LOG_LEVEL=INFO
```

### 3. 분석 실행

#### 방법 1: 단독 스크립트 실행
```bash
python analyze.py
```

결과 파일:
- `reports/login_analysis.json` - 분석 결과 (JSON)
- `reports/login_pom.py` - 자동 생성 POM 코드

#### 방법 2: Pytest로 테스트 실행
```bash
pytest tests/test_pom.py -v -s
```

#### 방법 3: 특정 테스트만 실행
```bash
pytest tests/test_pom.py::TestLogin::test_successful_login -v
```

## 📖 기본 개념

### Page Object Model이란?

POM은 웹 페이지를 객체로 표현하는 설계 패턴입니다:

```python
# ❌ POM 없이 (안티 패턴)
driver.find_element(By.ID, "username").send_keys("user")
driver.find_element(By.ID, "password").send_keys("pwd")
driver.find_element(By.ID, "login_btn").click()

# ✓ POM 사용 (권장)
login_page = LoginPage(driver)
login_page.login("user", "pwd")
```

**장점:**
- 유지보수 용이
- 코드 재사용
- 테스트 가독성 향상
- 요소 로케이터 중앙 관리

### BasePage 클래스

모든 페이지의 기본이 되는 클래스로, 공통 메서드 제공:

```python
# 요소 찾기
element = page.find_element(locator)

# 클릭
page.click(locator)

# 텍스트 입력
page.send_keys(locator, "text")

# 텍스트 가져오기
text = page.get_text(locator)

# 요소 표시 확인
if page.is_element_visible(locator):
    print("요소가 보입니다")

# 스크롤
page.scroll_to_element(locator)

# 마우스 오버
page.hover_over_element(locator)
```

## 💻 사용 예제

### 1. 페이지 객체 만들기

```python
from selenium.webdriver.common.by import By
from base_page import BasePage

class MyPage(BasePage):
    # 로케이터 정의
    USERNAME_INPUT = (By.ID, "username")
    LOGIN_BUTTON = (By.ID, "login_btn")
    ERROR_MSG = (By.CLASS_NAME, "error")
    
    def __init__(self, driver):
        super().__init__(driver)
    
    def login(self, username, password):
        self.send_keys(self.USERNAME_INPUT, username)
        self.click(self.LOGIN_BUTTON)
```

### 2. 테스트 작성

```python
def test_login(driver):
    page = LoginPage(driver)
    page.navigate_to_login_page()
    page.login("testuser", "testpass")
    
    assert page.is_dashboard_loaded()
```

### 3. 페이지 분석

```python
from pom_analyzer import POMAnalyzer

driver = DriverFactory.create_driver("chrome")
driver.get("http://example.com")

analyzer = POMAnalyzer(driver)
results = analyzer.analyze_page_elements("ExamplePage")

# 모든 입력 필드 찾기
print(results["inputs"])

# 모든 버튼 찾기
print(results["buttons"])

# 상호작용 요소 찾기
interactive = analyzer.find_interactive_elements()
print(interactive["buttons"])
print(interactive["inputs"])
```

## 🔍 POM Analyzer 기능

### 페이지 분석
```python
analyzer = POMAnalyzer(driver)
results = analyzer.analyze_page_elements("PageName")

# 결과 구조
{
    "page_name": "PageName",
    "timestamp": "2024-01-01T12:00:00",
    "url": "http://example.com",
    "title": "Page Title",
    "elements": [...],      # 모든 요소
    "inputs": [...],        # 입력 필드
    "buttons": [...],       # 버튼
    "links": [...],         # 링크
    "images": [...]         # 이미지
}
```

### JSON 내보내기
```python
analyzer.export_analysis_to_json("analysis.json")
```

### POM 코드 자동 생성
```python
pom_code = analyzer.generate_pom_code("PageName", "PageName")
```

### 상호작용 요소 찾기
```python
interactive = analyzer.find_interactive_elements()
# {
#     "buttons": [...],
#     "links": [...],
#     "inputs": [...],
#     "checkboxes": [...],
#     "radio_buttons": [...],
#     "selects": [...]
# }
```

## 📊 리포트 생성

분석 결과는 자동으로 `reports/` 디렉토리에 저장됩니다:

- `*.json` - 분석 데이터 (JSON 형식)
- `*_pom.py` - 자동 생성된 POM 코드

## 🔧 설정 커스터마이징

[config.py](config.py)에서 설정 변경:

```python
# 브라우저 선택
BROWSER = "chrome"  # chrome, firefox, edge

# 기본 대기 시간
EXPLICIT_WAIT = 10
IMPLICIT_WAIT = 10

# 헤드리스 모드 (선택적)
options.add_argument("--headless")
```

## 🎯 Best Practices

### 1. 로케이터는 상수로 정의
```python
class LoginPage(BasePage):
    USERNAME = (By.ID, "username")      # ✓ 좋음
    
    def enter_username(self, text):
        self.send_keys(self.USERNAME, text)
```

### 2. 메서드는 비즈니스 로직으로 명명
```python
# ❌ 나쁜 예
page.click(LOGIN_BUTTON)
page.send_keys(USERNAME_INPUT, "user")

# ✓ 좋은 예
page.login("user", "password")
```

### 3. 명시적 대기 사용
```python
# ❌ 안티 패턴
time.sleep(5)

# ✓ 명시적 대기
element = self.wait_for_element(locator, timeout=10)
```

### 4. 요소 선택자 우선순위
1. ID
2. Name
3. CSS Selector
4. XPath (마지막 수단)

## 🐛 트러블슈팅

### WebDriver 실행 오류
```
WebDriver 경로를 찾을 수 없음
→ webdriver-manager가 자동으로 설치합니다
```

### 요소를 찾을 수 없음
```python
# 명시적 대기 사용
element = wait.until(EC.presence_of_element_located(locator))
```

### 타임아웃 에러
```python
# 타임아웃 값 증가
self.wait = WebDriverWait(self.driver, 20)  # 20초
```

## 📚 추가 리소스

- [Selenium 공식 문서](https://www.selenium.dev/documentation/)
- [POM 패턴 가이드](https://www.selenium.dev/documentation/test_practices/encouraged/page_object_models/)
- [Python Selenium API](https://selenium-python.readthedocs.io/)

## 🤝 기여 방법

페이지 객체 추가:
1. `pages/` 디렉토리에 새 파일 생성
2. `BasePage`를 상속받음
3. 로케이터와 메서드 정의
4. 테스트 작성

## 📝 라이선스

MIT License
