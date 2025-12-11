/**
 * 디스플레이 모듈
 *
 * LCD 디스플레이 제어
 */

#include "display_module.h"
#include "config.h"
#include <M5GFX.h>
#include <M5Unified.h>
#include <WiFi.h>


static M5GFX *display = nullptr;
static constexpr size_t STATUS_HISTORY_SIZE = 4;
static constexpr int STATUS_BAR_HEIGHT = 38;
static constexpr int STATUS_HISTORY_SECTION_HEIGHT = 24;

static String statusHistory[STATUS_HISTORY_SIZE];
static uint32_t statusColorHistory[STATUS_HISTORY_SIZE];
static uint32_t statusTimestampHistory[STATUS_HISTORY_SIZE];
static size_t statusHistoryCount = 0;
static bool hasLastStatus = false;
static String lastStatusValue;
static uint32_t lastStatusColor = 0;

void setUtf8Font();

/**
 * 상태 변경 시각을 사람이 읽을 수 있는 형태로 변환
 */
static String formatStatusAge(uint32_t eventMillis) {
  const uint32_t now = millis();
  const uint32_t elapsedSeconds =
      (now >= eventMillis) ? (now - eventMillis) / 1000 : 0;

  if (elapsedSeconds < 60) {
    return String(elapsedSeconds) + "s ago";
  }

  if (elapsedSeconds < 3600) {
    return String(elapsedSeconds / 60) + "m ago";
  }

  return String(elapsedSeconds / 3600) + "h ago";
}

/**
 * 상태 히스토리를 갱신
 */
static void updateStatusHistory(const String &text, uint32_t color) {
  const uint32_t now = millis();

  if (hasLastStatus && lastStatusValue == text &&
      lastStatusColor == color && statusHistoryCount > 0) {
    statusTimestampHistory[0] = now;
  } else {
    const size_t lastIndex =
        (statusHistoryCount >= STATUS_HISTORY_SIZE) ? STATUS_HISTORY_SIZE - 1
                                                    : statusHistoryCount;

    for (size_t i = lastIndex; i > 0; --i) {
      statusHistory[i] = statusHistory[i - 1];
      statusColorHistory[i] = statusColorHistory[i - 1];
      statusTimestampHistory[i] = statusTimestampHistory[i - 1];
    }

    statusHistory[0] = text;
    statusColorHistory[0] = color;
    statusTimestampHistory[0] = now;

    if (statusHistoryCount < STATUS_HISTORY_SIZE) {
      statusHistoryCount++;
    }
  }

  lastStatusValue = text;
  lastStatusColor = color;
  hasLastStatus = true;
}

/**
 * 상태 오버레이 렌더링
 */
static void renderStatusOverlay() {
  if (!display || statusHistoryCount == 0)
    return;

  setUtf8Font();

  const uint32_t activeColor = statusColorHistory[0];
  const int iconCenterX = 18;
  const int iconRadius = 12;
  const int textStartX = 40;

  // 최상단 상태 바
  display->fillRect(0, 0, SCREEN_WIDTH, STATUS_BAR_HEIGHT, activeColor);
  display->fillCircle(iconCenterX, STATUS_BAR_HEIGHT / 2, iconRadius,
                      TFT_WHITE);
  display->fillCircle(iconCenterX, STATUS_BAR_HEIGHT / 2, iconRadius - 3,
                      activeColor);
  display->drawCircle(iconCenterX, STATUS_BAR_HEIGHT / 2, iconRadius,
                      TFT_WHITE);

  display->setTextDatum(middle_left);
  display->setTextSize(2);
  display->setTextColor(TFT_WHITE, activeColor);
  display->drawString(statusHistory[0], textStartX, STATUS_BAR_HEIGHT / 2);

  display->setTextSize(1);
  display->setTextDatum(middle_right);
  display->drawString(formatStatusAge(statusTimestampHistory[0]),
                      SCREEN_WIDTH - 6, STATUS_BAR_HEIGHT / 2);

  if (statusHistoryCount <= 1)
    return;

  // 최근 기록 영역
  display->fillRect(0, STATUS_BAR_HEIGHT, SCREEN_WIDTH,
                    STATUS_HISTORY_SECTION_HEIGHT, BG_COLOR);
  display->setTextDatum(top_left);
  display->setTextColor(TEXT_COLOR, BG_COLOR);
  display->setTextSize(1);

  const size_t limit = (statusHistoryCount > STATUS_HISTORY_SIZE)
                           ? STATUS_HISTORY_SIZE
                           : statusHistoryCount;

  int lineY = STATUS_BAR_HEIGHT + 4;
  for (size_t i = 1; i < limit; ++i) {
    display->fillCircle(10, lineY + 4, 3, statusColorHistory[i]);
    String historyLine =
        formatStatusAge(statusTimestampHistory[i]) + " - " + statusHistory[i];
    display->drawString(historyLine, 18, lineY);
    lineY += 14;

    if (lineY >= STATUS_BAR_HEIGHT + STATUS_HISTORY_SECTION_HEIGHT - 6) {
      break;
    }
  }
}

