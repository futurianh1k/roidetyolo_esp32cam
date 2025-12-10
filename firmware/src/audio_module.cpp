/**
 * 오디오 모듈
 *
 * I2S 마이크/스피커 제어
 * ASR (음성인식) 모드 지원 - WebSocket 스트리밍
 *
 * 참고:
 * - ESP32 I2S 라이브러리
 * - ArduinoWebsockets 라이브러리
 */

#include "audio_module.h"
#include "config.h"
#include "pins.h"
#include "websocket_module.h"
#include <Arduino.h>
#include <HTTPClient.h>
#include <driver/i2s.h>

// I2S 포트
#define I2S_PORT_OUT I2S_NUM_0 // 스피커
#define I2S_PORT_IN I2S_NUM_1  // 마이크

static bool audioInitialized = false;
static bool microphoneActive = false;
static bool microphonePaused = false;
static bool speakerPlaying = false;
static uint8_t currentVolume = 70; // 기본 볼륨 70%

// ASR 모드 관련
static bool asrMode = false;           // ASR 모드 활성 여부
static unsigned long asrStartTime = 0; // ASR 시작 시각

// 오디오 재생 Task 관련
static TaskHandle_t audioPlayTaskHandle = NULL;
static char audioPlayURL_buffer[256] = {0}; // URL 버퍼 (Task에서 사용)

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
      .fixed_mclk = 0};

  i2s_pin_config_t pin_config_out = {.bck_io_num = I2S_OUT_BCK,
                                     .ws_io_num = I2S_OUT_WS,
                                     .data_out_num = I2S_OUT_DATA,
                                     .data_in_num = I2S_PIN_NO_CHANGE};

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
      .fixed_mclk = 0};

  i2s_pin_config_t pin_config_in = {.bck_io_num = I2S_IN_BCK,
                                    .ws_io_num = I2S_IN_WS,
                                    .data_out_num = I2S_PIN_NO_CHANGE,
                                    .data_in_num = I2S_IN_DATA};

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
 * 오디오 재생 Task (FreeRTOS)
 * 
 * 별도 Task로 실행하여 메인 루프 블로킹 방지
 * MQTT keepalive와 WiFi 유지 보장
 */
