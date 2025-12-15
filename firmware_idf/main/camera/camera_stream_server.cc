/**
 * Camera Stream Server Implementation
 *
 * HTTP MJPEG 스트리밍 서버 구현
 *
 * 참고자료:
 * - ESP32-CAM MJPEG Streaming:
 * https://github.com/espressif/esp32-camera/blob/master/examples/camera_server/main/camera_server_main.c
 * - ESP HTTP Server:
 * https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/protocols/esp_http_server.html
 */

#include "camera_stream_server.h"
#include <cstring>
#include <esp_camera.h>
#include <esp_log.h>
#include <esp_timer.h>
#include <img_converters.h>

#define TAG "CameraStreamServer"

// JPEG 버퍼 크기 (QVGA 이미지 기준)
#define JPEG_BUFFER_SIZE (320 * 240 * 2) // RGB565 크기

// HTTP 응답 헤더
static const char *STREAM_CONTENT_TYPE_HDR =
    "multipart/x-mixed-replace;boundary=" STREAM_BOUNDARY;
static const char *STREAM_BOUNDARY_HDR = "\r\n--" STREAM_BOUNDARY "\r\n";
static const char *STREAM_PART_HDR =
    "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

// 서버 인스턴스 (핸들러에서 접근용)
static CameraStreamServer *g_server_instance = nullptr;

CameraStreamServer::CameraStreamServer(CameraService *camera_service)
    : camera_service_(camera_service) {
  client_mutex_ = xSemaphoreCreateMutex();
  g_server_instance = this;
}

CameraStreamServer::~CameraStreamServer() {
  Stop();
  if (client_mutex_) {
    vSemaphoreDelete(client_mutex_);
  }
  if (jpeg_buffer_) {
    free(jpeg_buffer_);
  }
  g_server_instance = nullptr;
}

bool CameraStreamServer::Start() {
  ESP_LOGI(TAG, "Starting Camera Stream Server...");

  // JPEG 버퍼 할당
  if (!jpeg_buffer_) {
    jpeg_buffer_ = (uint8_t *)heap_caps_malloc(
        JPEG_BUFFER_SIZE, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
    if (!jpeg_buffer_) {
      jpeg_buffer_ = (uint8_t *)malloc(JPEG_BUFFER_SIZE);
    }
    if (!jpeg_buffer_) {
      ESP_LOGE(TAG, "Failed to allocate JPEG buffer");
      return false;
    }
    jpeg_buffer_size_ = JPEG_BUFFER_SIZE;
  }

  // HTTP 서버 시작
  if (!StartHTTPServer()) {
    ESP_LOGE(TAG, "Failed to start HTTP server");
    return false;
  }

  ESP_LOGI(TAG, "Camera Stream Server started on port %d", STREAM_HTTP_PORT);
  return true;
}

void CameraStreamServer::Stop() {
  ESP_LOGI(TAG, "Stopping Camera Stream Server...");

  StopHTTPServer();

  ESP_LOGI(TAG, "Camera Stream Server stopped");
}

bool CameraStreamServer::StartHTTPServer() {
  if (http_server_) {
    return true; // 이미 실행 중
  }

  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  config.server_port = STREAM_HTTP_PORT;
  config.ctrl_port = STREAM_HTTP_PORT + 1;
  config.max_open_sockets = MAX_STREAM_CLIENTS + 2;
  config.max_uri_handlers = 8;
  config.stack_size = 8192;
  config.core_id = 1; // Core 1에서 실행

  esp_err_t err = httpd_start(&http_server_, &config);
  if (err != ESP_OK) {
    ESP_LOGE(TAG, "Failed to start HTTP server: %s", esp_err_to_name(err));
    return false;
  }

  // 스트림 핸들러 등록
  httpd_uri_t stream_uri = {
      .uri = "/stream",
      .method = HTTP_GET,
      .handler = StreamHandler,
      .user_ctx = this,
  };
  httpd_register_uri_handler(http_server_, &stream_uri);

  // 캡처 핸들러 등록
  httpd_uri_t capture_uri = {
      .uri = "/capture",
      .method = HTTP_GET,
      .handler = CaptureHandler,
      .user_ctx = this,
  };
  httpd_register_uri_handler(http_server_, &capture_uri);

  // 인덱스 핸들러 등록
  httpd_uri_t index_uri = {
      .uri = "/",
      .method = HTTP_GET,
      .handler = IndexHandler,
      .user_ctx = this,
  };
  httpd_register_uri_handler(http_server_, &index_uri);

  // 상태 핸들러 등록
  httpd_uri_t status_uri = {
      .uri = "/status",
      .method = HTTP_GET,
      .handler = StatusHandler,
      .user_ctx = this,
  };
  httpd_register_uri_handler(http_server_, &status_uri);

  ESP_LOGI(TAG, "HTTP server started on port %d", STREAM_HTTP_PORT);
  return true;
}

void CameraStreamServer::StopHTTPServer() {
  if (http_server_) {
    httpd_stop(http_server_);
    http_server_ = nullptr;
    ESP_LOGI(TAG, "HTTP server stopped");
  }
}

bool CameraStreamServer::CaptureAndEncodeJPEG(uint8_t **out_buf,
                                              size_t *out_len) {
  if (!camera_service_) {
    return false;
  }

  // 프레임 캡처
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    ESP_LOGE(TAG, "Failed to capture frame");
    return false;
  }

  // 카메라가 JPEG를 지원하는 경우 (OV2640 등)
  if (fb->format == PIXFORMAT_JPEG) {
    // JPEG 데이터를 내부 버퍼에 복사
    if (fb->len <= jpeg_buffer_size_) {
      memcpy(jpeg_buffer_, fb->buf, fb->len);
      *out_buf = jpeg_buffer_;
      *out_len = fb->len;
      esp_camera_fb_return(fb);
      return true;
    }
    ESP_LOGE(TAG, "JPEG buffer too small: need %d, have %d", fb->len,
             jpeg_buffer_size_);
    esp_camera_fb_return(fb);
    return false;
  }

  // GC0308은 RGB565를 출력하므로 JPEG로 인코딩 필요
  // esp32-camera의 frame2jpg 함수 사용
  uint8_t *jpeg_out = nullptr;
  size_t jpeg_out_len = 0;

  bool success = frame2jpg(fb, JPEG_QUALITY, &jpeg_out, &jpeg_out_len);

  if (success && jpeg_out && jpeg_out_len > 0) {
    // 내부 버퍼에 복사 (frame2jpg가 할당한 메모리는 free 필요)
    if (jpeg_out_len <= jpeg_buffer_size_) {
      memcpy(jpeg_buffer_, jpeg_out, jpeg_out_len);
      *out_buf = jpeg_buffer_;
      *out_len = jpeg_out_len;
    } else {
      ESP_LOGE(TAG, "JPEG buffer too small: need %d, have %d", jpeg_out_len,
               jpeg_buffer_size_);
      success = false;
    }
    free(jpeg_out);
  } else {
    ESP_LOGE(TAG, "frame2jpg failed, format=%d, size=%dx%d", fb->format,
             fb->width, fb->height);
    success = false;
  }

  esp_camera_fb_return(fb);
  return success;
}

