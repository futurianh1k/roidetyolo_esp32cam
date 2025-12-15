/**
 * Simple RTSP Server Implementation
 *
 * 간단한 RTSP/RTP 스트리밍 서버 구현
 *
 * 참고자료:
 * - Micro-RTSP: https://github.com/geeksville/Micro-RTSP
 * - RFC 2326 (RTSP): https://tools.ietf.org/html/rfc2326
 */

#include "rtsp_server.h"
#include <cstring>
#include <esp_log.h>
#include <esp_random.h>
#include <esp_timer.h>
#include <lwip/netdb.h>

#define TAG "RTSPServer"

// RTP 헤더 크기
#define RTP_HEADER_SIZE 12

// JPEG RTP 헤더 크기 (RFC 2435)
#define JPEG_HEADER_SIZE 8

// MTU 크기 (UDP 페이로드 제한)
#define RTP_MTU 1400

RTSPServer::RTSPServer() {
  clients_mutex_ = xSemaphoreCreateMutex();
  memset(sessions_, 0, sizeof(sessions_));
  for (int i = 0; i < RTSP_MAX_CLIENTS; i++) {
    sessions_[i].socket = -1;
    sessions_[i].rtp_socket = -1;
  }
}

RTSPServer::~RTSPServer() {
  Stop();
  if (clients_mutex_) {
    vSemaphoreDelete(clients_mutex_);
  }
}

void RTSPServer::SetFrameCallback(RTSPFrameCallback callback) {
  frame_callback_ = callback;
}

bool RTSPServer::Start() {
  if (running_) {
    return true;
  }

  ESP_LOGI(TAG, "Starting RTSP server on port %d", RTSP_PORT);

  // 서버 소켓 생성
  server_socket_ = socket(AF_INET, SOCK_STREAM, 0);
  if (server_socket_ < 0) {
    ESP_LOGE(TAG, "Failed to create socket");
    return false;
  }

  // 소켓 옵션 설정
  int opt = 1;
  setsockopt(server_socket_, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

  // 바인딩
  struct sockaddr_in server_addr = {};
  server_addr.sin_family = AF_INET;
  server_addr.sin_addr.s_addr = INADDR_ANY;
  server_addr.sin_port = htons(RTSP_PORT);

  if (bind(server_socket_, (struct sockaddr *)&server_addr,
           sizeof(server_addr)) < 0) {
    ESP_LOGE(TAG, "Failed to bind socket");
    close(server_socket_);
    server_socket_ = -1;
    return false;
  }

  // 리스닝
  if (listen(server_socket_, RTSP_MAX_CLIENTS) < 0) {
    ESP_LOGE(TAG, "Failed to listen");
    close(server_socket_);
    server_socket_ = -1;
    return false;
  }

  running_ = true;

  // 서버 태스크 시작
  xTaskCreatePinnedToCore(ServerTask, "rtsp_server", 4096, this, 3,
                          &server_task_, 1);

  // 스트리밍 태스크 시작
  xTaskCreatePinnedToCore(StreamTask, "rtsp_stream", 8192, this, 4,
                          &stream_task_, 1);

  ESP_LOGI(TAG, "RTSP server started");
  return true;
}

void RTSPServer::Stop() {
  if (!running_) {
    return;
  }

  ESP_LOGI(TAG, "Stopping RTSP server...");
  running_ = false;

  // 서버 소켓 닫기
  if (server_socket_ >= 0) {
    close(server_socket_);
    server_socket_ = -1;
  }

  // 모든 세션 닫기
  for (int i = 0; i < RTSP_MAX_CLIENTS; i++) {
    CloseSession(&sessions_[i]);
  }

  // 태스크 종료 대기
  if (server_task_) {
    vTaskDelay(pdMS_TO_TICKS(100));
    server_task_ = nullptr;
  }
  if (stream_task_) {
    vTaskDelay(pdMS_TO_TICKS(100));
    stream_task_ = nullptr;
  }

  ESP_LOGI(TAG, "RTSP server stopped");
}

void RTSPServer::ServerTask(void *arg) {
  RTSPServer *server = static_cast<RTSPServer *>(arg);
  server->ServerTaskImpl();
  vTaskDelete(nullptr);
}

void RTSPServer::ServerTaskImpl() {
  while (running_) {
    struct sockaddr_in client_addr;
    socklen_t addr_len = sizeof(client_addr);

    // 타임아웃 설정
    struct timeval tv = {1, 0}; // 1초 타임아웃
    setsockopt(server_socket_, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));

    int client_socket =
        accept(server_socket_, (struct sockaddr *)&client_addr, &addr_len);
    if (client_socket < 0) {
      continue; // 타임아웃 또는 에러
    }

    ESP_LOGI(TAG, "New RTSP client connected from %s",
             inet_ntoa(client_addr.sin_addr));

    // 세션 찾기
    int session_idx = FindFreeSession();
    if (session_idx < 0) {
      ESP_LOGW(TAG, "Max clients reached, rejecting connection");
      close(client_socket);
      continue;
    }

    RTSPSession *session = &sessions_[session_idx];
    session->socket = client_socket;
    session->client_addr = client_addr;
    session->ssrc = esp_random();
    session->sequence = 0;
    session->timestamp = 0;
    session->playing = false;
    GenerateSessionId(session->session_id, sizeof(session->session_id));

    active_clients_++;

    // 클라이언트 처리
    HandleClient(client_socket);
  }
}