void audioPlayTask(void *parameter) {
  const char *url = (const char *)parameter;
  
  DEBUG_PRINTF("🔊 Audio Task 시작: %s\n", url);

  HTTPClient http;
  http.begin(url);
  http.setTimeout(30000); // 30초 타임아웃
  http.setReuse(false);   // 연결 재사용 비활성화

  int httpCode = http.GET();

  if (httpCode != HTTP_CODE_OK) {
    DEBUG_PRINTF("❌ HTTP GET 실패, error: %d\n", httpCode);
    http.end();
    speakerPlaying = false;
    audioPlayTaskHandle = NULL;
    vTaskDelete(NULL);
    return;
  }

  // 스트림 가져오기
  WiFiClient *stream = http.getStreamPtr();

  if (!stream) {
    DEBUG_PRINTLN("❌ 스트림 포인터 획득 실패");
    http.end();
    speakerPlaying = false;
    audioPlayTaskHandle = NULL;
    vTaskDelete(NULL);
    return;
  }

  // 버퍼
  const size_t bufferSize = 1024;
  uint8_t *buffer = (uint8_t *)malloc(bufferSize);
  
  if (!buffer) {
    DEBUG_PRINTLN("❌ 버퍼 메모리 할당 실패");
    http.end();
    speakerPlaying = false;
    audioPlayTaskHandle = NULL;
    vTaskDelete(NULL);
    return;
  }

  // I2S 쓰기 시작
  i2s_start(I2S_PORT_OUT);

  DEBUG_PRINTLN("🎵 스트리밍 시작...");

  unsigned long lastProgressReport = millis();
  unsigned long totalBytesPlayed = 0;

  // 스트리밍 재생
  while (http.connected() && speakerPlaying) {
    // WiFi 연결 체크
    if (WiFi.status() != WL_CONNECTED) {
      DEBUG_PRINTLN("⚠️ WiFi 연결 끊김, 재생 중단");
      break;
    }

    size_t available = stream->available();

    if (available) {
      size_t bytesToRead = min(available, bufferSize);
      size_t bytesRead = stream->readBytes(buffer, bytesToRead);

      if (bytesRead > 0) {
        // 볼륨 조절
        if (currentVolume < 100) {
          for (size_t i = 0; i < bytesRead; i += 2) {
            int16_t *sample = (int16_t *)&buffer[i];
            *sample = (*sample * currentVolume) / 100;
          }
        }

        // I2S 쓰기 (타임아웃 설정)
        size_t bytesWritten;
        esp_err_t result = i2s_write(I2S_PORT_OUT, buffer, bytesRead, 
                                      &bytesWritten, pdMS_TO_TICKS(1000));
        
        if (result != ESP_OK) {
          DEBUG_PRINTF("⚠️ I2S write 실패: %d\n", result);
        }

        totalBytesPlayed += bytesWritten;
      }
    }

    // 진행 상황 출력 (5초마다)
    if (millis() - lastProgressReport > 5000) {
      DEBUG_PRINTF("🎵 재생 중... (%lu KB)\n", totalBytesPlayed / 1024);
      lastProgressReport = millis();
    }

    // Task 양보 (다른 Task들이 실행될 수 있도록)
    vTaskDelay(pdMS_TO_TICKS(1));
  }

  // 정리
  free(buffer);
  i2s_stop(I2S_PORT_OUT);
  http.end();

  speakerPlaying = false;
  audioPlayTaskHandle = NULL;

  DEBUG_PRINTLN("✅ 오디오 재생 완료");
  
  // Task 자가 삭제
  vTaskDelete(NULL);
}

/**
 * URL에서 오디오 재생
 * 
 * FreeRTOS Task로 실행하여 비블로킹 방식으로 재생
 */
bool audioPlayURL(const char *url) {
  if (!audioInitialized) {
    DEBUG_PRINTLN("❌ Audio not initialized");
    return false;
  }

  // 이미 재생 중이면 중단
  if (speakerPlaying && audioPlayTaskHandle != NULL) {
    DEBUG_PRINTLN("⚠️ 이미 오디오 재생 중, 기존 재생 중단");
    audioStopSpeaker();
    // Task 종료 대기
    vTaskDelay(pdMS_TO_TICKS(100));
  }

  // URL 복사 (Task에서 사용)
  strncpy(audioPlayURL_buffer, url, sizeof(audioPlayURL_buffer) - 1);
  audioPlayURL_buffer[sizeof(audioPlayURL_buffer) - 1] = '\0';

  speakerPlaying = true;

  // Task 생성 (Core 0에서 실행, 우선순위 1)
  BaseType_t result = xTaskCreatePinnedToCore(
      audioPlayTask,          // Task 함수
      "AudioPlayTask",        // Task 이름
      8192,                   // 스택 크기 (8KB)
      (void *)audioPlayURL_buffer, // 파라미터
      1,                      // 우선순위
      &audioPlayTaskHandle,   // Task 핸들
      0                       // Core 0
  );

  if (result != pdPASS) {
    DEBUG_PRINTLN("❌ Audio Task 생성 실패");
    speakerPlaying = false;
    return false;
  }

  DEBUG_PRINTLN("✅ Audio Task 생성 성공");
  return true;
}

/**
 * 볼륨 설정 (0-100)
 */
void audioSetVolume(uint8_t volume) {
  if (volume > 100)
    volume = 100;
  currentVolume = volume;
  DEBUG_PRINTF("Volume set to: %d%%\n", volume);
}

/**
 * 스피커 정지
 */
