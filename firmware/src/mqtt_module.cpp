/**
 * MQTT 모듈
 *
 * MQTT 메시지 처리 및 발행
 * ASR (음성인식) 모드 지원 추가
 */

#include "mqtt_module.h"
#include "audio_module.h"
#include "camera_module.h"
#include "camera_module.h" // cameraSetSink, cameraClearSink
#include "config.h"
#include "display_module.h"
#include "websocket_module.h"
#include <Arduino.h>
#include <ArduinoJson.h>
#include <PubSubClient.h>


// 외부 변수
extern bool cameraActive;
extern bool microphoneActive;

/**
 * MQTT 메시지 수신 콜백
 */
void mqttCallback(char *topic, byte *payload, unsigned int length) {
  DEBUG_PRINTF("MQTT message received: %s\n", topic);

  // JSON 파싱 (ASR 명령을 위해 더 큰 버퍼 사용)
  StaticJsonDocument<1024> doc;
  DeserializationError error = deserializeJson(doc, payload, length);

  if (error) {
    DEBUG_PRINTF("JSON parsing failed: %s\n", error.c_str());
    return;
  }

  // 명령 추출
  const char *command = doc["command"];
  const char *action = doc["action"];
  const char *requestId = doc["request_id"];

  DEBUG_PRINTF("Command: %s, Action: %s\n", command, action);

  // 토픽별 처리
  String topicStr = String(topic);

  if (topicStr.endsWith("/camera")) {
    // ✨ 영상 sink 관련 파라미터 추출
    const char *sinkUrl = doc["sink_url"] | nullptr;
    const char *streamMode = doc["stream_mode"] | nullptr;
    int frameInterval = doc["frame_interval"] | 1000;

    handleCameraControl(action, requestId, sinkUrl, streamMode, frameInterval);
  } else if (topicStr.endsWith("/microphone")) {
    // ✨ ASR 관련 파라미터 추출 (있을 수도 있고 없을 수도 있음)
    const char *sessionId = doc["session_id"] | nullptr;
    const char *wsUrl = doc["ws_url"] | nullptr;

    handleMicrophoneControl(action, requestId, sessionId, wsUrl);
  } else if (topicStr.endsWith("/speaker")) {
    const char *audioUrl = doc["audio_url"];
    int volume = doc["volume"] | 70; // 기본값 70%

    // 볼륨 설정
    if (volume >= 0 && volume <= 100) {
      audioSetVolume((uint8_t)volume);
    }

    handleSpeakerControl(action, audioUrl, requestId);
  } else if (topicStr.endsWith("/display")) {
    const char *content = doc["content"];
    const char *emojiId = doc["emoji_id"];
    handleDisplayControl(action, content, emojiId, requestId);
  } else if (topicStr.endsWith("/system")) {
    handleSystemControl(action, requestId);
  }
}

/**
 * 카메라 제어 처리 (영상 sink 전송 포함)
 *
 * @param action 액션 (start, pause, stop)
 * @param requestId 요청 ID
 * @param sinkUrl 영상 sink 주소 (start일 때만 사용)
 * @param streamMode 전송 방식 (start일 때만 사용)
 * @param frameInterval 프레임 간격 (ms, start일 때만 사용)
 */
