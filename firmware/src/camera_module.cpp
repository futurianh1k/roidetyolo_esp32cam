/**
 * 카메라 모듈
 *
 * OV2640 카메라 제어 및 RTSP 스트리밍
 * 참고: ESP32-Camera 라이브러리
 */

#include "camera_module.h"
#include "config.h"
#include "esp_camera.h"
#include "pins.h"
#include "websocket_module.h" // WebSocket 스트림용
#include <Arduino.h>
#include <HTTPClient.h>
#include <WiFiClient.h>


// 카메라 설정
static camera_config_t camera_config = {.pin_pwdn = PWDN_GPIO_NUM,
                                        .pin_reset = RESET_GPIO_NUM,
                                        .pin_xclk = XCLK_GPIO_NUM,
                                        .pin_sscb_sda = SIOD_GPIO_NUM,
                                        .pin_sscb_scl = SIOC_GPIO_NUM,

                                        .pin_d7 = Y9_GPIO_NUM,
                                        .pin_d6 = Y8_GPIO_NUM,
                                        .pin_d5 = Y7_GPIO_NUM,
                                        .pin_d4 = Y6_GPIO_NUM,
                                        .pin_d3 = Y5_GPIO_NUM,
                                        .pin_d2 = Y4_GPIO_NUM,
                                        .pin_d1 = Y3_GPIO_NUM,
                                        .pin_d0 = Y2_GPIO_NUM,
                                        .pin_vsync = VSYNC_GPIO_NUM,
                                        .pin_href = HREF_GPIO_NUM,
                                        .pin_pclk = PCLK_GPIO_NUM,

                                        .xclk_freq_hz = 20000000,
                                        .ledc_timer = LEDC_TIMER_0,
                                        .ledc_channel = LEDC_CHANNEL_0,

                                        .pixel_format = PIXFORMAT_JPEG,
                                        .frame_size = CAMERA_FRAMESIZE,
                                        .jpeg_quality = CAMERA_QUALITY,
                                        .fb_count = 2,
                                        .fb_location = CAMERA_FB_IN_PSRAM,
                                        .grab_mode = CAMERA_GRAB_LATEST};

static bool cameraInitialized = false;
static bool cameraStreamActive = false;
static bool cameraPaused = false;

// 영상 sink 설정
static String sinkUrl = "";
static String streamMode = "";
static int frameInterval = 1000; // ms
static bool sinkActive = false;
static unsigned long lastFrameTime = 0;
static HTTPClient httpClient;     // HTTP 전송용 (MJPEG 스틸컷)
static WiFiClient wsStreamClient; // WebSocket 스트림용
static bool wsStreamConnected = false;

/**
 * 카메라 초기화
 */
bool cameraInit() {
  if (cameraInitialized) {
    DEBUG_PRINTLN("Camera already initialized");
    return true;
  }

  DEBUG_PRINTLN("Initializing camera...");

  // 카메라 초기화
  esp_err_t err = esp_camera_init(&camera_config);
  if (err != ESP_OK) {
    DEBUG_PRINTF("Camera init failed with error 0x%x\n", err);
    return false;
  }

  // 카메라 센서 설정
  sensor_t *s = esp_camera_sensor_get();
  if (s == NULL) {
    DEBUG_PRINTLN("Failed to get camera sensor");
    return false;
  }

  // 이미지 설정
  s->set_brightness(s, CAMERA_BRIGHTNESS);
  s->set_contrast(s, CAMERA_CONTRAST);
  s->set_saturation(s, CAMERA_SATURATION);

  // 자동 화이트 밸런스
  s->set_whitebal(s, 1);
  s->set_awb_gain(s, 1);

  // 자동 노출
  s->set_exposure_ctrl(s, 1);
  s->set_aec2(s, 1);

  // 자동 게인
  s->set_gain_ctrl(s, 1);
  s->set_agc_gain(s, 0);

  // 렌즈 보정
  s->set_lenc(s, 1);

  cameraInitialized = true;
  DEBUG_PRINTLN("Camera initialized successfully");

  return true;
}

/**
 * 카메라 시작
 */
bool cameraStart() {
  if (!cameraInitialized) {
    DEBUG_PRINTLN("Camera not initialized");
    return false;
  }

  cameraStreamActive = true;
  cameraPaused = false;
  DEBUG_PRINTLN("Camera streaming started");

  // TODO: RTSP 서버 시작
  // rtspServer.start();

  return true;
}

/**
 * 카메라 일시정지
 */
void cameraPause() {
  cameraPaused = true;
  DEBUG_PRINTLN("Camera streaming paused");
}

/**
 * 카메라 정지
 */
void cameraStop() {
  cameraStreamActive = false;
  cameraPaused = false;

  // 영상 sink 정리
  if (::sinkActive) {
    cameraClearSink();
  }

  DEBUG_PRINTLN("Camera streaming stopped");

  // TODO: RTSP 서버 정지
  // rtspServer.stop();
}

/**
 * MJPEG 스틸컷 전송 (HTTP POST)
 */
static void sendMjpegStill(camera_fb_t *fb) {
  if (::sinkUrl.length() == 0) {
    return;
  }

  DEBUG_PRINTF("📤 MJPEG 스틸컷 전송: %d bytes → %s\n", fb->len,
               ::sinkUrl.c_str());

  httpClient.begin(::sinkUrl);
  httpClient.addHeader("Content-Type", "image/jpeg");
  httpClient.addHeader("Content-Length", String(fb->len));

  int httpCode = httpClient.POST(fb->buf, fb->len);

  if (httpCode > 0) {
    if (httpCode == HTTP_CODE_OK || httpCode == HTTP_CODE_CREATED) {
      DEBUG_PRINTLN("✅ MJPEG 스틸컷 전송 성공");
    } else {
      DEBUG_PRINTF("⚠️ MJPEG 스틸컷 전송 응답: %d\n", httpCode);
    }
  } else {
    DEBUG_PRINTF("❌ MJPEG 스틸컷 전송 실패: %s\n",
                 httpClient.errorToString(httpCode).c_str());
  }

  httpClient.end();
}

