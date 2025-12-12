#ifndef WEBSOCKET_CLIENT_H
#define WEBSOCKET_CLIENT_H

#include <esp_websocket_client.h> // ESP-IDF WebSocket client header
#include <freertos/FreeRTOS.h>
#include <freertos/queue.h>
#include <freertos/task.h>
#include <functional>
#include <memory>
#include <string>


/**
 * WebSocketClient - ASR 서버와 통신하는 WebSocket 클라이언트
 *
 * 기능:
 * - ASR 서버 WebSocket 연결
 * - 오디오 스트림 전송
 * - 인식 결과 수신
 * - 자동 재연결
 */
class WebSocketClient {
public:
  WebSocketClient();
  ~WebSocketClient();

  /**
   * WebSocket 연결
   * @param url WebSocket URL (예: ws://10.10.11.17:8001/ws/asr/{session_id})
   * @return true if connection successful
   */
  bool Connect(const std::string &url);

  /**
   * WebSocket 연결 해제
   */
  void Disconnect();

  /**
   * 연결 상태 확인
   */
  bool IsConnected() const { return connected_; }

  /**
   * 오디오 데이터 전송 (PCM 16-bit, 16kHz, mono)
   * @param data PCM 오디오 데이터
   * @param length 데이터 길이 (bytes)
   * @return true if sent successfully
   */
  bool SendAudio(const uint8_t *data, size_t length);

  /**
   * 텍스트 메시지 전송
   */
  bool SendText(const std::string &message);

  /**
   * 인식 결과 콜백 타입
   * Parameters: text, is_final, is_emergency
   */
  using RecognitionCallback = std::function<void(
      const std::string &text, bool is_final, bool is_emergency)>;

  /**
   * 인식 결과 콜백 설정
   */
  void SetRecognitionCallback(RecognitionCallback callback);

  /**
   * 연결 상태 변경 콜백 타입
   * Parameters: connected
   */
  using ConnectionCallback = std::function<void(bool connected)>;

  /**
   * 연결 상태 변경 콜백 설정
   */
  void SetConnectionCallback(ConnectionCallback callback);

  /**
   * WebSocket 루프 실행 (별도 태스크에서 호출)
   */
  void Loop();

  /**
   * 연결 상태 설정 (내부 사용)
   */
  void SetConnected(bool connected) { connected_ = connected; }

  /**
   * 연결 콜백 호출 (정적 이벤트 핸들러에서 사용)
   */
  void InvokeConnectionCallback(bool connected);

  /**
   * 메시지 처리 (정적 이벤트 핸들러에서 사용)
   */
  void ProcessReceivedMessage(const std::string &message);

private:
  std::string url_;
  bool connected_ = false;
  TaskHandle_t task_handle_ = nullptr;
  QueueHandle_t send_queue_ = nullptr;

  RecognitionCallback recognition_callback_;
  ConnectionCallback connection_callback_;

  // ESP-IDF HTTP 클라이언트 핸들
  void *http_client_ = nullptr;
  esp_websocket_client_handle_t ws_handle_ = nullptr;

  static void WebSocketTask(void *arg);
  void WebSocketTaskImpl();

  bool ConnectInternal();
  void DisconnectInternal();
};

#endif // WEBSOCKET_CLIENT_H
