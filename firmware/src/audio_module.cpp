/**
 * 오디오 모듈
 * 
 * I2S 마이크/스피커 제어
 * 참고: ESP32 I2S 라이브러리
 */

#include <Arduino.h>
#include <driver/i2s.h>
#include <HTTPClient.h>
#include "audio_module.h"
#include "config.h"
#include "pins.h"

// I2S 포트
#define I2S_PORT_OUT I2S_NUM_0  // 스피커
#define I2S_PORT_IN  I2S_NUM_1  // 마이크

static bool audioInitialized = false;
static bool microphoneActive = false;
static bool microphonePaused = false;
static bool speakerPlaying = false;

/**
 * 오디오 초기화
 */
bool audioInit() {
    if (audioInitialized) {
        DEBUG_PRINTLN("Audio already initialized");
        return true;
    }
    
    DEBUG_PRINTLN("Initializing audio...");
    
    // I2S Output (스피커) 설정
    i2s_config_t i2s_config_out = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
        .sample_rate = I2S_SAMPLE_RATE,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = 8,
        .dma_buf_len = 1024,
        .use_apll = false,
        .tx_desc_auto_clear = true,
        .fixed_mclk = 0
    };
    
    i2s_pin_config_t pin_config_out = {
        .bck_io_num = I2S_OUT_BCK,
        .ws_io_num = I2S_OUT_WS,
        .data_out_num = I2S_OUT_DATA,
        .data_in_num = I2S_PIN_NO_CHANGE
    };
    
    // I2S Output 설치
    esp_err_t err = i2s_driver_install(I2S_PORT_OUT, &i2s_config_out, 0, NULL);
    if (err != ESP_OK) {
        DEBUG_PRINTF("I2S output driver install failed: %d\n", err);
        return false;
    }
    
    err = i2s_set_pin(I2S_PORT_OUT, &pin_config_out);
    if (err != ESP_OK) {
        DEBUG_PRINTF("I2S output set pin failed: %d\n", err);
        return false;
    }
    
    // I2S Input (마이크) 설정
    i2s_config_t i2s_config_in = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
        .sample_rate = I2S_SAMPLE_RATE,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = 8,
        .dma_buf_len = 1024,
        .use_apll = false,
        .tx_desc_auto_clear = false,
        .fixed_mclk = 0
    };
    
    i2s_pin_config_t pin_config_in = {
        .bck_io_num = I2S_IN_BCK,
        .ws_io_num = I2S_IN_WS,
        .data_out_num = I2S_PIN_NO_CHANGE,
        .data_in_num = I2S_IN_DATA
    };
    
    // I2S Input 설치
    err = i2s_driver_install(I2S_PORT_IN, &i2s_config_in, 0, NULL);
    if (err != ESP_OK) {
        DEBUG_PRINTF("I2S input driver install failed: %d\n", err);
        return false;
    }
    
    err = i2s_set_pin(I2S_PORT_IN, &pin_config_in);
    if (err != ESP_OK) {
        DEBUG_PRINTF("I2S input set pin failed: %d\n", err);
        return false;
    }
    
    audioInitialized = true;
    DEBUG_PRINTLN("Audio initialized successfully");
    
    return true;
}

/**
 * 마이크 시작
 */
bool audioStartMicrophone() {
    if (!audioInitialized) {
        DEBUG_PRINTLN("Audio not initialized");
        return false;
    }
    
    microphoneActive = true;
    microphonePaused = false;
    
    // I2S 읽기 시작
    i2s_start(I2S_PORT_IN);
    
    DEBUG_PRINTLN("Microphone started");
    return true;
}

/**
 * 마이크 일시정지
 */
void audioPauseMicrophone() {
    microphonePaused = true;
    i2s_stop(I2S_PORT_IN);
    DEBUG_PRINTLN("Microphone paused");
}

/**
 * 마이크 정지
 */
void audioStopMicrophone() {
    microphoneActive = false;
    microphonePaused = false;
    i2s_stop(I2S_PORT_IN);
    DEBUG_PRINTLN("Microphone stopped");
}

/**
 * URL에서 오디오 재생
 */
bool audioPlayURL(const char* url) {
    if (!audioInitialized) {
        DEBUG_PRINTLN("Audio not initialized");
        return false;
    }
    
    DEBUG_PRINTF("Playing audio from URL: %s\n", url);
    
    HTTPClient http;
    http.begin(url);
    
    int httpCode = http.GET();
    
    if (httpCode != HTTP_CODE_OK) {
        DEBUG_PRINTF("HTTP GET failed, error: %d\n", httpCode);
        http.end();
        return false;
    }
    
    // 스트림 가져오기
    WiFiClient* stream = http.getStreamPtr();
    
    // Null 체크 (안전성 확보)
    if (!stream) {
        DEBUG_PRINTLN("Failed to get stream pointer");
        http.end();
        return false;
    }
    
    speakerPlaying = true;
    
    // 버퍼
    const size_t bufferSize = 1024;
    uint8_t buffer[bufferSize];
    
    // I2S 쓰기 시작
    i2s_start(I2S_PORT_OUT);
    
    // 스트리밍 재생
    while (http.connected() && speakerPlaying) {
        size_t available = stream->available();
        
        if (available) {
            size_t bytesToRead = min(available, bufferSize);
            size_t bytesRead = stream->readBytes(buffer, bytesToRead);
            
            if (bytesRead > 0) {
                size_t bytesWritten;
                i2s_write(I2S_PORT_OUT, buffer, bytesRead, &bytesWritten, portMAX_DELAY);
            }
        }
        
        delay(1);
    }
    
    i2s_stop(I2S_PORT_OUT);
    http.end();
    
    speakerPlaying = false;
    DEBUG_PRINTLN("Audio playback finished");
    
    return true;
}

/**
 * 스피커 정지
 */
void audioStopSpeaker() {
    speakerPlaying = false;
    i2s_stop(I2S_PORT_OUT);
    DEBUG_PRINTLN("Speaker stopped");
}

/**
 * 오디오 루프
 */
void audioLoop() {
    if (!microphoneActive || microphonePaused) {
        return;
    }
    
    // 마이크 데이터 읽기
    const size_t bufferSize = 1024;
    uint8_t buffer[bufferSize];
    size_t bytesRead;
    
    esp_err_t result = i2s_read(I2S_PORT_IN, buffer, bufferSize, &bytesRead, 0);
    
    if (result == ESP_OK && bytesRead > 0) {
        // TODO: 오디오 데이터 처리
        // - 백엔드로 스트리밍
        // - 로컬 저장
        // - 음성 인식 등
    }
}