/**
 * WebSocket 실시간 스트림 전송
 */
static void sendWebSocketStream(camera_fb_t *fb) {
  if (::sinkUrl.length() == 0) {
    return;
  }

  // WebSocket 연결 확인 및 연결
  if (!::wsStreamConnected) {
    // WebSocket URL 파싱 (ws:// 또는 wss://)
    String wsUrl = ::sinkUrl;
    if (!wsUrl.startsWith("ws://") && !wsUrl.startsWith("wss://")) {
      DEBUG_PRINTLN("❌ WebSocket URL 형식 오류 (ws:// 또는 wss:// 필요)");
      return;
    }

    // TODO: WebSocket 연결 구현
    // 현재는 websocket_module을 ASR 전용으로 사용 중
    // 별도의 WebSocket 클라이언트 필요 또는 모듈 확장
    DEBUG_PRINTLN("⚠️ WebSocket 스트림은 아직 구현되지 않았습니다");
    return;
  }

  // MJPEG 프레임 전송
  // TODO: WebSocket으로 바이너리 프레임 전송
  DEBUG_PRINTF("📤 WebSocket 스트림: %d bytes\n", fb->len);
}

/**
 * 카메라 루프
 */
void cameraLoop() {
  if (!cameraStreamActive || cameraPaused) {
    return;
  }

  // sink가 활성화되어 있지 않으면 기본 동작 (프레임만 캡처)
  if (!::sinkActive || ::sinkUrl.length() == 0) {
    camera_fb_t *fb = esp_camera_fb_get();
    if (fb) {
      esp_camera_fb_return(fb);
    }
    delay(33); // ~30 FPS
    return;
  }

  // sink 전송 모드에 따라 처리
  unsigned long currentTime = millis();

  if (::streamMode == "mjpeg_stills") {
    // MJPEG 스틸컷: 주기적으로 전송
    if (currentTime - ::lastFrameTime >= ::frameInterval) {
      camera_fb_t *fb = esp_camera_fb_get();
      if (fb) {
        sendMjpegStill(fb);
        esp_camera_fb_return(fb);
        ::lastFrameTime = currentTime;
      }
    }
    delay(10); // CPU 부하 감소

  } else if (::streamMode == "realtime_websocket") {
    // WebSocket 실시간 스트림: 최대 FPS로 전송
    camera_fb_t *fb = esp_camera_fb_get();
    if (fb) {
      sendWebSocketStream(fb);
      esp_camera_fb_return(fb);
    }
    delay(33); // ~30 FPS

  } else if (::streamMode == "realtime_rtsp") {
    // RTSP 실시간 스트림
    camera_fb_t *fb = esp_camera_fb_get();
    if (fb) {
      // TODO: RTSP 서버로 프레임 전송
      // rtspServer.sendFrame(fb->buf, fb->len);
      DEBUG_PRINTLN("⚠️ RTSP 스트림은 아직 구현되지 않았습니다");
      esp_camera_fb_return(fb);
    }
    delay(33); // ~30 FPS

  } else {
    // 알 수 없는 모드
    camera_fb_t *fb = esp_camera_fb_get();
    if (fb) {
      esp_camera_fb_return(fb);
    }
    delay(33);
  }
}

/**
 * 카메라 활성 상태 확인
 */
bool isCameraActive() { return cameraStreamActive && !cameraPaused; }

/**
 * 영상 sink 설정
 *
 * @param sinkUrl 영상 sink 주소 (URL)
 * @param streamMode 전송 방식 (mjpeg_stills, realtime_websocket, realtime_rtsp)
 * @param frameInterval 프레임 간격 (ms, mjpeg_stills일 경우)
 */
void cameraSetSink(const char *sinkUrl, const char *streamMode,
                   int frameInterval) {
  if (!sinkUrl || strlen(sinkUrl) == 0) {
    DEBUG_PRINTLN("⚠️ Sink URL이 비어있습니다");
    return;
  }

  ::sinkUrl = String(sinkUrl);
  ::streamMode = streamMode ? String(streamMode) : "";
  ::frameInterval = frameInterval > 0 ? frameInterval : 1000;
  ::sinkActive = true;
  ::lastFrameTime = 0;

  DEBUG_PRINTLN("📹 영상 sink 설정:");
  DEBUG_PRINTF("   URL: %s\n", ::sinkUrl.c_str());
  DEBUG_PRINTF("   모드: %s\n", ::streamMode.c_str());
  if (::streamMode == "mjpeg_stills") {
    DEBUG_PRINTF("   주기: %d ms\n", ::frameInterval);
  }

  // WebSocket 스트림 모드일 경우 연결 초기화
  if (::streamMode == "realtime_websocket") {
    ::wsStreamConnected = false;
    // TODO: WebSocket 연결 초기화
  }
}

/**
 * 영상 sink 설정 초기화
 */
void cameraClearSink() {
  ::sinkUrl = "";
  ::streamMode = "";
  ::sinkActive = false;
  ::wsStreamConnected = false;

  // HTTP 클라이언트 종료
  httpClient.end();

  DEBUG_PRINTLN("📹 영상 sink 설정 초기화");
}

/**
 * 영상 sink 활성 상태 확인
 */
bool isCameraSinkActive() { return ::sinkActive && ::sinkUrl.length() > 0; }
