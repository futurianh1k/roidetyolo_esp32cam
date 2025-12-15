/**
 * Simple RTSP Server for ESP32
 *
 * 간단한 RTSP/RTP 스트리밍 서버
 *
 * 참고자료:
 * - Micro-RTSP: https://github.com/geeksville/Micro-RTSP
 * - RFC 2326 (RTSP): https://tools.ietf.org/html/rfc2326
 * - RFC 3550 (RTP): https://tools.ietf.org/html/rfc3550
 */

#ifndef RTSP_SERVER_H
#define RTSP_SERVER_H

#include <freertos/FreeRTOS.h>
#include <freertos/semphr.h>
#include <freertos/task.h>
#include <functional>
#include <lwip/sockets.h>
#include <string>
#include <vector>


// RTSP 설정
#define RTSP_PORT 554
#define RTP_PORT_BASE 5000
#define RTSP_MAX_CLIENTS 2
#define RTSP_BUFFER_SIZE 2048

// RTP 페이로드 타입
#define RTP_PAYLOAD_JPEG 26

// 프레임 콜백 타입
using RTSPFrameCallback = std::function<bool(uint8_t **, size_t *)>;

/**
 * RTSP 클라이언트 세션
 */
struct RTSPSession {
  int socket;
  int rtp_socket;
  struct sockaddr_in client_addr;
  uint16_t client_rtp_port;
  uint32_t ssrc;
  uint16_t sequence;
  uint32_t timestamp;
  bool playing;
  char session_id[16];
};

/**
 * RTSPServer - 간단한 RTSP 스트리밍 서버
 */
class RTSPServer {
public:
  RTSPServer();
  ~RTSPServer();

  // 프레임 제공 콜백 설정
  void SetFrameCallback(RTSPFrameCallback callback);

  // 서버 시작/중지
  bool Start();
  void Stop();

  // 상태 확인
  bool IsRunning() const { return running_; }
  int GetClientCount() const { return active_clients_; }

private:
  int server_socket_ = -1;
  bool running_ = false;
  int active_clients_ = 0;

  TaskHandle_t server_task_ = nullptr;
  TaskHandle_t stream_task_ = nullptr;
  SemaphoreHandle_t clients_mutex_ = nullptr;

  RTSPSession sessions_[RTSP_MAX_CLIENTS];
  RTSPFrameCallback frame_callback_ = nullptr;

  // 서버 태스크
  static void ServerTask(void *arg);
  void ServerTaskImpl();

  // 스트리밍 태스크
  static void StreamTask(void *arg);
  void StreamTaskImpl();

  // RTSP 요청 처리
  void HandleClient(int client_socket);
  void HandleRTSPRequest(RTSPSession *session, const char *request);

  // RTSP 응답 생성
  void SendOPTIONS(RTSPSession *session, int cseq);
  void SendDESCRIBE(RTSPSession *session, int cseq);
  void SendSETUP(RTSPSession *session, int cseq, uint16_t client_rtp_port);
  void SendPLAY(RTSPSession *session, int cseq);
  void SendTEARDOWN(RTSPSession *session, int cseq);

  // RTP 전송
  bool SendRTPFrame(RTSPSession *session, const uint8_t *jpeg_data,
                    size_t jpeg_len);

  // 유틸리티
  int FindFreeSession();
  void CloseSession(RTSPSession *session);
  void GenerateSessionId(char *buf, size_t len);
};

#endif // RTSP_SERVER_H