void handleCameraControl(const char *action, const char *requestId,
                         const char *sinkUrl, const char *streamMode,
                         int frameInterval) {
  bool success = false;
  String message = "";

  if (strcmp(action, "start") == 0) {
    // ✨ 영상 sink 설정 (있을 경우)
    if (sinkUrl && streamMode) {
      DEBUG_PRINTLN("📹 영상 sink 설정 수신");
      DEBUG_PRINTF("   URL: %s\n", sinkUrl);
      DEBUG_PRINTF("   모드: %s\n", streamMode);
      DEBUG_PRINTF("   주기: %d ms\n", frameInterval);

      cameraSetSink(sinkUrl, streamMode, frameInterval);
    }

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
  } else if (strcmp(action, "pause") == 0) {
    cameraPause();
    success = true;
    message = "Camera paused";
    displayShowStatus("Camera PAUSED", TFT_YELLOW);
    DEBUG_PRINTLN("Camera paused");
  } else if (strcmp(action, "stop") == 0) {
    cameraStop();
    cameraClearSink(); // ✨ sink 설정 초기화
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
 * 마이크 제어 처리 (ASR 모드 포함)
 *
 * @param action 액션 (start, pause, stop, start_asr, stop_asr)
 * @param requestId 요청 ID
 * @param sessionId ASR 세션 ID (start_asr일 때만 사용)
 * @param wsUrl WebSocket URL (start_asr일 때만 사용)
 */
void handleMicrophoneControl(const char *action, const char *requestId,
                             const char *sessionId, const char *wsUrl) {
  bool success = false;
  String message = "";

  if (strcmp(action, "start") == 0) {
    // 일반 마이크 시작
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
  } else if (strcmp(action, "start_asr") == 0) {
    // ✨ ASR 모드 시작
    DEBUG_PRINTLN("🎤 ASR 모드 시작 요청");
    DEBUG_PRINTF("   Session ID: %s\n", sessionId ? sessionId : "null");
    DEBUG_PRINTF("   WebSocket URL: %s\n", wsUrl ? wsUrl : "null");

    if (!sessionId || !wsUrl) {
      message = "ASR start failed: missing session_id or ws_url";
      DEBUG_PRINTLN("❌ ASR 시작 실패: session_id 또는 ws_url 없음");
    } else {
      // WebSocket 연결
      if (websocketConnect(sessionId, wsUrl)) {
        // ASR 모드로 마이크 시작
        if (audioStartASRMode()) {
          success = true;
          message = "ASR mode started";
          displayShowStatus("ASR Recording", TFT_GREEN);
          DEBUG_PRINTLN("✅ ASR 모드 시작 완료");
        } else {
          message = "ASR mode start failed";
          DEBUG_PRINTLN("❌ ASR 모드 시작 실패");
          websocketDisconnect();
        }
      } else {
        message = "WebSocket connection failed";
        DEBUG_PRINTLN("❌ WebSocket 연결 실패");
      }
    }
  } else if (strcmp(action, "stop_asr") == 0) {
    // ✨ ASR 모드 종료
    DEBUG_PRINTLN("🛑 ASR 모드 종료 요청");

    audioStopASRMode();
    websocketDisconnect();

    success = true;
    message = "ASR mode stopped";
    displayShowStatus("ASR Stopped", TFT_YELLOW);
    DEBUG_PRINTLN("✅ ASR 모드 종료 완료");
  } else if (strcmp(action, "pause") == 0) {
    audioPauseMicrophone();
    success = true;
    message = "Microphone paused";
    displayShowStatus("Mic PAUSED", TFT_YELLOW);
    DEBUG_PRINTLN("Microphone paused");
  } else if (strcmp(action, "stop") == 0) {
    audioStopMicrophone();
    microphoneActive = false;
    success = true;
    message = "Microphone stopped";
    displayShowStatus("Mic OFF", TFT_YELLOW);
    DEBUG_PRINTLN("Microphone stopped");
  }

  // 응답 발행
  publishControlResponse(requestId, "microphone", action, success,
                         message.c_str());
}

/**
 * 스피커 제어 처리
 */
void handleSpeakerControl(const char *action, const char *audioUrl,
                          const char *requestId) {
  bool success = false;
  String message = "";

  if (strcmp(action, "play") == 0) {
    if (audioUrl && strlen(audioUrl) > 0) {
      // 볼륨 설정이 있으면 적용 (JSON에서 volume 필드 확인)
      // 참고: 이 함수는 이미 JSON에서 파싱된 후 호출됨

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
  } else if (strcmp(action, "stop") == 0) {
    audioStopSpeaker();
    success = true;
    message = "Speaker stopped";
    displayShowStatus("Audio Stopped", TFT_YELLOW);
    DEBUG_PRINTLN("Speaker stopped");
  }

  // 응답 발행
  publishControlResponse(requestId, "speaker", action, success,
                         message.c_str());
}

/**
 * 디스플레이 제어 처리
 */
void handleDisplayControl(const char *action, const char *content,
                          const char *emojiId, const char *requestId) {
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
  } else if (strcmp(action, "show_emoji") == 0) {
    if (emojiId && strlen(emojiId) > 0) {
      displayShowEmoji(emojiId);
      success = true;
      message = "Emoji displayed";
      DEBUG_PRINTF("Displaying emoji: %s\n", emojiId);
    } else {
      message = "Emoji ID required";
      DEBUG_PRINTLN("Emoji ID required");
    }
  } else if (strcmp(action, "clear") == 0) {
    displayClear();
    success = true;
    message = "Display cleared";
    DEBUG_PRINTLN("Display cleared");
  }

  // 응답 발행
  publishControlResponse(requestId, "display", action, success,
                         message.c_str());
}

/**
 * 시스템 제어 처리
 */
void handleSystemControl(const char *action, const char *requestId) {
  bool success = false;
  String message = "";

  if (strcmp(action, "restart") == 0) {
    success = true;
    message = "Device restarting";
    displayShowStatus("Restarting...", TFT_YELLOW);
    DEBUG_PRINTLN("Device restart requested");

    // 응답 발행
    publishControlResponse(requestId, "system", action, success,
                           message.c_str());

    // 응답 전송 완료 대기
    delay(1000);

    // ESP32 재시작
    ESP.restart();
  } else {
    message = "Unknown system command";
    publishControlResponse(requestId, "system", action, false, message.c_str());
  }
}

/**
 * 제어 응답 발행
 */
void publishControlResponse(const char *requestId, const char *command,
                            const char *action, bool success,
                            const char *message) {
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
void publishOnlineStatus(PubSubClient &client, bool isOnline) {
  StaticJsonDocument<128> doc;
  doc["device_id"] = DEVICE_ID;
  doc["online"] = isOnline;
  doc["timestamp"] = millis() / 1000;

  char buffer[128];
  serializeJson(doc, buffer);

  client.publish(TOPIC_STATUS, buffer, MQTT_QOS);
  DEBUG_PRINTF("Published online status: %s\n", isOnline ? "true" : "false");
}