void RTSPServer::HandleClient(int client_socket) {
  char buffer[RTSP_BUFFER_SIZE];
  RTSPSession *session = nullptr;

  // 세션 찾기
  for (int i = 0; i < RTSP_MAX_CLIENTS; i++) {
    if (sessions_[i].socket == client_socket) {
      session = &sessions_[i];
      break;
    }
  }

  if (!session) {
    close(client_socket);
    return;
  }

  while (running_ && session->socket >= 0) {
    struct timeval tv = {5, 0}; // 5초 타임아웃
    setsockopt(client_socket, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));

    int len = recv(client_socket, buffer, sizeof(buffer) - 1, 0);
    if (len <= 0) {
      break; // 연결 종료 또는 에러
    }

    buffer[len] = '\0';
    ESP_LOGD(TAG, "RTSP Request:\n%s", buffer);

    HandleRTSPRequest(session, buffer);
  }

  CloseSession(session);
  active_clients_--;
  ESP_LOGI(TAG, "RTSP client disconnected");
}

void RTSPServer::HandleRTSPRequest(RTSPSession *session, const char *request) {
  // CSeq 추출
  int cseq = 0;
  const char *cseq_str = strstr(request, "CSeq:");
  if (cseq_str) {
    cseq = atoi(cseq_str + 5);
  }

  // 메서드 파싱
  if (strncmp(request, "OPTIONS", 7) == 0) {
    SendOPTIONS(session, cseq);
  } else if (strncmp(request, "DESCRIBE", 8) == 0) {
    SendDESCRIBE(session, cseq);
  } else if (strncmp(request, "SETUP", 5) == 0) {
    // Transport 헤더에서 클라이언트 RTP 포트 추출
    uint16_t client_rtp_port = 0;
    const char *transport = strstr(request, "Transport:");
    if (transport) {
      const char *port_str = strstr(transport, "client_port=");
      if (port_str) {
        client_rtp_port = atoi(port_str + 12);
      }
    }
    SendSETUP(session, cseq, client_rtp_port);
  } else if (strncmp(request, "PLAY", 4) == 0) {
    SendPLAY(session, cseq);
  } else if (strncmp(request, "TEARDOWN", 8) == 0) {
    SendTEARDOWN(session, cseq);
  }
}

void RTSPServer::SendOPTIONS(RTSPSession *session, int cseq) {
  char response[256];
  snprintf(response, sizeof(response),
           "RTSP/1.0 200 OK\r\n"
           "CSeq: %d\r\n"
           "Public: OPTIONS, DESCRIBE, SETUP, PLAY, TEARDOWN\r\n\r\n",
           cseq);
  send(session->socket, response, strlen(response), 0);
}