/**
 * UTF-8 폰트 설정
 * M5GFX의 내장 UTF-8 폰트 사용 (한글/일본어 지원)
 *
 * 참고: M5GFX는 fonts 네임스페이스에 폰트를 제공합니다.
 * 한국어: &fonts::efontKR_16, &fonts::efontKR_24
 * 일본어: &fonts::lgfxJapanMincho_16, &fonts::lgfxJapanGothic_16 등
 *
 * M5GFX v0.1.14 이상에서는 efontKR 폰트가 기본적으로 포함되어 있습니다.
 */
void setUtf8Font() {
  if (!display)
    return;

  // M5GFX 내장 UTF-8 폰트 사용
  // 한국어 폰트 사용 (일본어도 일부 지원)
  // efontKR_16은 한국어를 지원하는 16px 폰트
  // M5GFX v0.1.14 이상에서는 이 폰트가 기본적으로 포함됨
  display->setFont(&fonts::efontKR_16);
  DEBUG_PRINTLN("UTF-8 font set (Korean/Japanese support)");
}

/**
 * 디스플레이 초기화
 */
void displayInit() {
  display = &M5.Display;

  display->begin();
  display->setRotation(1); // 가로 모드
  display->setBrightness(128);
  display->setColorDepth(16);

  // UTF-8 폰트 설정 (한글/일본어 지원)
  setUtf8Font();

  displayClear();

  DEBUG_PRINTLN("Display initialized");
}

/**
 * 화면 지우기
 */
void displayClear() {
  if (!display)
    return;

  display->fillScreen(BG_COLOR);
  display->setCursor(0, 0);

  DEBUG_PRINTLN("Display cleared");
}

/**
 * 텍스트 표시
 * UTF-8 폰트를 사용하여 한글/일본어 텍스트를 올바르게 표시합니다.
 */
void displayShowText(const char *text) {
  if (!display)
    return;

  displayClear();

  // UTF-8 폰트 설정 (한글/일본어 지원)
  setUtf8Font();

  display->setTextSize(TEXT_SIZE);
  display->setTextColor(TEXT_COLOR, BG_COLOR);
  display->setTextDatum(middle_center);

  // 화면 중앙에 텍스트 표시
  display->drawString(text, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2);

  DEBUG_PRINTF("Displayed text: %s\n", text);
}

/**
 * 이모티콘 표시
 * M5GFX를 사용하여 실제 그래픽으로 이모티콘 그리기
 */
