/**
 * 카메라 모듈
 * 
 * OV2640 카메라 제어 및 RTSP 스트리밍
 * 참고: ESP32-Camera 라이브러리
 */

#include <Arduino.h>
#include "esp_camera.h"
#include "camera_module.h"
#include "config.h"
#include "pins.h"

// 카메라 설정
static camera_config_t camera_config = {
    .pin_pwdn = PWDN_GPIO_NUM,
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
    .grab_mode = CAMERA_GRAB_LATEST
};

static bool cameraInitialized = false;
static bool cameraStreamActive = false;
static bool cameraPaused = false;

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
    sensor_t* s = esp_camera_sensor_get();
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
    DEBUG_PRINTLN("Camera streaming stopped");
    
    // TODO: RTSP 서버 정지
    // rtspServer.stop();
}

/**
 * 카메라 루프
 */
void cameraLoop() {
    if (!cameraStreamActive || cameraPaused) {
        return;
    }
    
    // 프레임 캡처
    camera_fb_t* fb = esp_camera_fb_get();
    if (!fb) {
        DEBUG_PRINTLN("Camera capture failed");
        return;
    }
    
    // TODO: RTSP 스트림으로 프레임 전송
    // rtspServer.sendFrame(fb->buf, fb->len);
    
    // 프레임 버퍼 반환
    esp_camera_fb_return(fb);
    
    delay(33);  // ~30 FPS
}

/**
 * 카메라 활성 상태 확인
 */
bool isCameraActive() {
    return cameraStreamActive && !cameraPaused;
}

