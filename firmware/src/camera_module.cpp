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
#include <WiFi.h>
#include <ArduinoWebsockets.h>
using namespace websockets;

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
                                        .fb_count = 1,                     // PSRAM이 없으면 1로 설정
                                        .fb_location = CAMERA_FB_IN_PSRAM, // PSRAM 사용 시도
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
static HTTPClient httpClient;          // HTTP 전송용 (MJPEG 스틸컷)
static WebsocketsClient wsStreamClient; // WebSocket 스트림용
static bool wsStreamConnected = false;

// RTSP 서버 (향후 구현 예정)
static WiFiServer rtspServer(RTSP_PORT);
static WiFiClient rtspClient;
static bool rtspServerActive = false;

/**
 * 카메라 초기화
 */
bool cameraInit()
{
  if (cameraInitialized)
  {
    DEBUG_PRINTLN("Camera already initialized");
    return true;
  }

  DEBUG_PRINTLN("Initializing camera...");
  DEBUG_PRINTF("  XCLK Pin: %d\n", XCLK_GPIO_NUM);
  DEBUG_PRINTF("  SDA Pin: %d, SCL Pin: %d\n", SIOD_GPIO_NUM, SIOC_GPIO_NUM);
  DEBUG_PRINTF("  Data Pins: D0=%d, D1=%d, D2=%d, D3=%d, D4=%d, D5=%d, D6=%d, D7=%d\n",
               Y2_GPIO_NUM, Y3_GPIO_NUM, Y4_GPIO_NUM, Y5_GPIO_NUM,
               Y6_GPIO_NUM, Y7_GPIO_NUM, Y8_GPIO_NUM, Y9_GPIO_NUM);
  DEBUG_PRINTF("  VSYNC: %d, HREF: %d, PCLK: %d\n", VSYNC_GPIO_NUM, HREF_GPIO_NUM, PCLK_GPIO_NUM);

  // 메모리 상태 확인
  DEBUG_PRINTF("  Free heap: %d bytes\n", ESP.getFreeHeap());
  DEBUG_PRINTF("  Free PSRAM: %d bytes\n", ESP.getFreePsram());
  DEBUG_PRINTF("  PSRAM size: %d bytes\n", ESP.getPsramSize());

  // 카메라 초기화 (여러 단계 fallback)
  esp_err_t err = esp_camera_init(&camera_config);

  // 초기화 실패 시 fallback 로직
  if (err != ESP_OK)
  {
    DEBUG_PRINTF("❌ Camera init failed with error: 0x%x\n", err);

    switch (err)
    {
    case ESP_ERR_INVALID_ARG:
      DEBUG_PRINTLN("   Error: Invalid argument - Check pin definitions!");
      return false;

    case ESP_ERR_NO_MEM:
      DEBUG_PRINTLN("   Error: Not enough memory");

      // Fallback 1: 단일 프레임 버퍼로 재시도
      if (camera_config.fb_count > 1)
      {
        DEBUG_PRINTLN("   Fallback 1: Trying with single frame buffer...");
        camera_config.fb_count = 1;
        err = esp_camera_init(&camera_config);
        if (err == ESP_OK)
        {
          DEBUG_PRINTLN("   ✅ Camera initialized with single buffer");
          goto init_success;
        }
        DEBUG_PRINTF("   Still failed: 0x%x\n", err);
      }

      // Fallback 2: DRAM 사용 (PSRAM 대신)
      if (camera_config.fb_location == CAMERA_FB_IN_PSRAM)
      {
        DEBUG_PRINTLN("   Fallback 2: Trying DRAM instead of PSRAM...");
        camera_config.fb_location = CAMERA_FB_IN_DRAM;
        camera_config.fb_count = 1;
        err = esp_camera_init(&camera_config);
        if (err == ESP_OK)
        {
          DEBUG_PRINTLN("   ✅ Camera initialized with DRAM");
          goto init_success;
        }
        DEBUG_PRINTF("   Still failed: 0x%x\n", err);
      }

      // Fallback 3: 해상도 낮추기
      if (camera_config.frame_size > FRAMESIZE_QVGA)
      {
        DEBUG_PRINTLN("   Fallback 3: Reducing resolution to QVGA (320x240)...");
        camera_config.frame_size = FRAMESIZE_QVGA;
        camera_config.fb_location = CAMERA_FB_IN_DRAM;
        camera_config.fb_count = 1;
        err = esp_camera_init(&camera_config);
        if (err == ESP_OK)
        {
          DEBUG_PRINTLN("   ✅ Camera initialized with reduced resolution");
          goto init_success;
        }
        DEBUG_PRINTF("   Still failed: 0x%x\n", err);
      }

      // Fallback 4: 최소 해상도 (QQVGA - 160x120)
      DEBUG_PRINTLN("   Fallback 4: Trying minimum resolution QQVGA (160x120)...");
      camera_config.frame_size = FRAMESIZE_QQVGA;
      camera_config.fb_location = CAMERA_FB_IN_DRAM;
      camera_config.fb_count = 1;
      camera_config.jpeg_quality = 12; // 품질도 낮춤
      err = esp_camera_init(&camera_config);
      if (err == ESP_OK)
      {
        DEBUG_PRINTLN("   ✅ Camera initialized with minimum resolution");
        goto init_success;
      }

      DEBUG_PRINTLN("   ❌ All fallback attempts failed!");
      return false;

    case ESP_ERR_NOT_FOUND:
      DEBUG_PRINTLN("   Error: Camera not found - Check hardware connection!");
      return false;

    default:
      DEBUG_PRINTF("   Unknown error: 0x%x\n", err);
      return false;
    }
  }

init_success:

  // 카메라 센서 설정
  sensor_t *s = esp_camera_sensor_get();
  if (s == NULL)
  {
    DEBUG_PRINTLN("❌ Failed to get camera sensor");
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
  DEBUG_PRINTLN("✓ Camera initialized successfully");

  return true;
}

/**
 * 카메라 시작
 */
bool cameraStart()
{
  if (!cameraInitialized)
  {
    DEBUG_PRINTLN("Camera not initialized");
    return false;
  }

  cameraStreamActive = true;
  cameraPaused = false;
  DEBUG_PRINTLN("Camera streaming started");

  return true;
}

/**
 * RTSP 서버 시작
 */
bool rtspServerStart()
{
  if (rtspServerActive)
  {
    DEBUG_PRINTLN("RTSP server already running");
    return true;
  }

  DEBUG_PRINTLN("Starting RTSP server...");

  // RTSP 서버 시작
  rtspServer.begin();
  rtspServerActive = true;

  DEBUG_PRINTF("✅ RTSP server started on port %d\n", RTSP_PORT);
  DEBUG_PRINTF("📺 RTSP URL: rtsp://%s:%d/mjpeg/1\n", WiFi.localIP().toString().c_str(), RTSP_PORT);

  return true;
}

/**
 * RTSP 서버 정지
 */
void rtspServerStop()
{
  if (!rtspServerActive)
  {
    return;
  }

  DEBUG_PRINTLN("Stopping RTSP server...");

  // 클라이언트 연결 종료
  if (rtspClient.connected())
  {
    rtspClient.stop();
  }

  rtspServer.stop();
  rtspServerActive = false;

  DEBUG_PRINTLN("✅ RTSP server stopped");
}

/**
 * RTSP 서버 루프 (클라이언트 연결 처리)
 *
 * 참고: 기본 RTSP 프로토콜 구현
 * 향후 Micro-RTSP 라이브러리 통합 예정
 */
void rtspServerLoop()
{
  if (!rtspServerActive)
  {
    return;
  }

  // 새 클라이언트 연결 확인
  WiFiClient newClient = rtspServer.available();
  if (newClient)
  {
    DEBUG_PRINTLN("🔗 RTSP client connected");

    // 기존 클라이언트가 있으면 종료
    if (rtspClient.connected())
    {
      rtspClient.stop();
    }

    rtspClient = newClient;
  }

  // 클라이언트 요청 처리
  if (rtspClient && rtspClient.connected())
  {
    if (rtspClient.available())
    {
      String request = rtspClient.readStringUntil('\n');
      DEBUG_PRINTF("RTSP Request: %s\n", request.c_str());

      // 기본 RTSP 응답 (OPTIONS, DESCRIBE 등)
      // 향후 완전한 RTSP 프로토콜 구현 예정
      if (request.indexOf("OPTIONS") >= 0)
      {
        rtspClient.println("RTSP/1.0 200 OK");
        rtspClient.println("CSeq: 1");
        rtspClient.println("Public: OPTIONS, DESCRIBE, SETUP, PLAY, TEARDOWN");
        rtspClient.println();
      }
      else if (request.indexOf("DESCRIBE") >= 0)
      {
        rtspClient.println("RTSP/1.0 200 OK");
        rtspClient.println("CSeq: 2");
        rtspClient.println("Content-Type: application/sdp");
        rtspClient.println();
        rtspClient.println("v=0");
        rtspClient.println("o=- 0 0 IN IP4 127.0.0.1");
        rtspClient.println("s=ESP32-CAM Stream");
        rtspClient.println("m=video 0 RTP/AVP 26");
        rtspClient.println();
      }
    }
  }
  else if (rtspClient && !rtspClient.connected())
  {
    DEBUG_PRINTLN("🔌 RTSP client disconnected");
    rtspClient.stop();
  }
}

/**
 * 카메라 일시정지
 */
void cameraPause()
{
  cameraPaused = true;
  DEBUG_PRINTLN("Camera streaming paused");
}

/**
 * 카메라 정지
 */
void cameraStop()
{
  cameraStreamActive = false;
  cameraPaused = false;

  // 영상 sink 정리
  if (::sinkActive)
  {
    cameraClearSink();
  }

  // RTSP 서버 정지
  if (rtspServerActive)
  {
    rtspServerStop();
  }

  DEBUG_PRINTLN("Camera streaming stopped");
}

/**
 * MJPEG 스틸컷 전송 (HTTP POST)
 */
static void sendMjpegStill(camera_fb_t *fb)
{
  if (::sinkUrl.length() == 0)
  {
    return;
  }

  DEBUG_PRINTF("📤 MJPEG 스틸컷 전송: %d bytes → %s\n", fb->len,
               ::sinkUrl.c_str());

  httpClient.begin(::sinkUrl);
  httpClient.addHeader("Content-Type", "image/jpeg");
  httpClient.addHeader("Content-Length", String(fb->len));

  int httpCode = httpClient.POST(fb->buf, fb->len);

  if (httpCode > 0)
  {
    if (httpCode == HTTP_CODE_OK || httpCode == HTTP_CODE_CREATED)
    {
      DEBUG_PRINTLN("✅ MJPEG 스틸컷 전송 성공");
    }
    else
    {
      DEBUG_PRINTF("⚠️ MJPEG 스틸컷 전송 응답: %d\n", httpCode);
    }
  }
  else
  {
    DEBUG_PRINTF("❌ MJPEG 스틸컷 전송 실패: %s\n",
                 httpClient.errorToString(httpCode).c_str());
  }

  httpClient.end();
}

/**
 * WebSocket 실시간 스트림 전송
 */
static void sendWebSocketStream(camera_fb_t *fb)
{
  if (::sinkUrl.length() == 0)
  {
    return;
  }

  // WebSocket 연결 확인 및 연결
  if (!::wsStreamConnected)
  {
    // WebSocket URL 파싱 (ws:// 또는 wss://)
    String wsUrl = ::sinkUrl;
    if (!wsUrl.startsWith("ws://") && !wsUrl.startsWith("wss://"))
    {
      DEBUG_PRINTLN("❌ WebSocket URL 형식 오류 (ws:// 또는 wss:// 필요)");
      return;
    }

    DEBUG_PRINTF("🔗 WebSocket 연결 시도: %s\n", wsUrl.c_str());

    // WebSocket 연결
    bool connected = wsStreamClient.connect(wsUrl);
    if (connected)
    {
      ::wsStreamConnected = true;
      DEBUG_PRINTLN("✅ WebSocket 카메라 스트림 연결 성공");

      // 연결 성공 메시지 전송
      wsStreamClient.send("{\"type\":\"camera_stream_connected\"}");
    }
    else
    {
      DEBUG_PRINTLN("❌ WebSocket 카메라 스트림 연결 실패");
      ::wsStreamConnected = false;
      return;
    }
  }

  // WebSocket 연결 상태 확인
  if (!wsStreamClient.available())
  {
    DEBUG_PRINTLN("⚠️ WebSocket 연결이 끊어졌습니다. 재연결 시도...");
    ::wsStreamConnected = false;
    return;
  }

  // MJPEG 프레임을 바이너리로 전송
  // 프레임 헤더: [4 bytes 길이] + [JPEG 데이터]
  uint8_t header[4];
  header[0] = (fb->len >> 24) & 0xFF;
  header[1] = (fb->len >> 16) & 0xFF;
  header[2] = (fb->len >> 8) & 0xFF;
  header[3] = fb->len & 0xFF;

  // 헤더 + 데이터를 합쳐서 전송
  size_t totalSize = 4 + fb->len;
  uint8_t *buffer = (uint8_t *)malloc(totalSize);
  if (buffer == NULL)
  {
    DEBUG_PRINTLN("❌ WebSocket 전송 버퍼 할당 실패");
    return;
  }

  memcpy(buffer, header, 4);
  memcpy(buffer + 4, fb->buf, fb->len);

  bool sent = wsStreamClient.sendBinary((const char *)buffer, totalSize);
  free(buffer);

  if (sent)
  {
    DEBUG_PRINTF("📤 WebSocket 프레임 전송: %d bytes\n", fb->len);
  }
  else
  {
    DEBUG_PRINTLN("❌ WebSocket 프레임 전송 실패");
    ::wsStreamConnected = false;
  }

  // WebSocket 이벤트 폴링
  wsStreamClient.poll();
}

/**
 * 카메라 루프
 */
void cameraLoop()
{
  // RTSP 서버 루프 (항상 실행)
  rtspServerLoop();

  if (!cameraStreamActive || cameraPaused)
  {
    return;
  }

  // sink가 활성화되어 있지 않으면 기본 동작 (프레임만 캡처)
  if (!::sinkActive || ::sinkUrl.length() == 0)
  {
    camera_fb_t *fb = esp_camera_fb_get();
    if (fb)
    {
      esp_camera_fb_return(fb);
    }
    delay(33); // ~30 FPS
    return;
  }

  // sink 전송 모드에 따라 처리
  unsigned long currentTime = millis();

  if (::streamMode == "mjpeg_stills")
  {
    // MJPEG 스틸컷: 주기적으로 전송
    if (currentTime - ::lastFrameTime >= ::frameInterval)
    {
      camera_fb_t *fb = esp_camera_fb_get();
      if (fb)
      {
        sendMjpegStill(fb);
        esp_camera_fb_return(fb);
        ::lastFrameTime = currentTime;
      }
    }
    delay(10); // CPU 부하 감소
  }
  else if (::streamMode == "realtime_websocket")
  {
    // WebSocket 실시간 스트림: 최대 FPS로 전송
    camera_fb_t *fb = esp_camera_fb_get();
    if (fb)
    {
      sendWebSocketStream(fb);
      esp_camera_fb_return(fb);
    }
    delay(33); // ~30 FPS
  }
  else if (::streamMode == "realtime_rtsp")
  {
    // RTSP 실시간 스트림은 rtspServerLoop()에서 자동으로 처리됨
    // 여기서는 별도 처리 불필요 (RTSP 서버가 자체적으로 프레임 캡처)
    delay(10); // CPU 부하 감소
  }
  else
  {
    // 알 수 없는 모드
    camera_fb_t *fb = esp_camera_fb_get();
    if (fb)
    {
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
                   int frameInterval)
{
  if (!sinkUrl || strlen(sinkUrl) == 0)
  {
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
  if (::streamMode == "mjpeg_stills")
  {
    DEBUG_PRINTF("   주기: %d ms\n", ::frameInterval);
  }

  // WebSocket 스트림 모드일 경우 연결 초기화
  if (::streamMode == "realtime_websocket")
  {
    ::wsStreamConnected = false;
  }

  // RTSP 스트림 모드일 경우 RTSP 서버 시작
  if (::streamMode == "realtime_rtsp")
  {
    rtspServerStart();
  }
}

/**
 * 영상 sink 설정 초기화
 */
void cameraClearSink()
{
  ::sinkUrl = "";
  ::streamMode = "";
  ::sinkActive = false;

  // WebSocket 연결 종료
  if (::wsStreamConnected)
  {
    wsStreamClient.close();
    ::wsStreamConnected = false;
    DEBUG_PRINTLN("🔌 WebSocket 카메라 스트림 연결 종료");
  }

  // HTTP 클라이언트 종료
  httpClient.end();

  DEBUG_PRINTLN("📹 영상 sink 설정 초기화");
}

/**
 * 영상 sink 활성 상태 확인
 */
bool isCameraSinkActive() { return ::sinkActive && ::sinkUrl.length() > 0; }
