#ifndef CONFIG_H
#define CONFIG_H

// WiFi 설정
#define WIFI_SSID "LUKUS"
#define WIFI_PASSWORD "important1@"
#define WIFI_CONNECT_TIMEOUT_MS 30000

// MQTT 설정
#define MQTT_BROKER "10.10.11.18"
#define MQTT_PORT 1883
#define MQTT_USERNAME ""
#define MQTT_PASSWORD ""
#define MQTT_CLIENT_ID_PREFIX "cores3_"
#define MQTT_KEEPALIVE_SEC 60
#define MQTT_QOS 1

// 장비 설정
#define DEVICE_ID "core_s3_001"
#define DEVICE_NAME "Core S3 Camera"
#define DEVICE_LOCATION "Office"

// 장비 DB ID (백엔드에서 할당된 ID)
// Note: 런타임에 NVS 또는 백엔드에서 자동으로 조회됨
// DEVICE_DB_ID는 더 이상 하드코딩하지 않음

// MQTT 토픽
#define TOPIC_CONTROL_CAMERA "devices/" DEVICE_ID "/control/camera"
#define TOPIC_CONTROL_MICROPHONE "devices/" DEVICE_ID "/control/microphone"
#define TOPIC_CONTROL_SPEAKER "devices/" DEVICE_ID "/control/speaker"
#define TOPIC_CONTROL_DISPLAY "devices/" DEVICE_ID "/control/display"
#define TOPIC_CONTROL_SYSTEM "devices/" DEVICE_ID "/control/system"
#define TOPIC_STATUS "devices/" DEVICE_ID "/status"
#define TOPIC_RESPONSE "devices/" DEVICE_ID "/response"

// 카메라 설정
// Note: FRAMESIZE_VGA는 esp_camera.h에서 정의됨
#define CAMERA_FRAMESIZE FRAMESIZE_VGA // 640x480
#define CAMERA_QUALITY 10
#define CAMERA_BRIGHTNESS 0
#define CAMERA_CONTRAST 0
#define CAMERA_SATURATION 0

// 오디오 설정
#define I2S_SAMPLE_RATE 16000
#define I2S_BITS_PER_SAMPLE 16
#define I2S_CHANNELS 1

// 상태 보고 설정
#define STATUS_REPORT_INTERVAL_MS 60000 // 기본값 60초 (1분)

// 버튼 설정
#define BUTTON_LONG_PRESS_MS 1000  // 롱프레스 감지 시간
#define BUTTON_DOUBLE_CLICK_MS 300 // 더블클릭 감지 시간

// 절전 모드 설정
#define LIGHT_SLEEP_DURATION_MS 300000 // Light Sleep 지속 시간 (5분)
#define DEEP_SLEEP_DURATION_SEC 0 // Deep Sleep 지속 시간 (0 = GPIO로만 깨움)

// ASR 서버 설정
#define ASR_SERVER_HOST "10.10.11.17"
#define ASR_SERVER_PORT 8001
#define ASR_SERVER_API_URL                                                     \
  "http://" ASR_SERVER_HOST ":" STRINGIFY(ASR_SERVER_PORT)
#define STRINGIFY(x) #x

// 백엔드 서버 설정 (음성인식 결과 전송용)
#define BACKEND_HOST "10.10.11.18"
#define BACKEND_PORT 8000
#define BACKEND_URL "http://" BACKEND_HOST ":" STRINGIFY(BACKEND_PORT)

// MQTT 명령 토픽
#define TOPIC_COMMAND "devices/" DEVICE_ID "/command"

#endif // CONFIG_H