void displayShowEmoji(const char *emojiId) {
  if (!display)
    return;

  displayClear();

  int centerX = SCREEN_WIDTH / 2;
  int centerY = SCREEN_HEIGHT / 2;
  int radius = 60; // 기본 원 반지름

  // 이모티콘 ID에 따라 다른 그래픽 표시
  if (strcmp(emojiId, "smile") == 0) {
    // 😊 웃는 얼굴
    display->fillCircle(centerX, centerY, radius, TFT_YELLOW);
    display->fillCircle(centerX - 20, centerY - 15, 8, TFT_BLACK); // 왼쪽 눈
    display->fillCircle(centerX + 20, centerY - 15, 8, TFT_BLACK); // 오른쪽 눈
    display->drawArc(centerX, centerY + 10, 35, 30, 0, 180,
                     TFT_BLACK);                             // 웃는 입
    display->fillCircle(centerX - 35, centerY, 10, TFT_RED); // 왼쪽 볼
    display->fillCircle(centerX + 35, centerY, 10, TFT_RED); // 오른쪽 볼
  } else if (strcmp(emojiId, "sad") == 0) {
    // 😢 슬픈 얼굴
    display->fillCircle(centerX, centerY, radius, TFT_YELLOW);
    display->fillCircle(centerX - 20, centerY - 15, 8, TFT_BLACK);
    display->fillCircle(centerX + 20, centerY - 15, 8, TFT_BLACK);
    display->drawArc(centerX, centerY + 30, 35, 30, 180, 360,
                     TFT_BLACK); // 슬픈 입
  } else if (strcmp(emojiId, "heart") == 0) {
    // ❤️ 하트
    int x = centerX;
    int y = centerY - 10;
    display->fillCircle(x - 25, y, 30, TFT_RED);
    display->fillCircle(x + 25, y, 30, TFT_RED);
    display->fillTriangle(x - 50, y + 10, x, y + 60, x + 50, y + 10, TFT_RED);
  } else if (strcmp(emojiId, "thumbs_up") == 0) {
    // 👍 좋아요 (단순화된 엄지)
    display->fillRoundRect(centerX - 15, centerY - 30, 30, 60, 8,
                           TFT_YELLOW);                                // 엄지
    display->fillRect(centerX - 20, centerY + 20, 40, 20, TFT_YELLOW); // 손바닥
    display->drawCircle(centerX - 5, centerY - 35, 15, TFT_ORANGE); // 강조 원
  } else if (strcmp(emojiId, "warning") == 0) {
    // ⚠️ 경고
    display->fillTriangle(centerX, centerY - 60, centerX - 60, centerY + 50,
                          centerX + 60, centerY + 50, TFT_YELLOW);
    display->drawTriangle(centerX, centerY - 60, centerX - 60, centerY + 50,
                          centerX + 60, centerY + 50, TFT_RED);
    display->fillRect(centerX - 5, centerY - 20, 10, 30, TFT_RED); // !
    display->fillCircle(centerX, centerY + 25, 6, TFT_RED);        // .
  } else if (strcmp(emojiId, "check") == 0) {
    // ✅ 체크
    display->fillRoundRect(centerX - 50, centerY - 50, 100, 100, 15, TFT_GREEN);
    display->drawLine(centerX - 30, centerY, centerX - 10, centerY + 25,
                      TFT_WHITE);
    display->drawLine(centerX - 10, centerY + 25, centerX + 35, centerY - 30,
                      TFT_WHITE);
    // 두께감을 위해 중복 그리기
    display->drawLine(centerX - 29, centerY + 1, centerX - 9, centerY + 26,
                      TFT_WHITE);
    display->drawLine(centerX - 9, centerY + 26, centerX + 36, centerY - 29,
                      TFT_WHITE);
    display->drawLine(centerX - 31, centerY - 1, centerX - 11, centerY + 24,
                      TFT_WHITE);
    display->drawLine(centerX - 11, centerY + 24, centerX + 34, centerY - 31,
                      TFT_WHITE);
  } else if (strcmp(emojiId, "fire") == 0) {
    // 🔥 불
    display->fillCircle(centerX, centerY + 20, 40, TFT_RED);
    display->fillCircle(centerX, centerY, 35, TFT_ORANGE);
    display->fillCircle(centerX, centerY - 15, 25, TFT_YELLOW);
    display->fillCircle(centerX, centerY - 25, 15, TFT_WHITE);
  } else if (strcmp(emojiId, "star") == 0) {
    // ⭐ 별
    int points[][2] = {
        {centerX, centerY - 60},      // 상단
        {centerX + 15, centerY - 20}, // 우상 내각
        {centerX + 55, centerY - 15}, // 우상 외각
        {centerX + 25, centerY + 10}, // 우하 내각
        {centerX + 35, centerY + 50}, // 우하 외각
        {centerX, centerY + 25},      // 하단 내각
        {centerX - 35, centerY + 50}, // 좌하 외각
        {centerX - 25, centerY + 10}, // 좌하 내각
        {centerX - 55, centerY - 15}, // 좌상 외각
        {centerX - 15, centerY - 20}  // 좌상 내각
    };
    for (int i = 0; i < 10; i++) {
      display->fillTriangle(centerX, centerY, points[i][0], points[i][1],
                            points[(i + 1) % 10][0], points[(i + 1) % 10][1],
                            TFT_YELLOW);
    }
  } else if (strcmp(emojiId, "moon") == 0) {
    // 🌙 달
    display->fillCircle(centerX - 10, centerY, 50, TFT_YELLOW);
    display->fillCircle(centerX + 15, centerY, 45, BG_COLOR);
  } else {
    // 알 수 없는 이모티콘
    display->fillCircle(centerX, centerY, radius, TFT_DARKGREY);
    display->setTextSize(4);
    display->setTextColor(TFT_WHITE, TFT_DARKGREY);
    display->setTextDatum(middle_center);
    display->drawString("?", centerX, centerY);
  }

  DEBUG_PRINTF("Displayed emoji: %s\n", emojiId);
}