void RTSPServer::SendDESCRIBE(RTSPSession *session, int cseq) {
  // SDP (Session Description Protocol) 생성
  char sdp[512];
  snprintf(sdp, sizeof(sdp),
           "v=0\r\n"
           "o=- 0 0 IN IP4 0.0.0.0\r\n"
           "s=CoreS3 Camera\r\n"
           "t=0 0\r\n"
           "m=video 0 RTP/AVP %d\r\n"
           "a=rtpmap:%d JPEG/90000\r\n"
           "a=control:stream\r\n",
           RTP_PAYLOAD_JPEG, RTP_PAYLOAD_JPEG);

  char response[1024];
  snprintf(response, sizeof(response),
           "RTSP/1.0 200 OK\r\n"
           "CSeq: %d\r\n"
           "Content-Type: application/sdp\r\n"
           "Content-Length: %d\r\n\r\n%s",
           cseq, (int)strlen(sdp), sdp);
  send(session->socket, response, strlen(response), 0);
}

void RTSPServer::SendSETUP(RTSPSession *session, int cseq,
                           uint16_t client_rtp_port) {
  session->client_rtp_port = client_rtp_port;

  // RTP 소켓 생성
  if (session->rtp_socket < 0) {
    session->rtp_socket = socket(AF_INET, SOCK_DGRAM, 0);
  }

  // 서버 RTP 포트
  uint16_t server_rtp_port = RTP_PORT_BASE + (session - sessions_) * 2;

  char response[512];
  snprintf(
      response, sizeof(response),
      "RTSP/1.0 200 OK\r\n"
      "CSeq: %d\r\n"
      "Session: %s\r\n"
      "Transport: RTP/AVP;unicast;client_port=%d-%d;server_port=%d-%d\r\n\r\n",
      cseq, session->session_id, client_rtp_port, client_rtp_port + 1,
      server_rtp_port, server_rtp_port + 1);
  send(session->socket, response, strlen(response), 0);

  ESP_LOGI(TAG, "SETUP: client RTP port=%d", client_rtp_port);
}

void RTSPServer::SendPLAY(RTSPSession *session, int cseq) {
  session->playing = true;

  char response[256];
  snprintf(response, sizeof(response),
           "RTSP/1.0 200 OK\r\n"
           "CSeq: %d\r\n"
           "Session: %s\r\n"
           "Range: npt=0.000-\r\n\r\n",
           cseq, session->session_id);
  send(session->socket, response, strlen(response), 0);

  ESP_LOGI(TAG, "PLAY started for session %s", session->session_id);
}

void RTSPServer::SendTEARDOWN(RTSPSession *session, int cseq) {
  session->playing = false;

  char response[128];
  snprintf(response, sizeof(response),
           "RTSP/1.0 200 OK\r\n"
           "CSeq: %d\r\n\r\n",
           cseq);
  send(session->socket, response, strlen(response), 0);
}

void RTSPServer::StreamTask(void *arg) {
  RTSPServer *server = static_cast<RTSPServer *>(arg);
  server->StreamTaskImpl();
  vTaskDelete(nullptr);
}

void RTSPServer::StreamTaskImpl() {
  const int frame_interval_ms = 100; // 10 FPS

  while (running_) {
    bool has_active_client = false;

    // 활성 클라이언트 확인
    for (int i = 0; i < RTSP_MAX_CLIENTS; i++) {
      if (sessions_[i].playing) {
        has_active_client = true;
        break;
      }
    }

    if (has_active_client && frame_callback_) {
      uint8_t *jpeg_data = nullptr;
      size_t jpeg_len = 0;

      if (frame_callback_(&jpeg_data, &jpeg_len)) {
        // 모든 활성 클라이언트에게 프레임 전송
        for (int i = 0; i < RTSP_MAX_CLIENTS; i++) {
          if (sessions_[i].playing) {
            SendRTPFrame(&sessions_[i], jpeg_data, jpeg_len);
          }
        }
      }
    }

    vTaskDelay(pdMS_TO_TICKS(frame_interval_ms));
  }
}

