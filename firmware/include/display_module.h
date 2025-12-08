/**
 * 디스플레이 모듈 헤더
 */

#ifndef DISPLAY_MODULE_H
#define DISPLAY_MODULE_H

#include <Arduino.h>
#include <M5GFX.h>

// 디스플레이 초기화
void displayInit();

// 디스플레이 제어
void displayClear();
void displayShowText(const char* text);
void displayShowEmoji(const char* emojiId);
void displayShowStatus(const char* status, uint32_t color);
void displayShowSystemInfo();

#endif // DISPLAY_MODULE_H

