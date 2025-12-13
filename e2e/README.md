# E2E 테스트 가이드

Core S3 Management System의 End-to-End 테스트입니다.

## 설치

```bash
cd e2e
pip install -r requirements.txt
```

## 환경 설정

```bash
# .env 파일 생성
cp .env.example .env

# 필요에 따라 .env 수정
```

## 테스트 실행

### Windows PowerShell (권장)

```powershell
cd e2e

# 기본 실행 (헤드리스 모드)
.\run_tests.ps1

# 브라우저 표시 모드 (디버깅)
.\run_tests.ps1 -Headless $false

# 특정 테스트 파일 실행
.\run_tests.ps1 -TestFile test_dashboard.py

# HTML 리포트 생성
.\run_tests.ps1 -Report

# 느린 테스트 제외
.\run_tests.ps1 -Markers "not slow"

# 병렬 실행 (4개 프로세스)
.\run_tests.ps1 -Parallel 4

# 의존성만 설치
.\run_tests.ps1 -Install
```

### Windows CMD

```cmd
cd e2e

# 기본 실행
run_tests.cmd

# 브라우저 표시 모드
run_tests.cmd --no-headless

# 특정 테스트 파일
run_tests.cmd --file test_dashboard.py

# HTML 리포트 생성
run_tests.cmd --report

# 도움말
run_tests.cmd --help
```

### Linux/Mac (bash)

```bash
cd e2e
pip install -r requirements.txt

# 기본 실행 (헤드리스 모드)
pytest

# 브라우저 표시 모드
E2E_HEADLESS=false pytest

# 특정 테스트 파일 실행
pytest tests/test_dashboard.py

# 특정 테스트 케이스 실행
pytest tests/test_dashboard.py::TestDashboard::test_tc_dash_001_dashboard_load_and_stats
```

### 마커별 실행

```bash
# 대시보드 테스트만 실행
pytest -m dashboard

# 느린 테스트 제외
pytest -m "not slow"

# 인증 테스트 제외 (현재 비활성화 상태)
pytest -m "not auth"
```

### 병렬 실행

```bash
# 자동 병렬 실행
pytest -n auto

# 4개 프로세스로 실행
pytest -n 4
```

### 리포트 생성

```bash
# HTML 리포트
pytest --html=report.html --self-contained-html

# Allure 리포트
pytest --alluredir=allure-results
allure serve allure-results
```

## 테스트 시나리오

### 인증 (TC-AUTH)

| ID          | 설명                   | 상태                 |
| ----------- | ---------------------- | -------------------- |
| TC-AUTH-001 | 로그인 성공            | Skip (인증 비활성화) |
| TC-AUTH-002 | 로그인 실패            | Skip (인증 비활성화) |
| TC-AUTH-003 | 로그아웃               | Skip (인증 비활성화) |
| TC-AUTH-004 | 비로그인 대시보드 접근 | Active               |

### 대시보드 (TC-DASH)

| ID          | 설명                  | 상태   |
| ----------- | --------------------- | ------ |
| TC-DASH-001 | 대시보드 로드 및 통계 | Active |
| TC-DASH-002 | 장비 목록 표시        | Active |
| TC-DASH-003 | 장비 등록 모달        | Active |
| TC-DASH-004 | 장비 등록 플로우      | Active |
| TC-DASH-005 | 새로고침 버튼         | Active |
| TC-DASH-006 | 장비 상세 이동        | Active |

### 장비 상세 (TC-DEV)

| ID         | 설명               | 상태                 |
| ---------- | ------------------ | -------------------- |
| TC-DEV-001 | 상세 페이지 로드   | Active               |
| TC-DEV-002 | IP 주소 편집       | Active               |
| TC-DEV-003 | 카메라 제어        | Active (온라인 필요) |
| TC-DEV-004 | 디스플레이 텍스트  | Active (온라인 필요) |
| TC-DEV-005 | 음성인식 시작/종료 | Active (온라인 필요) |
| TC-DEV-006 | 장비 삭제          | Skip (주의 필요)     |
| TC-DEV-007 | 뒤로가기           | Active               |

### 음성인식 (TC-ASR)

| ID         | 설명           | 상태                  |
| ---------- | -------------- | --------------------- |
| TC-ASR-001 | 세션 시작      | Slow                  |
| TC-ASR-003 | 세션 종료      | Slow                  |
| TC-ASR-004 | WebSocket 연결 | Skip (인프라 필요)    |
| TC-ASR-005 | 응급 상황 감지 | Skip (실제 음성 필요) |

## 디렉토리 구조

```
e2e/
├── conftest.py          # Pytest 설정 및 fixtures
├── pytest.ini           # Pytest 설정
├── requirements.txt     # 의존성
├── .env.example         # 환경 변수 예제
├── README.md            # 이 파일
├── pages/               # Page Object 패턴
│   ├── __init__.py
│   ├── base_page.py
│   ├── login_page.py
│   ├── dashboard_page.py
│   └── device_detail_page.py
├── tests/               # 테스트 케이스
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_dashboard.py
│   ├── test_device_detail.py
│   └── test_asr.py
└── screenshots/         # 실패 시 스크린샷
```

## 트러블슈팅

### Chrome 드라이버 오류

```bash
# webdriver-manager가 자동으로 드라이버 설치
# 수동 설치가 필요한 경우:
pip install --upgrade webdriver-manager
```

### 타임아웃 오류

- `conftest.py`의 `driver.implicitly_wait()` 값 조정
- 각 Page Object의 `timeout` 값 조정

### 요소를 찾을 수 없음

- `E2E_SLOW_MODE=true`로 설정하여 디버깅
- `E2E_HEADLESS=false`로 브라우저 확인

## 참고 자료

- [Selenium Python](https://selenium-python.readthedocs.io/)
- [Pytest](https://docs.pytest.org/)
- [Page Object Pattern](https://www.selenium.dev/documentation/test_practices/encouraged/page_object_models/)