bool RTSPServer::SendRTPFrame(RTSPSession *session, const uint8_t *jpeg_data,
                              size_t jpeg_len) {
  if (session->rtp_socket < 0 || session->client_rtp_port == 0) {
    return false;
  }

  // 대상 주소 설정
  struct sockaddr_in dest_addr = session->client_addr;
  dest_addr.sin_port = htons(session->client_rtp_port);

  // 타임스탬프 업데이트 (90kHz 클록)
  session->timestamp += 90000 / 10; // 10 FPS

  // JPEG 프레임을 RTP 패킷으로 분할 전송 (RFC 2435)
  size_t offset = 0;

  while (offset < jpeg_len) {
    uint8_t packet[RTP_MTU + RTP_HEADER_SIZE + JPEG_HEADER_SIZE];
    size_t payload_size = jpeg_len - offset;
    bool last_packet = true;

    if (payload_size > RTP_MTU - JPEG_HEADER_SIZE) {
      payload_size = RTP_MTU - JPEG_HEADER_SIZE;
      last_packet = false;
    }

    // RTP 헤더
    packet[0] = 0x80; // V=2, P=0, X=0, CC=0
    packet[1] = RTP_PAYLOAD_JPEG | (last_packet ? 0x80 : 0x00); // M bit
    packet[2] = (session->sequence >> 8) & 0xFF;
    packet[3] = session->sequence & 0xFF;
    packet[4] = (session->timestamp >> 24) & 0xFF;
    packet[5] = (session->timestamp >> 16) & 0xFF;
    packet[6] = (session->timestamp >> 8) & 0xFF;
    packet[7] = session->timestamp & 0xFF;
    packet[8] = (session->ssrc >> 24) & 0xFF;
    packet[9] = (session->ssrc >> 16) & 0xFF;
    packet[10] = (session->ssrc >> 8) & 0xFF;
    packet[11] = session->ssrc & 0xFF;

    // JPEG 헤더 (RFC 2435)
    uint32_t fragment_offset = offset;
    packet[12] = 0; // Type-specific
    packet[13] = (fragment_offset >> 16) & 0xFF;
    packet[14] = (fragment_offset >> 8) & 0xFF;
    packet[15] = fragment_offset & 0xFF;
    packet[16] = 0;  // Type (0 = baseline)
    packet[17] = 80; // Q factor
    packet[18] = 40; // Width / 8 (320/8)
    packet[19] = 30; // Height / 8 (240/8)

    // JPEG 데이터 복사
    memcpy(&packet[RTP_HEADER_SIZE + JPEG_HEADER_SIZE], jpeg_data + offset,
           payload_size);

    // 전송
    int sent = sendto(session->rtp_socket, packet,
                      RTP_HEADER_SIZE + JPEG_HEADER_SIZE + payload_size, 0,
                      (struct sockaddr *)&dest_addr, sizeof(dest_addr));

    if (sent < 0) {
      ESP_LOGW(TAG, "RTP send failed");
      return false;
    }

    session->sequence++;
    offset += payload_size;
  }

  return true;
}

int RTSPServer::FindFreeSession() {
  xSemaphoreTake(clients_mutex_, portMAX_DELAY);
  for (int i = 0; i < RTSP_MAX_CLIENTS; i++) {
    if (sessions_[i].socket < 0) {
      xSemaphoreGive(clients_mutex_);
      return i;
    }
  }
  xSemaphoreGive(clients_mutex_);
  return -1;
}

void RTSPServer::CloseSession(RTSPSession *session) {
  if (session->socket >= 0) {
    close(session->socket);
    session->socket = -1;
  }
  if (session->rtp_socket >= 0) {
    close(session->rtp_socket);
    session->rtp_socket = -1;
  }
  session->playing = false;
}

void RTSPServer::GenerateSessionId(char *buf, size_t len) {
  uint32_t r = esp_random();
  snprintf(buf, len, "%08lX", (unsigned long)r);
}
