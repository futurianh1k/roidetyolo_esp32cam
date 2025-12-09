/**
 * WebSocket 모듈
 *
 * ASR 서버와 WebSocket 통신 구현
 *
 * 참고:
 * - ArduinoWebsockets 라이브러리:
 * https://github.com/gilmaimon/ArduinoWebsockets
 * - Base64 인코딩: ESP32 Arduino 코어에 포함된 base64.h 사용
 */

#include "websocket_module.h"
#include "config.h"
#include "display_module.h"
#include <ArduinoJson.h>
#include <base64.h> // ESP32 Arduino 코어에 포함된 Base64 라이브러리

// WebSocket 클라이언트
static WebsocketsClient wsClient;

// 세션 정보
static String currentSessionId = "";
static bool isConnected = false;
static unsigned long lastPingTime = 0;
static const unsigned long PING_INTERVAL = 30000; // 30초마다 Ping

// 외부 변수 (다른 모듈에서 참조)
extern bool asrMode;

// 내부 함수 선언
void websocketOnMessage(WebsocketsMessage message);

/**
 * WebSocket 초기화
 *
 * 이벤트 핸들러 설정
 */
void websocketInit() {
  DEBUG_PRINTLN("Initializing WebSocket module...");

  // 메시지 수신 콜백
  wsClient.onMessage(
      [](WebsocketsMessage message) { websocketOnMessage(message); });

  // 연결 이벤트 콜백
  wsClient.onEvent([](WebsocketsEvent event, String data) {
    switch (event) {
    case WebsocketsEvent::ConnectionOpened:
      DEBUG_PRINTLN("✅ WebSocket 연결 성공");
      isConnected = true;
      displayShowStatus("ASR Connected", TFT_GREEN);
      break;

    case WebsocketsEvent::ConnectionClosed:
      DEBUG_PRINTLN("🔌 WebSocket 연결 끊김");
      isConnected = false;
      currentSessionId = "";
      displayShowStatus("ASR Disconnected", TFT_YELLOW);
      break;

    case WebsocketsEvent::GotPing:
      DEBUG_PRINTLN("📡 Ping 수신");
      wsClient.pong();
      break;

    case WebsocketsEvent::GotPong:
      DEBUG_PRINTLN("📡 Pong 수신");
      break;
    }
  });

  DEBUG_PRINTLN("WebSocket module initialized");
}

/**
 * ASR 서버에 연결
 *
 * @param sessionId ASR 세션 ID
 * @param wsUrl WebSocket URL
 * @return 연결 성공 여부
 */
bool websocketConnect(const char *sessionId, const char *wsUrl) {
  if (isConnected) {
    DEBUG_PRINTLN("⚠️ 이미 WebSocket에 연결되어 있습니다");
    return false;
  }

  DEBUG_PRINTF("WebSocket 연결 시도: %s\n", wsUrl);
  DEBUG_PRINTF("Session ID: %s\n", sessionId);

  currentSessionId = String(sessionId);

  // WebSocket 연결
  bool connected = wsClient.connect(wsUrl);

  if (connected) {
    DEBUG_PRINTLN("✅ WebSocket 연결 성공");
    isConnected = true;
    lastPingTime = millis();

    // 연결 확인 메시지 대기 (최대 3초)
    unsigned long startTime = millis();
    while (millis() - startTime < 3000) {
      wsClient.poll();
      if (wsClient.available()) {
        // 환영 메시지 수신
        break;
      }
      delay(10);
    }

    displayShowStatus("ASR Ready", TFT_GREEN);
    return true;
  } else {
    DEBUG_PRINTLN("❌ WebSocket 연결 실패");
    isConnected = false;
    displayShowStatus("ASR Failed", TFT_RED);
    return false;
  }
}

/**
 * WebSocket 연결 해제
 */
void websocketDisconnect() {
  if (!isConnected) {
    DEBUG_PRINTLN("⚠️ WebSocket이 연결되어 있지 않습니다");
    return;
  }

  DEBUG_PRINTLN("WebSocket 연결 해제 중...");

  wsClient.close();
  isConnected = false;
  currentSessionId = "";

  DEBUG_PRINTLN("✅ WebSocket 연결 해제 완료");
  displayShowStatus("ASR Stopped", TFT_YELLOW);
}

/**
 * WebSocket 연결 상태 확인
 */
bool websocketIsConnected() { return isConnected && wsClient.available(); }

/**
 * 오디오 청크 전송
 *
 * int16 PCM → Base64 → JSON → WebSocket
 *
 * @param audioData int16 PCM 오디오 버퍼
 * @param sampleCount 샘플 수
 * @param timestamp 타임스탬프 (밀리초)
 * @return 전송 성공 여부
 */
