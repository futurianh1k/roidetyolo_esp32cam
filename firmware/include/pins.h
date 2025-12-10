/**
 * Core S3 핀 정의
 *
 * 참고: M5Stack Core S3 핀아웃
 * https://docs.m5stack.com/en/core/CoreS3
 *
 * ⚠️ 핀 충돌 주의!
 * - XCLK_GPIO_NUM: 카메라 클럭 핀 (필수)
 * - I2S 핀들: 오디오 입출력 (필수)
 * - 사용자 버튼은 선택사항
 */

#ifndef PINS_H
#define PINS_H

// ============================================================================
// 카메라 핀 (OV2640)
// ============================================================================
#define PWDN_GPIO_NUM -1  // 파워다운 핀 (사용 안 함)
#define RESET_GPIO_NUM -1 // 리셋 핀 (사용 안 함)
#define XCLK_GPIO_NUM 10  // 클럭 핀 (카메라 필수)
#define SIOD_GPIO_NUM 12  // I2C SDA
#define SIOC_GPIO_NUM 11  // I2C SCL

#define Y9_GPIO_NUM 47 // D7
#define Y8_GPIO_NUM 48 // D6
#define Y7_GPIO_NUM 16 // D5
#define Y6_GPIO_NUM 15 // D4
#define Y5_GPIO_NUM 42 // D3
#define Y4_GPIO_NUM 41 // D2
#define Y3_GPIO_NUM 40 // D1
#define Y2_GPIO_NUM 39 // D0

#define VSYNC_GPIO_NUM 46 // VSYNC
#define HREF_GPIO_NUM 38  // HREF
#define PCLK_GPIO_NUM 45  // PCLK

// ============================================================================
// I2S 핀 (오디오)
// ============================================================================
// I2S Output (Speaker - AW88298)
#define I2S_OUT_BCK 7  // Bit Clock
#define I2S_OUT_WS 5   // Word Select
#define I2S_OUT_DATA 6 // Data Out

// I2S Input (Microphone - ES7210)
#define I2S_IN_BCK 34  // Bit Clock
#define I2S_IN_WS 33   // Word Select
#define I2S_IN_DATA 14 // Data In

// ============================================================================
// 버튼 (선택사항)
// ============================================================================
// M5Stack Core S3의 버튼은 특별한 설정이 필요합니다
// GPIO 0: 전원 버튼 (자동 관리)
// GPIO 41-42: 터치 센서로 사용됨

// ============================================================================
// LED & 기타
// ============================================================================
#define LED_PIN 21 // RGB LED (SK6812)

// SD 카드와 배터리 ADC는 내부 신호선으로 자동 관리됨
// 추가 핀 설정이 필요하지 않습니다

#endif // PINS_H
