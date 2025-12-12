#include "camera_service.h"
#include "../pins.h"
#include "../config.h"
#include <esp_log.h>
#include <esp_camera.h>
#include <esp_http_client.h>
#include <cstring>

#define TAG "CameraService"

static camera_config_t camera_config = {
    .pin_pwdn = (gpio_num_t)PWDN_GPIO_NUM,
    .pin_reset = (gpio_num_t)RESET_GPIO_NUM,
    .pin_xclk = (gpio_num_t)XCLK_GPIO_NUM,
    .pin_sscb_sda = (gpio_num_t)SIOD_GPIO_NUM,
    .pin_sscb_scl = (gpio_num_t)SIOC_GPIO_NUM,
    
    .pin_d7 = (gpio_num_t)Y9_GPIO_NUM,
    .pin_d6 = (gpio_num_t)Y8_GPIO_NUM,
    .pin_d5 = (gpio_num_t)Y7_GPIO_NUM,
    .pin_d4 = (gpio_num_t)Y6_GPIO_NUM,
    .pin_d3 = (gpio_num_t)Y5_GPIO_NUM,
    .pin_d2 = (gpio_num_t)Y4_GPIO_NUM,
    .pin_d1 = (gpio_num_t)Y3_GPIO_NUM,
    .pin_d0 = (gpio_num_t)Y2_GPIO_NUM,
    .pin_vsync = (gpio_num_t)VSYNC_GPIO_NUM,
    .pin_href = (gpio_num_t)HREF_GPIO_NUM,
    .pin_pclk = (gpio_num_t)PCLK_GPIO_NUM,
    
    .xclk_freq_hz = 20000000,
    .ledc_timer = LEDC_TIMER_0,
    .ledc_channel = LEDC_CHANNEL_0,
    
    .pixel_format = PIXFORMAT_JPEG,
    .frame_size = CAMERA_FRAMESIZE,
    .jpeg_quality = CAMERA_QUALITY,
    .fb_count = 1,
    .fb_location = CAMERA_FB_IN_PSRAM,
    .grab_mode = CAMERA_GRAB_WHEN_EMPTY,
};

CameraService::CameraService() {
}

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
    sensor_t* s = esp_camera_sensor_get();
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
    xTaskCreatePinnedToCore(
        CameraTask,
        "camera_task",
        8192,
        this,
        3,  // 우선순위
        &camera_task_handle_,
        1   // Core 1
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

void CameraService::StartStream(const std::string& sink_url, const std::string& stream_mode, int frame_interval_ms) {
    sink_url_ = sink_url;
    stream_mode_ = stream_mode;
    frame_interval_ms_ = frame_interval_ms;
    streaming_active_ = true;
    
    ESP_LOGI(TAG, "Camera stream started: %s, mode: %s, interval: %dms", 
             sink_url.c_str(), stream_mode.c_str(), frame_interval_ms);
}

void CameraService::StopStream() {
    streaming_active_ = false;
    ESP_LOGI(TAG, "Camera stream stopped");
}

bool CameraService::CaptureFrame(std::vector<uint8_t>& jpeg_data) {
    if (!initialized_) {
        return false;
    }
    
    camera_fb_t* fb = esp_camera_fb_get();
    if (!fb) {
        ESP_LOGE(TAG, "Failed to capture frame");
        return false;
    }
    
    jpeg_data.assign(fb->buf, fb->buf + fb->len);
    esp_camera_fb_return(fb);
    
    return true;
}

void CameraService::CameraTask(void* arg) {
    CameraService* service = static_cast<CameraService*>(arg);
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
                    if (stream_mode_ == "http" || stream_mode_ == "mjpeg") {
                        SendFrameHTTP(jpeg_data);
                    }
                    // TODO: WebSocket 스트리밍 추가
                }
                last_frame_time = now;
            }
        }
        
        vTaskDelay(pdMS_TO_TICKS(100));
    }
    
    vTaskDelete(nullptr);
}

bool CameraService::SendFrameHTTP(const std::vector<uint8_t>& jpeg_data) {
    if (sink_url_.empty()) {
        return false;
    }
    
    esp_http_client_config_t config = {};
    config.url = sink_url_.c_str();
    config.method = HTTP_METHOD_POST;
    config.timeout_ms = 5000;
    
    esp_http_client_handle_t client = esp_http_client_init(&config);
    if (!client) {
        ESP_LOGE(TAG, "Failed to init HTTP client");
        return false;
    }
    
    esp_http_client_set_method(client, HTTP_METHOD_POST);
    esp_http_client_set_header(client, "Content-Type", "image/jpeg");
    esp_http_client_set_post_field(client, (const char*)jpeg_data.data(), jpeg_data.size());
    
    esp_err_t err = esp_http_client_perform(client);
    int status_code = esp_http_client_get_status_code(client);
    
    esp_http_client_cleanup(client);
    
    if (err != ESP_OK || status_code != 200) {
        ESP_LOGE(TAG, "HTTP POST failed: %s, status: %d", esp_err_to_name(err), status_code);
        return false;
    }
    
    return true;
}

