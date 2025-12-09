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

/**
 * 디스플레이 초기화
 */
void displayInit() {
  display = &M5.Display;

  display->begin();
  display->setRotation(1); // 가로 모드
  display->setBrightness(128);
  display->setColorDepth(16);

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
 */
void displayShowText(const char *text) {
  if (!display)
    return;

  displayClear();

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
 */
void displayShowStatus(const char *status, uint32_t color) {
  if (!display)
    return;

  // 상단에 상태 바 표시
  display->fillRect(0, 0, SCREEN_WIDTH, 30, color);
  display->setTextSize(2);
  display->setTextColor(TFT_WHITE, color);
  display->setTextDatum(middle_center);
  display->drawString(status, SCREEN_WIDTH / 2, 15);

  DEBUG_PRINTF("Status: %s\n", status);
}

/**
 * 시스템 정보 표시
 */
void displayShowSystemInfo() {
  if (!display)
    return;

  displayClear();

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
