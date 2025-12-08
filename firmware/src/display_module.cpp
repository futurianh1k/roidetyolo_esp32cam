/**
 * 디스플레이 모듈
 * 
 * LCD 디스플레이 제어
 */

#include <M5Unified.h>
#include <M5GFX.h>
#include "display_module.h"
#include "config.h"

static M5GFX* display = nullptr;

/**
 * 디스플레이 초기화
 */
void displayInit() {
    display = &M5.Display;
    
    display->begin();
    display->setRotation(1);  // 가로 모드
    display->setBrightness(128);
    display->setColorDepth(16);
    
    displayClear();
    
    DEBUG_PRINTLN("Display initialized");
}

/**
 * 화면 지우기
 */
void displayClear() {
    if (!display) return;
    
    display->fillScreen(BG_COLOR);
}

/**
 * 텍스트 표시
 */
void displayShowText(const char* text) {
    if (!display) return;
    
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
 */
void displayShowEmoji(const char* emojiId) {
    if (!display) return;
    
    displayClear();
    
    // 이모티콘 ID에 따라 다른 이모티콘 표시
    display->setTextSize(8);
    display->setTextColor(TFT_YELLOW, BG_COLOR);
    display->setTextDatum(middle_center);
    
    String emoji = "";
    
    if (strcmp(emojiId, "smile") == 0) {
        emoji = ":)";
    }
    else if (strcmp(emojiId, "sad") == 0) {
        emoji = ":(";
    }
    else if (strcmp(emojiId, "heart") == 0) {
        emoji = "<3";
    }
    else if (strcmp(emojiId, "thumbs_up") == 0) {
        emoji = "!";
    }
    else if (strcmp(emojiId, "warning") == 0) {
        emoji = "/!\\";
        display->setTextColor(TFT_RED, BG_COLOR);
    }
    else if (strcmp(emojiId, "check") == 0) {
        emoji = "OK";
        display->setTextColor(TFT_GREEN, BG_COLOR);
    }
    else {
        emoji = "?";
    }
    
    display->drawString(emoji, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2);
    
    DEBUG_PRINTF("Displayed emoji: %s\n", emojiId);
}

/**
 * 상태 메시지 표시
 */
void displayShowStatus(const char* status, uint32_t color) {
    if (!display) return;
    
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
    if (!display) return;
    
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
    String uptimeStr = "Uptime: " + String(uptime / 60) + "m " + String(uptime % 60) + "s";
    display->drawString(uptimeStr, 10, y);
    
    DEBUG_PRINTLN("System info displayed");
}

