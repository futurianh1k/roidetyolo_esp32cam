/**
 * Core S3 Management System - 메인 펌웨어
 * 
 * 기능:
 * - WiFi 연결
 * - MQTT 통신
 * - 카메라 스트리밍 (RTSP)
 * - 마이크/스피커 제어
 * - 디스플레이 제어
 * - 상태 보고
 */

#include <M5Unified.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "config.h"
#include "camera_module.h"
#include "mqtt_module.h"
#include "audio_module.h"
#include "display_module.h"
#include "status_module.h"

// ============================================================================
// 전역 변수
// ============================================================================
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

unsigned long lastStatusReport = 0;
unsigned long lastWiFiCheck = 0;
unsigned long lastMqttCheck = 0;

bool cameraActive = false;
bool microphoneActive = false;
bool isInitialized = false;

// ============================================================================
// 함수 선언
// ============================================================================
void setupWiFi();
void setupMQTT();
void reconnectWiFi();
void reconnectMQTT();
void handleLoop();

/**
 * 초기 설정
 */
void setup() {
    // M5Stack 초기화
    auto cfg = M5.config();
    M5.begin(cfg);
    
    // 시리얼 통신 시작
    Serial.begin(115200);
    delay(1000);
    
    DEBUG_PRINTLN("\n=================================");
    DEBUG_PRINTLN("Core S3 Management System");
    DEBUG_PRINTLN("=================================");
    DEBUG_PRINTF("Device ID: %s\n", DEVICE_ID);
    DEBUG_PRINTF("Device Name: %s\n", DEVICE_NAME);
    
    // 디스플레이 초기화
    displayInit();
    displayShowStatus("Initializing...", TFT_YELLOW);
    
    // WiFi 연결
    setupWiFi();
    
    // 카메라 초기화
    DEBUG_PRINTLN("Initializing camera...");
    if (cameraInit()) {
        DEBUG_PRINTLN("Camera initialized successfully");
        displayShowStatus("Camera OK", TFT_GREEN);
        delay(500);
    } else {
        DEBUG_PRINTLN("Camera initialization failed!");
        displayShowStatus("Camera Failed", TFT_RED);
        delay(2000);
    }
    
    // 오디오 초기화
    DEBUG_PRINTLN("Initializing audio...");
    if (audioInit()) {
        DEBUG_PRINTLN("Audio initialized successfully");
        displayShowStatus("Audio OK", TFT_GREEN);
        delay(500);
    } else {
        DEBUG_PRINTLN("Audio initialization failed!");
        displayShowStatus("Audio Failed", TFT_RED);
        delay(2000);
    }
    
    // MQTT 연결
    setupMQTT();
    
    // 초기화 완료
    isInitialized = true;
    displayShowStatus("Ready", TFT_GREEN);
    delay(1000);
    displayClear();
    
    DEBUG_PRINTLN("=================================");
    DEBUG_PRINTLN("System initialized successfully!");
    DEBUG_PRINTLN("=================================\n");
}

/**
 * 메인 루프
 */
void loop() {
    M5.update();
    
    unsigned long currentMillis = millis();
    
    // WiFi 연결 확인 (10초마다)
    if (currentMillis - lastWiFiCheck >= 10000) {
        lastWiFiCheck = currentMillis;
        if (WiFi.status() != WL_CONNECTED) {
            DEBUG_PRINTLN("WiFi disconnected. Reconnecting...");
            reconnectWiFi();
        }
    }
    
    // MQTT 연결 확인 (5초마다)
    if (currentMillis - lastMqttCheck >= 5000) {
        lastMqttCheck = currentMillis;
        if (!mqttClient.connected()) {
            DEBUG_PRINTLN("MQTT disconnected. Reconnecting...");
            reconnectMQTT();
        }
    }
    
    // MQTT 루프
    mqttClient.loop();
    
    // 상태 보고 (10초마다)
    if (currentMillis - lastStatusReport >= STATUS_REPORT_INTERVAL) {
        lastStatusReport = currentMillis;
        reportStatus(mqttClient);
    }
    
    // 카메라 프레임 처리
    if (cameraActive) {
        cameraLoop();
    }
    
    // 마이크 처리
    if (microphoneActive) {
        audioLoop();
    }
    
    // 버튼 처리
    if (M5.BtnA.wasPressed()) {
        DEBUG_PRINTLN("Button A pressed");
        // 카메라 토글
        if (cameraActive) {
            cameraStop();
            cameraActive = false;
            displayShowStatus("Camera OFF", TFT_YELLOW);
        } else {
            cameraStart();
            cameraActive = true;
            displayShowStatus("Camera ON", TFT_GREEN);
        }
    }
    
    if (M5.BtnB.wasPressed()) {
        DEBUG_PRINTLN("Button B pressed");
        // 마이크 토글
        if (microphoneActive) {
            audioStopMicrophone();
            microphoneActive = false;
            displayShowStatus("Mic OFF", TFT_YELLOW);
        } else {
            audioStartMicrophone();
            microphoneActive = true;
            displayShowStatus("Mic ON", TFT_GREEN);
        }
    }
    
    if (M5.BtnC.wasPressed()) {
        DEBUG_PRINTLN("Button C pressed");
        // 상태 정보 표시
        displayShowSystemInfo();
    }
    
    delay(10);
}

