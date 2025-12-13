@echo off
REM E2E 테스트 실행 스크립트 (CMD)
REM 사용법: run_tests.cmd [옵션]
REM 
REM 옵션:
REM   --no-headless    브라우저 표시 모드
REM   --slow           느린 모드 (디버깅용)
REM   --report         HTML 리포트 생성
REM   --install        의존성만 설치
REM   --file FILE      특정 테스트 파일 실행
REM
REM 예시:
REM   run_tests.cmd                           기본 실행
REM   run_tests.cmd --no-headless             브라우저 표시
REM   run_tests.cmd --file test_dashboard.py  대시보드 테스트만
REM   run_tests.cmd --report                  리포트 생성

setlocal EnableDelayedExpansion

cd /d "%~dp0"

echo.
echo ========================================
echo     E2E Test Runner (CMD)
echo ========================================
echo.

REM 기본 설정
set "HEADLESS=true"
set "SLOW_MODE=false"
set "REPORT=false"
set "INSTALL_ONLY=false"
set "TEST_FILE="
set "MARKERS="

REM 인자 파싱
:parse_args
if "%~1"=="" goto :done_args
if "%~1"=="--no-headless" set "HEADLESS=false" & shift & goto :parse_args
if "%~1"=="--slow" set "SLOW_MODE=true" & shift & goto :parse_args
if "%~1"=="--report" set "REPORT=true" & shift & goto :parse_args
if "%~1"=="--install" set "INSTALL_ONLY=true" & shift & goto :parse_args
if "%~1"=="--file" set "TEST_FILE=%~2" & shift & shift & goto :parse_args
if "%~1"=="--markers" set "MARKERS=%~2" & shift & shift & goto :parse_args
if "%~1"=="--help" goto :show_help
shift
goto :parse_args
:done_args

REM 가상환경 확인
if not exist "venv\Scripts\python.exe" (
    echo [*] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [X] Failed to create virtual environment
        exit /b 1
    )
)

REM 가상환경 활성화
call venv\Scripts\activate.bat

REM 의존성 설치
if not exist "venv\Scripts\pytest.exe" set "INSTALL_ONLY=true"
if "%INSTALL_ONLY%"=="true" (
    echo [*] Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [X] Failed to install dependencies
        exit /b 1
    )
    if "%TEST_FILE%"=="" if "%REPORT%"=="false" (
        echo [OK] Dependencies installed
        exit /b 0
    )
)

REM 스크린샷 디렉토리
if not exist "screenshots" mkdir screenshots

REM 환경 변수 설정
set "E2E_HEADLESS=%HEADLESS%"
set "E2E_SLOW_MODE=%SLOW_MODE%"
set "E2E_SCREENSHOT_DIR=screenshots"

REM .env 파일 로드
if exist ".env" (
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
        set "%%a=%%b"
    )
)

REM 환경 변수 오버라이드
set "E2E_HEADLESS=%HEADLESS%"
set "E2E_SLOW_MODE=%SLOW_MODE%"

echo [*] Configuration:
echo     E2E_HEADLESS = %E2E_HEADLESS%
echo     E2E_SLOW_MODE = %E2E_SLOW_MODE%
echo     E2E_BASE_URL = %E2E_BASE_URL%
echo.

REM pytest 인자 구성
set "PYTEST_ARGS=-v --tb=short"

if not "%TEST_FILE%"=="" (
    set "PYTEST_ARGS=%PYTEST_ARGS% tests\%TEST_FILE%"
)

if not "%MARKERS%"=="" (
    set "PYTEST_ARGS=%PYTEST_ARGS% -m "%MARKERS%""
)

if "%REPORT%"=="true" (
    if not exist "reports" mkdir reports
    for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set "datetime=%%I"
    set "TIMESTAMP=!datetime:~0,8!_!datetime:~8,6!"
    set "PYTEST_ARGS=%PYTEST_ARGS% --html=reports\report_!TIMESTAMP!.html --self-contained-html"
)

REM 테스트 실행
echo [*] Running tests...
echo     python -m pytest %PYTEST_ARGS%
echo.

python -m pytest %PYTEST_ARGS%
set "EXIT_CODE=%ERRORLEVEL%"

echo.
if %EXIT_CODE%==0 (
    echo [OK] All tests passed!
) else (
    echo [X] Some tests failed (exit code: %EXIT_CODE%)
)

exit /b %EXIT_CODE%

:show_help
echo Usage: run_tests.cmd [options]
echo.
echo Options:
echo   --no-headless    Show browser window
echo   --slow           Slow mode for debugging
echo   --report         Generate HTML report
echo   --install        Install dependencies only
echo   --file FILE      Run specific test file
echo   --markers EXPR   Pytest marker expression
echo   --help           Show this help
echo.
echo Examples:
echo   run_tests.cmd                           Run all tests
echo   run_tests.cmd --no-headless             Show browser
echo   run_tests.cmd --file test_dashboard.py  Dashboard tests only
echo   run_tests.cmd --report                  Generate report
exit /b 0
