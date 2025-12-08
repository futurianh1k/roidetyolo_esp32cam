/**
 * 상태 모듈 헤더
 */

#ifndef STATUS_MODULE_H
#define STATUS_MODULE_H

#include <PubSubClient.h>

// 시스템 상태
struct SystemStatus {
    int batteryLevel;      // 0-100%
    uint32_t memoryUsage;  // bytes
    uint32_t storageUsage; // bytes
    float temperature;     // Celsius
    int cpuUsage;          // 0-100%
    const char* cameraStatus;
    const char* micStatus;
};

// 상태 보고
void reportStatus(PubSubClient& client);
SystemStatus getSystemStatus();

// 배터리
int getBatteryLevel();

// 메모리
uint32_t getFreeHeap();
uint32_t getTotalHeap();

// 온도
float getCPUTemperature();

#endif // STATUS_MODULE_H

