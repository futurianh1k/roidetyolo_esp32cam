/**
 * MQTT 모듈 헤더
 */

#ifndef MQTT_MODULE_H
#define MQTT_MODULE_H

#include <PubSubClient.h>

// MQTT 콜백
void mqttCallback(char* topic, byte* payload, unsigned int length);

// 제어 명령 처리
void handleCameraControl(const char* action, const char* requestId);
void handleMicrophoneControl(const char* action, const char* requestId);
void handleSpeakerControl(const char* action, const char* audioUrl, const char* requestId);
void handleDisplayControl(const char* action, const char* content, 
                          const char* emojiId, const char* requestId);

// 메시지 발행
void publishControlResponse(const char* requestId, const char* command, 
                           const char* action, bool success, const char* message);
void publishOnlineStatus(PubSubClient& client, bool isOnline);

#endif // MQTT_MODULE_H

