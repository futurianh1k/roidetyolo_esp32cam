#!/bin/bash
# ESP32-CoreS3 부팅 문제 디버깅 스크립트

set -e

PORT="${1:-/dev/ttyACM0}"
IDF_PATH="${IDF_PATH:-$HOME/esp/esp-idf}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}ESP32-CoreS3 부팅 문제 디버깅${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

# ESP-IDF 환경 설정
if [ -f "$IDF_PATH/export.sh" ]; then
    echo -e "${YELLOW}[1] ESP-IDF 환경 설정...${NC}"
    source "$IDF_PATH/export.sh"
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}ERROR: ESP-IDF를 찾을 수 없습니다: $IDF_PATH${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}[2] 시리얼 포트 확인: $PORT${NC}"
if [ ! -e "$PORT" ]; then
    echo -e "${RED}ERROR: 시리얼 포트를 찾을 수 없습니다: $PORT${NC}"
    echo -e "${YELLOW}사용 가능한 포트:${NC}"
    ls -la /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || echo "포트를 찾을 수 없습니다"
    exit 1
fi

# 권한 확인
if [ ! -r "$PORT" ] || [ ! -w "$PORT" ]; then
    echo -e "${YELLOW}경고: 시리얼 포트 권한이 없습니다.${NC}"
    echo -e "${CYAN}해결 방법:${NC}"
    echo -e "${GRAY}  sudo usermod -a -G dialout $USER${NC}"
    echo -e "${GRAY}  (로그아웃 후 다시 로그인 필요)${NC}"
    echo ""
fi

echo -e "${GREEN}OK${NC}"

echo ""
echo -e "${YELLOW}[3] 플래시 정보 확인...${NC}"
idf.py -p "$PORT" flash_id || echo -e "${YELLOW}경고: 플래시 ID를 읽을 수 없습니다${NC}"

echo ""
echo -e "${YELLOW}[4] 파티션 테이블 확인...${NC}"
idf.py partition-table || echo -e "${YELLOW}경고: 파티션 테이블을 확인할 수 없습니다${NC}"

echo ""
echo -e "${YELLOW}[5] 시리얼 모니터 시작 (10초간)...${NC}"
echo -e "${GRAY}디바이스를 리셋하거나 전원을 켜서 부트 로그를 확인하세요.${NC}"
echo -e "${GRAY}종료: Ctrl+]${NC}"
echo ""

timeout 10 idf.py -p "$PORT" monitor --print-filter="*:I" 2>/dev/null || true

echo ""
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}다음 단계:${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""
echo -e "${YELLOW}1. 부트 로그 확인:${NC}"
echo -e "${GRAY}   idf.py -p $PORT monitor${NC}"
echo ""
echo -e "${YELLOW}2. 전체 플래시 재작성:${NC}"
echo -e "${GRAY}   idf.py -p $PORT erase-flash${NC}"
echo -e "${GRAY}   idf.py -p $PORT flash${NC}"
echo ""
echo -e "${YELLOW}3. 플래시 검증:${NC}"
echo -e "${GRAY}   idf.py -p $PORT verify${NC}"
echo ""
echo -e "${YELLOW}4. 상세 로그 (에러만):${NC}"
echo -e "${GRAY}   idf.py -p $PORT monitor --print-filter=\"*:E\"${NC}"
echo ""
echo -e "${CYAN}자세한 내용은 DEBUG_BOOT_ISSUES.md를 참조하세요.${NC}"