void audioStopSpeaker() {
  speakerPlaying = false;
  
  // Task가 실행 중이면 종료 대기
  if (audioPlayTaskHandle != NULL) {
    DEBUG_PRINTLN("🛑 Audio Task 종료 대기 중...");
    
    unsigned long startWait = millis();
    while (audioPlayTaskHandle != NULL && (millis() - startWait) < 3000) {
      vTaskDelay(pdMS_TO_TICKS(100));
    }
    
    // 여전히 종료 안되면 강제 종료
    if (audioPlayTaskHandle != NULL) {
      DEBUG_PRINTLN("⚠️ Audio Task 강제 종료");
      vTaskDelete(audioPlayTaskHandle);
      audioPlayTaskHandle = NULL;
    }
  }
  
  i2s_stop(I2S_PORT_OUT);
  DEBUG_PRINTLN("✅ Speaker stopped");
}

/**
 * ASR 모드 시작
 *
 * 음성인식 모드로 마이크를 시작합니다.
 * WebSocket으로 오디오 스트리밍을 전송합니다.
 *
 * @return 시작 성공 여부
 */
bool audioStartASRMode() {
  if (!audioInitialized) {
    DEBUG_PRINTLN("Audio not initialized");
    return false;
  }

  if (asrMode) {
    DEBUG_PRINTLN("⚠️ ASR 모드가 이미 활성화되어 있습니다");
    return false;
  }

  DEBUG_PRINTLN("🎤 ASR 모드 시작");

  // 마이크 시작
  if (!audioStartMicrophone()) {
    DEBUG_PRINTLN("❌ 마이크 시작 실패");
    return false;
  }

  asrMode = true;
  asrStartTime = millis();

  DEBUG_PRINTLN("✅ ASR 모드 활성화");
  return true;
}

/**
 * ASR 모드 종료
 */
void audioStopASRMode() {
  if (!asrMode) {
    DEBUG_PRINTLN("⚠️ ASR 모드가 활성화되어 있지 않습니다");
    return;
  }

  DEBUG_PRINTLN("🛑 ASR 모드 종료");

  asrMode = false;
  audioStopMicrophone();

  DEBUG_PRINTLN("✅ ASR 모드 비활성화");
}

/**
 * ASR 모드 확인
 *
 * @return ASR 모드 활성 여부
 */
bool audioIsASRMode() { return asrMode; }

/**
 * 오디오 루프
 *
 * 일반 모드: 오디오 데이터 로컬 처리
 * ASR 모드: WebSocket으로 오디오 스트리밍 전송
 */
void audioLoop() {
  if (!microphoneActive || microphonePaused) {
    return;
  }

  // 마이크 데이터 읽기 (1024 samples = 64ms @ 16kHz)
  const size_t sampleCount = 1024;
  const size_t bufferSize = sampleCount * sizeof(int16_t);
  int16_t audioBuffer[sampleCount];
  size_t bytesRead;

  esp_err_t result =
      i2s_read(I2S_PORT_IN, audioBuffer, bufferSize, &bytesRead, 0);

  if (result == ESP_OK && bytesRead > 0) {
    size_t samplesRead = bytesRead / sizeof(int16_t);

    if (asrMode) {
      // ✨ ASR 모드: WebSocket으로 오디오 전송
      unsigned long timestamp = millis() - asrStartTime;

      // WebSocket으로 오디오 청크 전송
      bool sent = websocketSendAudioChunk(audioBuffer, samplesRead, timestamp);

      if (!sent) {
        DEBUG_PRINTLN("⚠️ WebSocket 오디오 전송 실패");
      }

      // 디버그: 주기적으로 상태 출력 (1초마다)
      static unsigned long lastDebugTime = 0;
      if (millis() - lastDebugTime > 1000) {
        DEBUG_PRINTF("🎤 ASR 스트리밍 중... (%.1f초)\n", timestamp / 1000.0f);
        lastDebugTime = millis();
      }
    } else {
      // 일반 모드: 로컬 처리
      // TODO: 오디오 데이터 처리
      // - 백엔드로 스트리밍
      // - 로컬 저장
      // - 음성 인식 등
    }
  }
}
