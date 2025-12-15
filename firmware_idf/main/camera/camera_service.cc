#include "camera_service.h"
#include "../config.h"
#include "../pins.h"
#include <cstring>
#include <esp_camera.h>
#include <esp_http_client.h>
#include <esp_log.h>
#include <img_converters.h>

#define TAG "CameraService"

/**
 * M5Stack CoreS3 Camera Configuration
 * Reference:
 * https://github.com/felmue/MyM5StackExamples/blob/main/M5CoreS3/CamWebServer/
 *
 * Camera: GC0308 (0.3MP)
 * - Does NOT support JPEG! Use RGB565 or GRAYSCALE
 * - XCLK is GPIO 2!
 * - Uses existing I2C port 1 (initialized in application.cc)
 */
static camera_config_t camera_config = {
    .pin_pwdn = GPIO_NUM_NC,
    .pin_reset = GPIO_NUM_NC,
    .pin_xclk = GPIO_NUM_2,      // XCLK is connected to GPIO 2!
    .pin_sscb_sda = GPIO_NUM_NC, // Use existing I2C port
    .pin_sccb_scl = GPIO_NUM_NC, // Use existing I2C port

    // Data pins - from working example
    .pin_d7 = GPIO_NUM_47,
    .pin_d6 = GPIO_NUM_48,
    .pin_d5 = GPIO_NUM_16,
    .pin_d4 = GPIO_NUM_15,
    .pin_d3 = GPIO_NUM_42,
    .pin_d2 = GPIO_NUM_41,
    .pin_d1 = GPIO_NUM_40,
    .pin_d0 = GPIO_NUM_39,
    .pin_vsync = GPIO_NUM_46,
    .pin_href = GPIO_NUM_38,
    .pin_pclk = GPIO_NUM_45,

    // GC0308 camera settings
    .xclk_freq_hz = 20000000, // 20MHz (from working example)
    .ledc_timer = LEDC_TIMER_0,
    .ledc_channel = LEDC_CHANNEL_0,

    // GC0308 does NOT support JPEG! Use RGB565
    .pixel_format = PIXFORMAT_RGB565,
    .frame_size = FRAMESIZE_QVGA, // 320x240 (matching display)
    .jpeg_quality = 12,
    .fb_count = 2,
    .fb_location = CAMERA_FB_IN_PSRAM,
    .grab_mode = CAMERA_GRAB_WHEN_EMPTY,

    // Use existing I2C port 1 (already initialized in application.cc)
    .sccb_i2c_port = 1,
};

CameraService::CameraService() {}

CameraService::~CameraService() {
  Stop();
  if (initialized_) {
    esp_camera_deinit();
  }
}

bool CameraService::Initialize() {
  if (initialized_) {
    return true;
  }

  ESP_LOGI(TAG, "Initializing camera...");

  // 카메라 초기화 (재시도 로직 포함)
  esp_err_t err = ESP_FAIL;
  int retry_count = 0;
  const int max_retries = 3;

  while (err != ESP_OK && retry_count < max_retries) {
    if (retry_count > 0) {
      ESP_LOGW(TAG, "Camera init retry %d/%d", retry_count, max_retries - 1);
      vTaskDelay(pdMS_TO_TICKS(500));
    }

    err = esp_camera_init(&camera_config);
    retry_count++;
  }

  if (err != ESP_OK) {
    ESP_LOGE(TAG, "Camera init failed: %s", esp_err_to_name(err));
    return false;
  }

  // 센서 설정
  sensor_t *s = esp_camera_sensor_get();
  if (s) {
    s->set_brightness(s, CAMERA_BRIGHTNESS);
    s->set_contrast(s, CAMERA_CONTRAST);
    s->set_saturation(s, CAMERA_SATURATION);
    s->set_whitebal(s, 1);
    s->set_awb_gain(s, 1);
    s->set_exposure_ctrl(s, 1);
    s->set_aec2(s, 1);
    s->set_agc_gain(s, 1);
  }

  initialized_ = true;
  ESP_LOGI(TAG, "Camera initialized");
  return true;
}

void CameraService::Start() {
  if (service_running_) {
    return;
  }

  service_running_ = true;

  // 카메라 태스크 생성
  xTaskCreatePinnedToCore(CameraTask, "camera_task", 8192, this,
                          3, // 우선순위
                          &camera_task_handle_,
                          1 // Core 1
  );

  ESP_LOGI(TAG, "Camera service started");
}

void CameraService::Stop() {
  if (!service_running_) {
    return;
  }

  service_running_ = false;
  StopStream();

  if (camera_task_handle_) {
    vTaskDelete(camera_task_handle_);
    camera_task_handle_ = nullptr;
  }

  ESP_LOGI(TAG, "Camera service stopped");
}

void CameraService::StartStream(const std::string &sink_url,
                                const std::string &stream_mode,
                                int frame_interval_ms) {
  sink_url_ = sink_url;
  stream_mode_ = stream_mode;
  frame_interval_ms_ = frame_interval_ms;
  streaming_active_ = true;

  // 서비스가 실행 중이 아니면 시작
  if (!service_running_) {
    Start();
  }

  ESP_LOGI(TAG, "Camera stream started: %s, mode: %s, interval: %dms",
           sink_url.c_str(), stream_mode.c_str(), frame_interval_ms);
}