bool websocketSendAudioChunk(const int16_t *audioData, size_t sampleCount,
                             unsigned long timestamp) {
  if (!websocketIsConnected()) {
    DEBUG_PRINTLN("⚠️ WebSocket 연결 안 됨");
    return false;
  }

  // int16 → bytes
  size_t byteSize = sampleCount * sizeof(int16_t);

  // Base64 인코딩
  String base64Audio = base64::encode((uint8_t *)audioData, byteSize);

  // JSON 메시지 생성
  StaticJsonDocument<4096> doc; // Base64 문자열이 크므로 충분한 크기
  doc["type"] = "audio_chunk";
  doc["data"] = base64Audio;
  doc["timestamp"] = timestamp;

  String jsonMessage;
  serializeJson(doc, jsonMessage);

  // 크기 확인 (디버그)
  DEBUG_PRINTF("📤 오디오 전송: %d samples, %d bytes, Base64: %d chars\n",
               sampleCount, byteSize, base64Audio.length());

  // WebSocket 전송
  bool sent = wsClient.send(jsonMessage);

  if (!sent) {
    DEBUG_PRINTLN("❌ 오디오 전송 실패");
  }

  return sent;
}

/**
 * Ping 전송 (연결 유지)
 */
bool websocketSendPing() {
  if (!websocketIsConnected()) {
    return false;
  }

  StaticJsonDocument<64> doc;
  doc["type"] = "ping";

  String jsonMessage;
  serializeJson(doc, jsonMessage);

  return wsClient.send(jsonMessage);
}

/**
 * WebSocket 메시지 수신 처리
 *
 * 인식 결과, 에러, Pong 등을 처리
 *
 * @param message 수신된 WebSocket 메시지
 */
void websocketOnMessage(WebsocketsMessage message) {
  DEBUG_PRINTLN("📨 WebSocket 메시지 수신");

  // JSON 파싱
  StaticJsonDocument<1024> doc;
  DeserializationError error = deserializeJson(doc, message.data());

  if (error) {
    DEBUG_PRINTF("❌ JSON 파싱 실패: %s\n", error.c_str());
    return;
  }

  // 메시지 타입 확인
  const char *msgType = doc["type"];

  if (!msgType) {
    DEBUG_PRINTLN("⚠️ 메시지 타입 없음");
    return;
  }

  DEBUG_PRINTF("메시지 타입: %s\n", msgType);

  // 타입별 처리
  if (strcmp(msgType, "connected") == 0) {
    // 연결 확인 메시지
    const char *msg = doc["message"];
    DEBUG_PRINTF("✅ ASR 연결: %s\n", msg);

  } else if (strcmp(msgType, "recognition_result") == 0) {
    // 음성인식 결과
    const char *text = doc["text"];
    const char *timestamp = doc["timestamp"];
    float duration = doc["duration"] | 0.0f;
    bool isEmergency = doc["is_emergency"] | false;

    DEBUG_PRINTLN("🎤 인식 결과 수신:");
    DEBUG_PRINTF("   텍스트: %s\n", text);
    DEBUG_PRINTF("   시각: %s\n", timestamp);
    DEBUG_PRINTF("   길이: %.2f초\n", duration);

    if (isEmergency) {
      DEBUG_PRINTLN("   🚨 응급 상황 감지!");
      // 디스플레이에 경고 표시
      displayShowStatus("EMERGENCY!", TFT_RED);
      delay(1000);
    }

    // 디스플레이에 인식 결과 표시
    displayShowText(text);

    DEBUG_PRINTLN("✅ 인식 결과 표시 완료");

  } else if (strcmp(msgType, "processing") == 0) {
    // 처리 중 상태
    const char *msg = doc["message"];
    DEBUG_PRINTF("🗣️ %s\n", msg);
    // 필요시 상태 표시
    // displayShowStatus(msg, TFT_YELLOW);

  } else if (strcmp(msgType, "error") == 0) {
    // 에러 메시지
    const char *errorMsg = doc["message"];
    DEBUG_PRINTF("❌ ASR 에러: %s\n", errorMsg);
    displayShowStatus("ASR Error", TFT_RED);

  } else if (strcmp(msgType, "pong") == 0) {
    // Pong 응답
    DEBUG_PRINTLN("📡 Pong 수신");

  } else {
    DEBUG_PRINTF("⚠️ 알 수 없는 메시지 타입: %s\n", msgType);
  }
}

/**
 * WebSocket 루프
 *
 * 메시지 수신 및 Ping 전송을 처리
 * main loop에서 호출해야 함
 */
void websocketLoop() {
  if (!websocketIsConnected()) {
    return;
  }

  // 메시지 수신 처리
  wsClient.poll();

  // 주기적으로 Ping 전송 (연결 유지)
  unsigned long now = millis();
  if (now - lastPingTime > PING_INTERVAL) {
    DEBUG_PRINTLN("📡 Ping 전송");
    websocketSendPing();
    lastPingTime = now;
  }
}

/**
 * 현재 세션 ID 가져오기
 */
String websocketGetSessionId() { return currentSessionId; }