void CameraStreamServer::FreeJPEGBuffer(uint8_t *buf) {
  // jpeg_buffer_는 재사용되므로 해제하지 않음
  // JPEG 카메라의 경우에만 fb_return 필요
}

void CameraStreamServer::SetWebSocketCallback(WebSocketFrameCallback callback) {
  ws_callback_ = callback;
}

void CameraStreamServer::EnableWebSocketStream(bool enable) {
  ws_stream_enabled_ = enable;
  ESP_LOGI(TAG, "WebSocket stream %s", enable ? "enabled" : "disabled");
}

// ============== HTTP 핸들러 ==============

esp_err_t CameraStreamServer::StreamHandler(httpd_req_t *req) {
  CameraStreamServer *server = static_cast<CameraStreamServer *>(req->user_ctx);

  ESP_LOGI(TAG, "MJPEG stream request from client");

  // CORS 헤더 추가
  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
  httpd_resp_set_hdr(req, "X-Framerate", "10");

  // Content-Type 설정
  httpd_resp_set_type(req, STREAM_CONTENT_TYPE_HDR);
  httpd_resp_set_hdr(req, "Cache-Control",
                     "no-cache, no-store, must-revalidate");

  // 클라이언트 수 증가
  if (server->client_mutex_) {
    xSemaphoreTake(server->client_mutex_, portMAX_DELAY);
    server->active_clients_++;
    xSemaphoreGive(server->client_mutex_);
  }

  ESP_LOGI(TAG, "Stream client connected (total: %d)", server->active_clients_);

  char part_buf[128];
  int64_t last_frame_time = 0;
  const int frame_interval_ms = 100; // 10 FPS

  while (true) {
    // 프레임 레이트 제한
    int64_t now = esp_timer_get_time() / 1000;
    if (now - last_frame_time < frame_interval_ms) {
      vTaskDelay(pdMS_TO_TICKS(10));
      continue;
    }

    uint8_t *jpeg_buf = nullptr;
    size_t jpeg_len = 0;

    if (!server->CaptureAndEncodeJPEG(&jpeg_buf, &jpeg_len)) {
      ESP_LOGW(TAG, "Frame capture failed, retrying...");
      vTaskDelay(pdMS_TO_TICKS(100));
      continue;
    }

    // boundary 전송
    if (httpd_resp_send_chunk(req, STREAM_BOUNDARY_HDR,
                              strlen(STREAM_BOUNDARY_HDR)) != ESP_OK) {
      ESP_LOGW(TAG, "Client disconnected (boundary)");
      break;
    }

    // 헤더 전송
    size_t hdr_len = snprintf(part_buf, sizeof(part_buf), STREAM_PART_HDR,
                              (unsigned int)jpeg_len);
    if (httpd_resp_send_chunk(req, part_buf, hdr_len) != ESP_OK) {
      ESP_LOGW(TAG, "Client disconnected (header)");
      break;
    }

    // JPEG 데이터 전송
    if (httpd_resp_send_chunk(req, (const char *)jpeg_buf, jpeg_len) !=
        ESP_OK) {
      ESP_LOGW(TAG, "Client disconnected (data)");
      break;
    }

    // 통계 업데이트
    server->frames_sent_++;
    server->bytes_sent_ += jpeg_len;
    last_frame_time = now;

    // WebSocket으로도 전송
    if (server->ws_stream_enabled_ && server->ws_callback_) {
      server->ws_callback_(jpeg_buf, jpeg_len);
    }

    // 다른 태스크에게 양보
    vTaskDelay(pdMS_TO_TICKS(1));
  }

  // 클라이언트 수 감소
  if (server->client_mutex_) {
    xSemaphoreTake(server->client_mutex_, portMAX_DELAY);
    server->active_clients_--;
    xSemaphoreGive(server->client_mutex_);
  }

  ESP_LOGI(TAG, "Stream client disconnected (remaining: %d)",
           server->active_clients_);

  return ESP_OK;
}