/**
 * WiFi 연결 설정
 */
void setupWiFi() {
    DEBUG_PRINTLN("Connecting to WiFi...");
    DEBUG_PRINTF("SSID: %s\n", WIFI_SSID);
    
    displayShowStatus("WiFi Connecting...", TFT_YELLOW);
    
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    
    unsigned long startAttemptTime = millis();
    
    while (WiFi.status() != WL_CONNECTED && 
           millis() - startAttemptTime < WIFI_CONNECT_TIMEOUT) {
        delay(500);
        DEBUG_PRINT(".");
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        DEBUG_PRINTLN("\nWiFi connected!");
        DEBUG_PRINTF("IP Address: %s\n", WiFi.localIP().toString().c_str());
        DEBUG_PRINTF("Signal Strength: %d dBm\n", WiFi.RSSI());
        
        displayShowStatus("WiFi Connected", TFT_GREEN);
        delay(1000);
    } else {
        DEBUG_PRINTLN("\nWiFi connection failed!");
        displayShowStatus("WiFi Failed", TFT_RED);
        delay(2000);
    }
}

/**
 * WiFi 재연결
 */
void reconnectWiFi() {
    displayShowStatus("WiFi Reconnecting...", TFT_YELLOW);
    
    WiFi.disconnect();
    delay(1000);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    
    unsigned long startAttemptTime = millis();
    
    while (WiFi.status() != WL_CONNECTED && 
           millis() - startAttemptTime < WIFI_CONNECT_TIMEOUT) {
        delay(500);
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        DEBUG_PRINTLN("WiFi reconnected!");
        displayShowStatus("WiFi Connected", TFT_GREEN);
        delay(500);
        displayClear();
    }
}

/**
 * MQTT 연결 설정
 */
void setupMQTT() {
    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
    mqttClient.setCallback(mqttCallback);
    mqttClient.setKeepAlive(MQTT_KEEPALIVE);
    
    reconnectMQTT();
}

/**
 * MQTT 재연결
 */
void reconnectMQTT() {
    if (WiFi.status() != WL_CONNECTED) {
        return;
    }
    
    displayShowStatus("MQTT Connecting...", TFT_YELLOW);
    
    String clientId = String(MQTT_CLIENT_ID_PREFIX) + String(DEVICE_ID);
    
    DEBUG_PRINTF("Connecting to MQTT broker: %s:%d\n", MQTT_BROKER, MQTT_PORT);
    DEBUG_PRINTF("Client ID: %s\n", clientId.c_str());
    
    if (mqttClient.connect(clientId.c_str(), MQTT_USERNAME, MQTT_PASSWORD)) {
        DEBUG_PRINTLN("MQTT connected!");
        
        // 제어 토픽 구독
        mqttClient.subscribe(TOPIC_CONTROL_CAMERA, MQTT_QOS);
        mqttClient.subscribe(TOPIC_CONTROL_MICROPHONE, MQTT_QOS);
        mqttClient.subscribe(TOPIC_CONTROL_SPEAKER, MQTT_QOS);
        mqttClient.subscribe(TOPIC_CONTROL_DISPLAY, MQTT_QOS);
        
        DEBUG_PRINTLN("Subscribed to control topics");
        
        displayShowStatus("MQTT Connected", TFT_GREEN);
        delay(500);
        displayClear();
        
        // 연결 성공 메시지 발행
        publishOnlineStatus(mqttClient, true);
        
    } else {
        DEBUG_PRINTF("MQTT connection failed, rc=%d\n", mqttClient.state());
        displayShowStatus("MQTT Failed", TFT_RED);
        delay(1000);
    }
}

