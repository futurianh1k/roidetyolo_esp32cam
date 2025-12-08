/**
 * Core S3 Management System - 설정 파일
 * 
 * WiFi, MQTT, 장비 설정
 */

#ifndef CONFIG_H
#define CONFIG_H

// ============================================================================
// WiFi 설정
// ============================================================================
#define WIFI_SSID "LUKUS"
#define WIFI_PASSWORD "important1@"
#define WIFI_CONNECT_TIMEOUT 30000  // 30초
#define WIFI_RETRY_INTERVAL 5000    // 5초

// ============================================================================
// MQTT 설정
// ============================================================================
#define MQTT_BROKER "10.10.11.18"  // 백엔드 서버 IP
#define MQTT_PORT 1883
#define MQTT_USERNAME ""
#define MQTT_PASSWORD ""
#define MQTT_CLIENT_ID_PREFIX "cores3_"
#define MQTT_KEEPALIVE_SEC 60  // PubSubClient의 MQTT_KEEPALIVE와 충돌 방지
#define MQTT_QOS 1

// ============================================================================
// 장비 설정
// ============================================================================
#define DEVICE_ID "core_s3_001"  // 고유 장비 ID (MAC 주소 기반으로 자동 생성 가능)
#define DEVICE_NAME "Core S3 Camera"
#define DEVICE_LOCATION "Office"

// ============================================================================
// MQTT 토픽
// ============================================================================
#define TOPIC_CONTROL_CAMERA "devices/" DEVICE_ID "/control/camera"
#define TOPIC_CONTROL_MICROPHONE "devices/" DEVICE_ID "/control/microphone"
#define TOPIC_CONTROL_SPEAKER "devices/" DEVICE_ID "/control/speaker"
#define TOPIC_CONTROL_DISPLAY "devices/" DEVICE_ID "/control/display"
#define TOPIC_STATUS "devices/" DEVICE_ID "/status"
#define TOPIC_RESPONSE "devices/" DEVICE_ID "/response"

// ============================================================================
// 카메라 설정
// ============================================================================
#define CAMERA_MODEL_M5STACK_CORES3
#define CAMERA_FRAMESIZE FRAMESIZE_VGA  // 640x480
#define CAMERA_QUALITY 10  // 0-63, 낮을수록 고품질
#define CAMERA_BRIGHTNESS 0  // -2 to 2
#define CAMERA_CONTRAST 0    // -2 to 2
#define CAMERA_SATURATION 0  // -2 to 2

// ============================================================================
// RTSP 설정
// ============================================================================
#define RTSP_PORT 554
#define RTSP_USERNAME ""
#define RTSP_PASSWORD ""

// ============================================================================
// 오디오 설정
// ============================================================================
#define I2S_SAMPLE_RATE 16000
#define I2S_BITS_PER_SAMPLE 16
#define I2S_CHANNELS 1

// ============================================================================
// 상태 보고 설정
// ============================================================================
#define STATUS_REPORT_INTERVAL 10000  // 10초마다 상태 보고
#define BATTERY_CHECK_INTERVAL 5000   // 5초마다 배터리 체크

// ============================================================================
// 디스플레이 설정
// ============================================================================
#define SCREEN_WIDTH 320
#define SCREEN_HEIGHT 240
#define TEXT_SIZE 2
#define TEXT_COLOR TFT_WHITE
#define BG_COLOR TFT_BLACK

// ============================================================================
// 디버그 설정
// ============================================================================
#define DEBUG_ENABLED 1
#if DEBUG_ENABLED
  #define DEBUG_PRINT(x) Serial.print(x)
  #define DEBUG_PRINTLN(x) Serial.println(x)
  #define DEBUG_PRINTF(x, ...) Serial.printf(x, ##__VA_ARGS__)
#else
  #define DEBUG_PRINT(x)
  #define DEBUG_PRINTLN(x)
  #define DEBUG_PRINTF(x, ...)
#endif

#endif // CONFIG_H