void CameraService::StopStream() {
  streaming_active_ = false;
  ESP_LOGI(TAG, "Camera stream stopped");
}

bool CameraService::CaptureFrame(std::vector<uint8_t> &jpeg_data) {
  if (!initialized_) {
    return false;
  }

  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    ESP_LOGE(TAG, "Failed to capture frame");
    return false;
  }

  // GC0308 카메라는 RGB565로 캡처하므로 JPEG로 변환 필요
  // Reference: esp32-camera의 img_converters.h
  if (fb->format == PIXFORMAT_RGB565) {
    uint8_t *jpeg_out = nullptr;
    size_t jpeg_len = 0;

    // RGB565 → JPEG 변환
    bool converted = frame2jpg(fb, 80, &jpeg_out, &jpeg_len); // Quality 80
    esp_camera_fb_return(fb);

    if (!converted || jpeg_out == nullptr) {
      ESP_LOGE(TAG, "JPEG conversion failed");
      return false;
    }

    jpeg_data.assign(jpeg_out, jpeg_out + jpeg_len);
    free(jpeg_out); // frame2jpg가 할당한 메모리 해제
  } else {
    // 이미 JPEG 형식인 경우 (다른 카메라)
    jpeg_data.assign(fb->buf, fb->buf + fb->len);
    esp_camera_fb_return(fb);
  }

  return true;
}

void CameraService::CameraTask(void *arg) {
  CameraService *service = static_cast<CameraService *>(arg);
  service->CameraTaskImpl();
}

void CameraService::CameraTaskImpl() {
  TickType_t last_frame_time = 0;

  while (service_running_) {
    if (streaming_active_) {
      TickType_t now = xTaskGetTickCount();
      if (now - last_frame_time >= pdMS_TO_TICKS(frame_interval_ms_)) {
        std::vector<uint8_t> jpeg_data;
        if (CaptureFrame(jpeg_data)) {
          // mjpeg_stills, http, mjpeg 모두 HTTP POST로 전송
          if (stream_mode_ == "mjpeg_stills" || stream_mode_ == "http" ||
              stream_mode_ == "mjpeg") {
            SendFrameHTTP(jpeg_data);
          }
          // TODO: WebSocket 스트리밍 추가 (realtime_websocket)
          // TODO: RTSP 스트리밍 추가 (realtime_rtsp)
        }
        last_frame_time = now;
      }
    }

    vTaskDelay(pdMS_TO_TICKS(100));
  }

  vTaskDelete(nullptr);
}

bool CameraService::SendFrameHTTP(const std::vector<uint8_t> &jpeg_data) {
  if (sink_url_.empty()) {
    return false;
  }

  // Multipart form-data 형식으로 전송 (FastAPI UploadFile 호환)
  // Reference: RFC 2046 (multipart/form-data)
  static const char *boundary = "----ESP32CameraBoundary";

  // Multipart 헤더 구성
  std::string header = std::string("------") + boundary + "\r\n";
  header += "Content-Disposition: form-data; name=\"file\"; "
            "filename=\"frame.jpg\"\r\n";
  header += "Content-Type: image/jpeg\r\n\r\n";

  // Multipart 끝 경계
  std::string footer = "\r\n------";
  footer += boundary;
  footer += "--\r\n";

  // 전체 바디 구성
  std::vector<uint8_t> body;
  body.reserve(header.size() + jpeg_data.size() + footer.size());

  // 헤더 추가
  body.insert(body.end(), header.begin(), header.end());
  // JPEG 데이터 추가
  body.insert(body.end(), jpeg_data.begin(), jpeg_data.end());
  // 푸터 추가
  body.insert(body.end(), footer.begin(), footer.end());

  esp_http_client_config_t config = {};
  config.url = sink_url_.c_str();
  config.method = HTTP_METHOD_POST;
  config.timeout_ms = 5000;

  esp_http_client_handle_t client = esp_http_client_init(&config);
  if (!client) {
    ESP_LOGE(TAG, "Failed to init HTTP client");
    return false;
  }

  // Multipart Content-Type 설정
  std::string content_type =
      std::string("multipart/form-data; boundary=----") + boundary;

  esp_http_client_set_method(client, HTTP_METHOD_POST);
  esp_http_client_set_header(client, "Content-Type", content_type.c_str());
  esp_http_client_set_post_field(client, (const char *)body.data(),
                                 body.size());

  esp_err_t err = esp_http_client_perform(client);
  int status_code = esp_http_client_get_status_code(client);

  esp_http_client_cleanup(client);

  if (err != ESP_OK || status_code != 200) {
    ESP_LOGE(TAG, "HTTP POST failed: %s, status: %d", esp_err_to_name(err),
             status_code);
    return false;
  }

  ESP_LOGI(TAG, "Frame sent successfully (%d bytes)", jpeg_data.size());
  return true;
}
