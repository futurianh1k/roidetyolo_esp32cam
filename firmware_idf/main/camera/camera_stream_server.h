/**
 * Camera Stream Server
 *
 * HTTP MJPEG, RTSP, WebSocket 스트리밍 서버
 *
 * 참고자료:
 * - ESP HTTP Server:
 * https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/protocols/esp_http_server.html
 * - MJPEG Streaming: https://en.wikipedia.org/wiki/Motion_JPEG
 * - ESP32-CAM Example:
 * https://github.com/espressif/esp32-camera/tree/master/examples
 */

#ifndef CAMERA_STREAM_SERVER_H
#define CAMERA_STREAM_SERVER_H

#include "camera_service.h"
#include <atomic>
#include <esp_http_server.h>
#include <freertos/FreeRTOS.h>
#include <freertos/semphr.h>
#include <freertos/task.h>
#include <functional>
#include <string>
#include <vector>


// 스트리밍 설정
#define STREAM_HTTP_PORT 81
#define STREAM_RTSP_PORT 554
#define STREAM_BOUNDARY "frame"
#define STREAM_CONTENT_TYPE                                                    \
  "multipart/x-mixed-replace;boundary=" STREAM_BOUNDARY
#define STREAM_PART_BOUNDARY "\r\n--" STREAM_BOUNDARY "\r\n"
#define STREAM_PART_END "\r\n--" STREAM_BOUNDARY "--\r\n"

// JPEG 품질 (0-100)
#define JPEG_QUALITY 80

// 최대 동시 클라이언트 수
#define MAX_STREAM_CLIENTS 4

// WebSocket 프레임 콜백
using WebSocketFrameCallback = std::function<void(const uint8_t *, size_t)>;

/**
 * CameraStreamServer - 카메라 스트리밍 서버
 *
 * HTTP MJPEG, WebSocket 스트리밍 제공
 */
class CameraStreamServer {
public:
  CameraStreamServer(CameraService *camera_service);
  ~CameraStreamServer();

  // 서버 시작/중지
  bool Start();
  void Stop();

  // HTTP 서버 상태
  bool IsHTTPRunning() const { return http_server_ != nullptr; }

  // WebSocket 스트리밍 설정
  void SetWebSocketCallback(WebSocketFrameCallback callback);
  void EnableWebSocketStream(bool enable);

  // 현재 연결된 클라이언트 수
  int GetClientCount() const { return active_clients_.load(); }

  // 스트리밍 통계
  uint32_t GetFramesSent() const { return frames_sent_; }
  uint32_t GetBytesSent() const { return bytes_sent_; }

private:
  CameraService *camera_service_;
  httpd_handle_t http_server_ = nullptr;

  // 스트리밍 태스크
  TaskHandle_t stream_task_handle_ = nullptr;
  bool stream_task_running_ = false;

  // 클라이언트 관리
  std::atomic<int> active_clients_{0};
  SemaphoreHandle_t client_mutex_ = nullptr;

  // WebSocket
  WebSocketFrameCallback ws_callback_ = nullptr;
  bool ws_stream_enabled_ = false;

  // 통계
  uint32_t frames_sent_ = 0;
  uint32_t bytes_sent_ = 0;

  // JPEG 인코딩 버퍼
  uint8_t *jpeg_buffer_ = nullptr;
  size_t jpeg_buffer_size_ = 0;

  // HTTP 핸들러 (static)
  static esp_err_t StreamHandler(httpd_req_t *req);
  static esp_err_t CaptureHandler(httpd_req_t *req);
  static esp_err_t IndexHandler(httpd_req_t *req);
  static esp_err_t StatusHandler(httpd_req_t *req);

  // 내부 함수
  bool StartHTTPServer();
  void StopHTTPServer();
  bool CaptureAndEncodeJPEG(uint8_t **out_buf, size_t *out_len);
  void FreeJPEGBuffer(uint8_t *buf);
};

#endif // CAMERA_STREAM_SERVER_H
