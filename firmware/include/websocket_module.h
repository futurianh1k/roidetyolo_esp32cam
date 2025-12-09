/**
 * WebSocket 모듈 헤더
 *
 * ASR 서버와 WebSocket 통신을 담당하는 모듈
 *
 * 주요 기능:
 * - WebSocket 클라이언트 연결/해제
 * - 오디오 데이터 Base64 인코딩 및 전송
 * - 인식 결과 수신 및 처리
 * - Ping-Pong (연결 유지)
 *
 * 참고: ArduinoWebsockets 라이브러리 사용
 */

#ifndef WEBSOCKET_MODULE_H
#define WEBSOCKET_MODULE_H

#include <Arduino.h>
#include <ArduinoWebsockets.h>

using namespace websockets;

/**
 * WebSocket 초기화
 */
void websocketInit();

/**
 * ASR 서버에 연결
 *
 * @param sessionId ASR 세션 ID (UUID)
 * @param wsUrl WebSocket URL (예: "ws://192.168.1.100:8001/ws/asr/uuid-xxxx")
 * @return 연결 성공 여부
 */
bool websocketConnect(const char *sessionId, const char *wsUrl);

/**
 * WebSocket 연결 해제
 */
void websocketDisconnect();

/**
 * WebSocket 연결 상태 확인
 *
 * @return true: 연결됨, false: 연결 안 됨
 */
bool websocketIsConnected();

/**
 * 오디오 청크 전송
 *
 * int16 PCM 오디오를 Base64로 인코딩하여 JSON 메시지로 전송
 *
 * @param audioData int16 PCM 오디오 버퍼
 * @param sampleCount 샘플 수
 * @param timestamp 타임스탬프 (밀리초)
 * @return 전송 성공 여부
 */
bool websocketSendAudioChunk(const int16_t *audioData, size_t sampleCount,
                             unsigned long timestamp);

/**
 * Ping 전송 (연결 유지)
 *
 * @return 전송 성공 여부
 */
bool websocketSendPing();

/**
 * WebSocket 루프 (메시지 수신 처리)
 *
 * main loop에서 주기적으로 호출해야 함
 */
void websocketLoop();

/**
 * 현재 세션 ID 가져오기
 *
 * @return 세션 ID 문자열
 */
String websocketGetSessionId();

#endif // WEBSOCKET_MODULE_H
