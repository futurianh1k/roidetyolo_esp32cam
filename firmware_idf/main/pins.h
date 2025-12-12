#ifndef PINS_H
#define PINS_H

// 카메라 핀 (M5Stack CoreS3 - GC0308)
// Reference: https://docs.m5stack.com/en/core/CoreS3
// Camera: GC0308 (0.3MP)
#define PWDN_GPIO_NUM -1 // Not connected
#define RESET_GPIO_NUM 1 // Reset pin (was AW9523B P1_0, now GPIO1)
#define XCLK_GPIO_NUM 8  // External clock (corrected from GPIO40)
#define SIOD_GPIO_NUM 12 // I2C SDA
#define SIOC_GPIO_NUM 11 // I2C SCL

// Data pins (D0-D7) - GC0308
#define Y9_GPIO_NUM 4  // D7
#define Y8_GPIO_NUM 5  // D6
#define Y7_GPIO_NUM 6  // D5
#define Y6_GPIO_NUM 7  // D4
#define Y5_GPIO_NUM 15 // D3
#define Y4_GPIO_NUM 16 // D2
#define Y3_GPIO_NUM 48 // D1
#define Y2_GPIO_NUM 47 // D0

// Control pins
#define VSYNC_GPIO_NUM 46 // Vertical sync
#define HREF_GPIO_NUM 38  // Horizontal reference
#define PCLK_GPIO_NUM 45  // Pixel clock

// I2S 핀 (오디오) - M5Stack CoreS3
// Reference: https://docs.m5stack.com/en/core/CoreS3
// Shared I2S bus for both Speaker (AW88298) and Microphone (ES7210)
#define I2S_MCLK 0      // I2S Master Clock
#define I2S_BCK 34      // I2S Bit Clock (shared)
#define I2S_WS 33       // I2S Word Select (shared)
#define I2S_OUT_DATA 13 // Speaker data out
#define I2S_IN_DATA 14  // Microphone data in

// Legacy defines for compatibility
#define I2S_OUT_BCK I2S_BCK
#define I2S_OUT_WS I2S_WS
#define I2S_IN_BCK I2S_BCK
#define I2S_IN_WS I2S_WS

#endif // PINS_H