esp_err_t CameraStreamServer::CaptureHandler(httpd_req_t *req) {
  CameraStreamServer *server = static_cast<CameraStreamServer *>(req->user_ctx);

  ESP_LOGI(TAG, "Capture request");

  uint8_t *jpeg_buf = nullptr;
  size_t jpeg_len = 0;

  if (!server->CaptureAndEncodeJPEG(&jpeg_buf, &jpeg_len)) {
    httpd_resp_send_500(req);
    return ESP_FAIL;
  }

  // CORS 및 헤더 설정
  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
  httpd_resp_set_type(req, "image/jpeg");
  httpd_resp_set_hdr(req, "Content-Disposition",
                     "inline; filename=capture.jpg");

  // JPEG 전송
  esp_err_t err = httpd_resp_send(req, (const char *)jpeg_buf, jpeg_len);

  return err;
}

esp_err_t CameraStreamServer::IndexHandler(httpd_req_t *req) {
  static const char *INDEX_HTML = R"HTML(
<!DOCTYPE html>
<html>
<head>
    <title>CoreS3 Camera</title>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; text-align: center; background: #1a1a2e; color: #eee; margin: 20px; }
        h1 { color: #4cc9f0; }
        img { max-width: 100%; border: 2px solid #4cc9f0; border-radius: 8px; }
        .container { max-width: 800px; margin: 0 auto; }
        .btn { background: #4cc9f0; color: #1a1a2e; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        .btn:hover { background: #7dd3fc; }
        .info { background: #2a2a4e; padding: 10px; border-radius: 5px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>CoreS3 Camera Stream</h1>
        <div class="info">
            <p>MJPEG Stream: <a href="/stream" style="color:#4cc9f0">/stream</a></p>
            <p>Single Capture: <a href="/capture" style="color:#4cc9f0">/capture</a></p>
        </div>
        <img id="stream" src="/stream" alt="Camera Stream">
        <div>
            <button class="btn" onclick="location.reload()">Refresh</button>
            <button class="btn" onclick="window.open('/capture')">Capture</button>
        </div>
    </div>
</body>
</html>
)HTML";

  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
  httpd_resp_set_type(req, "text/html");
  return httpd_resp_send(req, INDEX_HTML, strlen(INDEX_HTML));
}

esp_err_t CameraStreamServer::StatusHandler(httpd_req_t *req) {
  CameraStreamServer *server = static_cast<CameraStreamServer *>(req->user_ctx);

  char json[256];
  snprintf(json, sizeof(json),
           "{\"clients\":%d,\"frames_sent\":%lu,\"bytes_sent\":%lu,"
           "\"http_running\":%s,\"ws_enabled\":%s}",
           server->active_clients_, (unsigned long)server->frames_sent_,
           (unsigned long)server->bytes_sent_,
           server->IsHTTPRunning() ? "true" : "false",
           server->ws_stream_enabled_ ? "true" : "false");

  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
  httpd_resp_set_type(req, "application/json");
  return httpd_resp_send(req, json, strlen(json));
}
