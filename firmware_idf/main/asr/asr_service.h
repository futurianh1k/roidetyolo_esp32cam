#ifndef ASR_SERVICE_H
#define ASR_SERVICE_H

#include "../audio/audio_service.h"
#include "../network/websocket_client.h"
#include <functional>
#include <memory>
#include <string>

/**
 * ASRService - 음성인식 서비스
 *
 * 기능:
 * - ASR 서버와 세션 관리
 * - 오디오 스트림 전송
 * - 인식 결과 수신 및 처리
 */
class ASRService {
public:
  ASRService();
  ~ASRService();

  /**
   * 초기화
   */
  bool Initialize(AudioService *audio_service);

  /**
   * 음성인식 세션 시작
   * @param language 언어 코드 (예: "ko", "en")
   * @param ws_url WebSocket URL (제공되면 사용, 없으면 ASR 서버에서 세션 생성)
   * @return true if successful
   */
  bool StartSession(const std::string &language = "ko",
                    const std::string &ws_url = "");

  /**
   * 음성인식 세션 종료
   */
  void StopSession();

  /**
   * 세션 활성 상태 확인
   */
  bool IsSessionActive() const { return session_active_; }

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

private:
  AudioService *audio_service_ = nullptr;
  WebSocketClient *ws_client_ = nullptr;
  bool session_active_ = false;
  std::string session_id_;
  std::string ws_url_;

  RecognitionCallback recognition_callback_;

  bool CreateASRSession(const std::string &language);
  void OnRecognitionResult(const std::string &text, bool is_final,
                           bool is_emergency);
  void OnWebSocketConnected(bool connected);
  void SendAudioToASR();

  static void AudioStreamTask(void *arg);
  void AudioStreamTaskImpl();
  TaskHandle_t audio_stream_task_handle_ = nullptr;
};

#endif // ASR_SERVICE_H