/**
 * 상태 메시지 표시
 * UTF-8 폰트를 사용하여 한글/일본어 상태 메시지를 올바르게 표시합니다.
 */
void displayShowStatus(const char *status, uint32_t color) {
  if (!display)
    return;

  String statusText = String(status ? status : "");
  statusText.trim();
  if (statusText.isEmpty()) {
    statusText = "Status";
  }

  updateStatusHistory(statusText, color);
  renderStatusOverlay();

  DEBUG_PRINTF("Status: %s\n", statusText.c_str());
}

/**
 * 시스템 정보 표시
 * UTF-8 폰트를 사용하여 한글/일본어 시스템 정보를 올바르게 표시합니다.
 */
void displayShowSystemInfo() {
  if (!display)
    return;

  displayClear();

  // UTF-8 폰트 설정 (한글/일본어 지원)
  setUtf8Font();

  display->setTextSize(1);
  display->setTextColor(TEXT_COLOR, BG_COLOR);
  display->setTextDatum(top_left);

  int y = 10;
  int lineHeight = 20;

  // 제목
  display->setTextSize(2);
  display->drawString("System Info", 10, y);
  y += lineHeight * 2;

  display->setTextSize(1);

  // WiFi 정보
  if (WiFi.status() == WL_CONNECTED) {
    display->drawString("WiFi: Connected", 10, y);
    y += lineHeight;

    String ip = "IP: " + WiFi.localIP().toString();
    display->drawString(ip, 10, y);
    y += lineHeight;

    String rssi = "RSSI: " + String(WiFi.RSSI()) + " dBm";
    display->drawString(rssi, 10, y);
    y += lineHeight;
  } else {
    display->drawString("WiFi: Disconnected", 10, y);
    y += lineHeight;
  }

  y += lineHeight / 2;

  // 메모리 정보
  String freeHeap = "Free Heap: " + String(ESP.getFreeHeap() / 1024) + " KB";
  display->drawString(freeHeap, 10, y);
  y += lineHeight;

  String totalHeap = "Total Heap: " + String(ESP.getHeapSize() / 1024) + " KB";
  display->drawString(totalHeap, 10, y);
  y += lineHeight;

  y += lineHeight / 2;

  // 장비 정보
  display->drawString("Device ID: " + String(DEVICE_ID), 10, y);
  y += lineHeight;

  // 업타임
  unsigned long uptime = millis() / 1000;
  String uptimeStr =
      "Uptime: " + String(uptime / 60) + "m " + String(uptime % 60) + "s";
  display->drawString(uptimeStr, 10, y);

  DEBUG_PRINTLN("System info displayed");
}
