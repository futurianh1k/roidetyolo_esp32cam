/**
 * MQTT 모듈
 * 
 * MQTT 메시지 처리 및 발행
 */

#include <Arduino.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "mqtt_module.h"
#include "config.h"
#include "camera_module.h"
#include "audio_module.h"
#include "display_module.h"

// 외부 변수
extern bool cameraActive;
extern bool microphoneActive;

/**
 * MQTT 메시지 수신 콜백
 */
void mqttCallback(char* topic, byte* payload, unsigned int length) {
    DEBUG_PRINTF("MQTT message received: %s\n", topic);
    
    // JSON 파싱
    StaticJsonDocument<512> doc;
    DeserializationError error = deserializeJson(doc, payload, length);
    
    if (error) {
        DEBUG_PRINTF("JSON parsing failed: %s\n", error.c_str());
        return;
    }
    
    // 명령 추출
    const char* command = doc["command"];
    const char* action = doc["action"];
    const char* requestId = doc["request_id"];
    
    DEBUG_PRINTF("Command: %s, Action: %s\n", command, action);
    
    // 토픽별 처리
    String topicStr = String(topic);
    
    if (topicStr.endsWith("/camera")) {
        handleCameraControl(action, requestId);
    }
    else if (topicStr.endsWith("/microphone")) {
        handleMicrophoneControl(action, requestId);
    }
    else if (topicStr.endsWith("/speaker")) {
        const char* audioUrl = doc["audio_url"];
        handleSpeakerControl(action, audioUrl, requestId);
    }
    else if (topicStr.endsWith("/display")) {
        const char* content = doc["content"];
        const char* emojiId = doc["emoji_id"];
        handleDisplayControl(action, content, emojiId, requestId);
    }
}

/**
 * 카메라 제어 처리
 */
void handleCameraControl(const char* action, const char* requestId) {
    bool success = false;
    String message = "";
    
    if (strcmp(action, "start") == 0) {
        if (cameraStart()) {
            cameraActive = true;
            success = true;
            message = "Camera started";
            displayShowStatus("Camera ON", TFT_GREEN);
            DEBUG_PRINTLN("Camera started");
        } else {
            message = "Camera start failed";
            DEBUG_PRINTLN("Camera start failed");
        }
    }
    else if (strcmp(action, "pause") == 0) {
        cameraPause();
        success = true;
        message = "Camera paused";
        displayShowStatus("Camera PAUSED", TFT_YELLOW);
        DEBUG_PRINTLN("Camera paused");
    }
    else if (strcmp(action, "stop") == 0) {
        cameraStop();
        cameraActive = false;
        success = true;
        message = "Camera stopped";
        displayShowStatus("Camera OFF", TFT_YELLOW);
        DEBUG_PRINTLN("Camera stopped");
    }
    
    // 응답 발행
    publishControlResponse(requestId, "camera", action, success, message.c_str());
}

/**
 * 마이크 제어 처리
 */
void handleMicrophoneControl(const char* action, const char* requestId) {
    bool success = false;
    String message = "";
    
    if (strcmp(action, "start") == 0) {
        if (audioStartMicrophone()) {
            microphoneActive = true;
            success = true;
            message = "Microphone started";
            displayShowStatus("Mic ON", TFT_GREEN);
            DEBUG_PRINTLN("Microphone started");
        } else {
            message = "Microphone start failed";
            DEBUG_PRINTLN("Microphone start failed");
        }
    }
    else if (strcmp(action, "pause") == 0) {
        audioPauseMicrophone();
        success = true;
        message = "Microphone paused";
        displayShowStatus("Mic PAUSED", TFT_YELLOW);
        DEBUG_PRINTLN("Microphone paused");
    }
    else if (strcmp(action, "stop") == 0) {
        audioStopMicrophone();
        microphoneActive = false;
        success = true;
        message = "Microphone stopped";
        displayShowStatus("Mic OFF", TFT_YELLOW);
        DEBUG_PRINTLN("Microphone stopped");
    }
    
    // 응답 발행
    publishControlResponse(requestId, "microphone", action, success, message.c_str());
}

/**
 * 스피커 제어 처리
 */
void handleSpeakerControl(const char* action, const char* audioUrl, const char* requestId) {
    bool success = false;
    String message = "";
    
    if (strcmp(action, "play") == 0) {
        if (audioUrl && strlen(audioUrl) > 0) {
            if (audioPlayURL(audioUrl)) {
                success = true;
                message = "Speaker playing";
                displayShowStatus("Playing Audio", TFT_GREEN);
                DEBUG_PRINTF("Playing audio: %s\n", audioUrl);
            } else {
                message = "Audio playback failed";
                DEBUG_PRINTLN("Audio playback failed");
            }
        } else {
            message = "Audio URL required";
            DEBUG_PRINTLN("Audio URL required");
        }
    }
    else if (strcmp(action, "stop") == 0) {
        audioStopSpeaker();
        success = true;
        message = "Speaker stopped";
        displayShowStatus("Audio Stopped", TFT_YELLOW);
        DEBUG_PRINTLN("Speaker stopped");
    }
    
    // 응답 발행
    publishControlResponse(requestId, "speaker", action, success, message.c_str());
}

/**
 * 디스플레이 제어 처리
 */
void handleDisplayControl(const char* action, const char* content, 
                          const char* emojiId, const char* requestId) {
    bool success = false;
    String message = "";
    
    if (strcmp(action, "show_text") == 0) {
        if (content && strlen(content) > 0) {
            displayShowText(content);
            success = true;
            message = "Text displayed";
            DEBUG_PRINTF("Displaying text: %s\n", content);
        } else {
            message = "Text content required";
            DEBUG_PRINTLN("Text content required");
        }
    }
    else if (strcmp(action, "show_emoji") == 0) {
        if (emojiId && strlen(emojiId) > 0) {
            displayShowEmoji(emojiId);
            success = true;
            message = "Emoji displayed";
            DEBUG_PRINTF("Displaying emoji: %s\n", emojiId);
        } else {
            message = "Emoji ID required";
            DEBUG_PRINTLN("Emoji ID required");
        }
    }
    else if (strcmp(action, "clear") == 0) {
        displayClear();
        success = true;
        message = "Display cleared";
        DEBUG_PRINTLN("Display cleared");
    }
    
    // 응답 발행
    publishControlResponse(requestId, "display", action, success, message.c_str());
}

/**
 * 제어 응답 발행
 */
void publishControlResponse(const char* requestId, const char* command, 
                           const char* action, bool success, const char* message) {
    extern PubSubClient mqttClient;
    
    StaticJsonDocument<256> doc;
    doc["request_id"] = requestId;
    doc["command"] = command;
    doc["action"] = action;
    doc["success"] = success;
    doc["message"] = message;
    doc["timestamp"] = millis() / 1000;
    
    char buffer[256];
    serializeJson(doc, buffer);
    
    mqttClient.publish(TOPIC_RESPONSE, buffer, MQTT_QOS);
    DEBUG_PRINTF("Published response: %s\n", buffer);
}

/**
 * 온라인 상태 발행
 */
void publishOnlineStatus(PubSubClient& client, bool isOnline) {
    StaticJsonDocument<128> doc;
    doc["device_id"] = DEVICE_ID;
    doc["online"] = isOnline;
    doc["timestamp"] = millis() / 1000;
    
    char buffer[128];
    serializeJson(doc, buffer);
    
    client.publish(TOPIC_STATUS, buffer, MQTT_QOS);
    DEBUG_PRINTF("Published online status: %s\n", isOnline ? "true" : "false");
}

