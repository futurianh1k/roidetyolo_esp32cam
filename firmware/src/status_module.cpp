/**
 * 상태 모듈
 * 
 * 시스템 상태 모니터링 및 보고
 */

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "status_module.h"
#include "config.h"

// 외부 변수
extern bool cameraActive;
extern bool microphoneActive;

/**
 * 배터리 레벨 가져오기
 */
int getBatteryLevel() {
    // M5Stack Core S3는 내부 배터리 관리 IC가 있음
    // AXP2101 배터리 관리 IC 사용
    // TODO: AXP2101 라이브러리로 실제 배터리 레벨 읽기
    
    // 임시: 배터리 전압 ADC 읽기
    // 완전 충전: ~4.2V, 방전: ~3.0V
    // ADC 범위: 0-4095 (12-bit)
    
    // 더미 값 (실제로는 AXP2101 사용)
    return 85;  // 85%
}

/**
 * 여유 힙 메모리
 */
uint32_t getFreeHeap() {
    return ESP.getFreeHeap();
}

/**
 * 전체 힙 메모리
 */
uint32_t getTotalHeap() {
    return ESP.getHeapSize();
}

/**
 * CPU 온도 가져오기
 */
float getCPUTemperature() {
    // ESP32-S3 내부 온도 센서
    // TODO: 실제 온도 센서 읽기 구현
    
    // 더미 값
    return 38.5;  // 섭씨
}

/**
 * 시스템 상태 가져오기
 */
SystemStatus getSystemStatus() {
    SystemStatus status;
    
    status.batteryLevel = getBatteryLevel();
    status.memoryUsage = getTotalHeap() - getFreeHeap();
    status.storageUsage = 0;  // TODO: SD 카드 사용량
    status.temperature = getCPUTemperature();
    status.cpuUsage = 0;  // TODO: CPU 사용률 계산
    
    // 카메라 상태
    if (cameraActive) {
        status.cameraStatus = "active";
    } else {
        status.cameraStatus = "stopped";
    }
    
    // 마이크 상태
    if (microphoneActive) {
        status.micStatus = "active";
    } else {
        status.micStatus = "stopped";
    }
    
    return status;
}

/**
 * 상태 보고
 */
void reportStatus(PubSubClient& client) {
    if (!client.connected()) {
        return;
    }
    
    // 시스템 상태 가져오기
    SystemStatus status = getSystemStatus();
    
    // JSON 생성
    StaticJsonDocument<512> doc;
    
    doc["device_id"] = DEVICE_ID;
    doc["battery_level"] = status.batteryLevel;
    doc["memory_usage"] = status.memoryUsage;
    doc["storage_usage"] = status.storageUsage;
    doc["temperature"] = status.temperature;
    doc["cpu_usage"] = status.cpuUsage;
    doc["camera_status"] = status.cameraStatus;
    doc["mic_status"] = status.micStatus;
    doc["timestamp"] = millis() / 1000;
    
    // WiFi 정보 추가
    doc["wifi_rssi"] = WiFi.RSSI();
    doc["wifi_connected"] = (WiFi.status() == WL_CONNECTED);
    
    // 업타임
    doc["uptime"] = millis() / 1000;
    
    // 직렬화
    char buffer[512];
    serializeJson(doc, buffer);
    
    // MQTT 발행
    bool success = client.publish(TOPIC_STATUS, buffer, MQTT_QOS);
    
    if (success) {
        DEBUG_PRINTLN("Status reported successfully");
    } else {
        DEBUG_PRINTLN("Status report failed");
    }
}

