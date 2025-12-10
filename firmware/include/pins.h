/**
 * Core S3 핀 정의
 * 
 * 참고: M5Stack Core S3 핀아웃
 * https://docs.m5stack.com/en/core/CoreS3
 */

#ifndef PINS_H
#define PINS_H

// ============================================================================
// 카메라 핀 (OV2640)
// ============================================================================
#define PWDN_GPIO_NUM     -1
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM     2
#define SIOD_GPIO_NUM     12
#define SIOC_GPIO_NUM     11

#define Y9_GPIO_NUM       47
#define Y8_GPIO_NUM       48
#define Y7_GPIO_NUM       16
#define Y6_GPIO_NUM       15
#define Y5_GPIO_NUM       42
#define Y4_GPIO_NUM       41
#define Y3_GPIO_NUM       40
#define Y2_GPIO_NUM       39

#define VSYNC_GPIO_NUM    46
#define HREF_GPIO_NUM     38
#define PCLK_GPIO_NUM     45

// ============================================================================
// I2S 핀 (오디오)
// ============================================================================
// I2S Output (Speaker - AW88298)
#define I2S_OUT_BCK       7
#define I2S_OUT_WS        5
#define I2S_OUT_DATA      6

// I2S Input (Microphone - ES7210)
#define I2S_IN_BCK        34
#define I2S_IN_WS         33
#define I2S_IN_DATA       14

// ============================================================================
// 버튼
// ============================================================================
#define BTN_A_PIN         0   // 전원 버튼
#define BTN_B_PIN         1   // 사용자 버튼 B
#define BTN_C_PIN         2   // 사용자 버튼 C

// ============================================================================
// LED
// ============================================================================
#define LED_PIN           21  // RGB LED (SK6812)

// ============================================================================
// 기타
// ============================================================================
#define TF_CARD_CS_PIN    4   // SD 카드 CS
#define BATTERY_ADC_PIN   4   // 배터리 전압 측정

#endif // PINS_H

