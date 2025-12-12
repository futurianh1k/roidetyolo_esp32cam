#include "asr_service.h"
#include "../audio/audio_service.h"
#include "../config.h"
#include "../network/websocket_client.h"
#include <cJSON.h>
#include <cstring>
#include <esp_http_client.h>
#include <esp_log.h>
#include <sstream>
#include <stdio.h>
#include <sys/time.h>
#include <time.h>

#define TAG "ASRService"
#define AUDIO_STREAM_BUFFER_SIZE 320 // 20ms @ 16kHz

ASRService::ASRService() {
  audio_service_ = nullptr;
  ws_client_ = nullptr;
  session_active_ = false;
  audio_stream_task_handle_ = nullptr;
}

ASRService::~ASRService() {
  StopSession();
  if (ws_client_) {
    delete ws_client_;
  }
}

bool ASRService::Initialize(AudioService *audio_service) {
  if (!audio_service) {
    ESP_LOGE(TAG, "AudioService is null");
    return false;
  }

  audio_service_ = audio_service;
  ws_client_ = new WebSocketClient();

  // WebSocket 연결 콜백 설정
  ws_client_->SetConnectionCallback(
      [this](bool connected) { OnWebSocketConnected(connected); });

  // 인식 결과 콜백 설정
  ws_client_->SetRecognitionCallback(
      [this](const std::string &text, bool is_final, bool is_emergency) {
        OnRecognitionResult(text, is_final, is_emergency);
      });

  ESP_LOGI(TAG, "ASR service initialized");
  return true;
}

bool ASRService::CreateASRSession(const std::string &language) {
  // HTTP 클라이언트로 ASR 세션 생성
  std::string url = std::string(ASR_SERVER_API_URL) + "/api/v1/sessions";

  esp_http_client_config_t config = {};
  config.url = url.c_str();
  config.method = HTTP_METHOD_POST;
  config.timeout_ms = 10000;

  esp_http_client_handle_t client = esp_http_client_init(&config);
  if (!client) {
    ESP_LOGE(TAG, "Failed to create HTTP client");
    return false;
  }

  // 요청 본문 생성
  cJSON *json = cJSON_CreateObject();
  cJSON_AddStringToObject(json, "device_id", DEVICE_ID);
  cJSON_AddStringToObject(json, "language", language.c_str());
  cJSON_AddTrueToObject(json, "vad_enabled");

  char *json_str = cJSON_Print(json);
  esp_http_client_set_post_field(client, json_str, strlen(json_str));
  esp_http_client_set_header(client, "Content-Type", "application/json");

  esp_err_t err = esp_http_client_perform(client);
  if (err == ESP_OK) {
    int status_code = esp_http_client_get_status_code(client);
    if (status_code == 200 || status_code == 201) {
      int content_length = esp_http_client_get_content_length(client);
      char *response = (char *)malloc(content_length + 1);
      esp_http_client_read_response(client, response, content_length);
      response[content_length] = '\0';

      // JSON 파싱
      cJSON *response_json = cJSON_Parse(response);
      if (response_json) {
        cJSON *session_id_item =
            cJSON_GetObjectItem(response_json, "session_id");
        cJSON *ws_url_item = cJSON_GetObjectItem(response_json, "ws_url");

        if (session_id_item && cJSON_IsString(session_id_item) && ws_url_item &&
            cJSON_IsString(ws_url_item)) {
          session_id_ = session_id_item->valuestring;
          ws_url_ = ws_url_item->valuestring;
          cJSON_Delete(response_json);
          free(response);
          free(json_str);
          cJSON_Delete(json);
          esp_http_client_cleanup(client);
          ESP_LOGI(TAG, "ASR session created: %s", session_id_.c_str());
          return true;
        }
        cJSON_Delete(response_json);
      }
      free(response);
    } else {
      ESP_LOGE(TAG, "HTTP error: %d", status_code);
    }
  } else {
    ESP_LOGE(TAG, "HTTP request failed: %s", esp_err_to_name(err));
  }

  free(json_str);
  cJSON_Delete(json);
  esp_http_client_cleanup(client);
  return false;
}

bool ASRService::StartSession(const std::string &language,
                              const std::string &ws_url) {
  if (session_active_) {
    ESP_LOGW(TAG, "Session already active");
    return true;
  }

  // ws_url이 제공되면 사용, 없으면 ASR 서버에서 세션 생성
  if (!ws_url.empty()) {
    ws_url_ = ws_url;
    // session_id는 ws_url에서 추출하거나 나중에 받음
    ESP_LOGI(TAG, "Using provided WebSocket URL: %s", ws_url_.c_str());
  } else {
    if (!CreateASRSession(language)) {
      ESP_LOGE(TAG, "Failed to create ASR session");
      return false;
    }
  }

  // WebSocket 연결
  if (!ws_client_->Connect(ws_url_)) {
    ESP_LOGE(TAG, "Failed to connect WebSocket");
    return false;
  }

  // WebSocket 연결 후 오디오 형식 메타데이터는 전송하지 않음
  // ASR 서버는 연결 시 자동으로 형식을 인식하거나, 세션 생성 시 이미 형식을
  // 알고 있음

  // 오디오 스트림 태스크 시작
  if (audio_stream_task_handle_ == nullptr) {
    xTaskCreate(AudioStreamTask, "asr_audio", 4096, this, 5,
                &audio_stream_task_handle_);
  }

  // 마이크 시작
  if (audio_service_) {
    audio_service_->StartMicrophone();
  }

  session_active_ = true;
  ESP_LOGI(TAG, "ASR session started");
  return true;
}

void ASRService::StopSession() {
  if (!session_active_) {
    return;
  }

  // 마이크 중지
  if (audio_service_) {
    audio_service_->StopMicrophone();
  }

  // 오디오 스트림 태스크 종료
  if (audio_stream_task_handle_) {
    TaskHandle_t handle = audio_stream_task_handle_;
    audio_stream_task_handle_ = nullptr;
    vTaskDelay(pdMS_TO_TICKS(100));
    vTaskDelete(handle);
  }

  // WebSocket 연결 해제
  if (ws_client_) {
    ws_client_->Disconnect();
  }

  session_active_ = false;
  session_id_.clear();
  ws_url_.clear();
  ESP_LOGI(TAG, "ASR session stopped");
}

void ASRService::SetRecognitionCallback(RecognitionCallback callback) {
  recognition_callback_ = callback;
}

void ASRService::OnRecognitionResult(const std::string &text, bool is_final,
                                     bool is_emergency) {
  ESP_LOGI(TAG, "Recognition: %s (final=%d, emergency=%d)", text.c_str(),
           is_final, is_emergency);

  // 최종 결과만 백엔드로 전송
  if (is_final && !text.empty()) {
    // HTTP POST로 백엔드에 결과 전송
    std::string url = std::string(BACKEND_URL) + "/api/asr/result";

    esp_http_client_config_t config = {};
    config.url = url.c_str();
    config.method = HTTP_METHOD_POST;
    config.timeout_ms = 5000;

    esp_http_client_handle_t client = esp_http_client_init(&config);
    if (client) {
      // 현재 시간 가져오기 (ISO 8601 형식)
      struct timeval tv;
      gettimeofday(&tv, nullptr);
      struct tm timeinfo;
      localtime_r(&tv.tv_sec, &timeinfo);
      char timestamp[64];
      strftime(timestamp, sizeof(timestamp), "%Y-%m-%dT%H:%M:%S", &timeinfo);
      // 밀리초 추가
      char timestamp_with_ms[80];
      snprintf(timestamp_with_ms, sizeof(timestamp_with_ms), "%s.%03ld",
               timestamp, tv.tv_usec / 1000);

      // 요청 본문 생성 (RecognitionResult 스키마에 맞춤)
      cJSON *json = cJSON_CreateObject();
      cJSON_AddStringToObject(json, "type", "recognition_result");
      // device_id는 백엔드에서 device_id_string으로 장비를 찾아서 처리
      cJSON_AddStringToObject(json, "device_id_string", DEVICE_ID);
      cJSON_AddStringToObject(json, "device_name", DEVICE_NAME);
      cJSON_AddStringToObject(json, "session_id", session_id_.c_str());
      cJSON_AddStringToObject(json, "text", text.c_str());
      cJSON_AddStringToObject(json, "timestamp", timestamp_with_ms);
      cJSON_AddNumberToObject(json, "duration",
                              0.0); // TODO: 실제 duration 계산
      cJSON_AddBoolToObject(json, "is_emergency", is_emergency);

      // emergency_keywords 배열
      cJSON *keywords_array = cJSON_CreateArray();
      if (is_emergency) {
        // TODO: 실제 키워드 추출
      }
      cJSON_AddItemToObject(json, "emergency_keywords", keywords_array);

      char *json_str = cJSON_Print(json);
      esp_http_client_set_post_field(client, json_str, strlen(json_str));
      esp_http_client_set_header(client, "Content-Type", "application/json");

      esp_err_t err = esp_http_client_perform(client);
      if (err == ESP_OK) {
        int status_code = esp_http_client_get_status_code(client);
        if (status_code >= 200 && status_code < 300) {
          ESP_LOGI(TAG, "Recognition result sent to backend: %s", text.c_str());
        } else {
          ESP_LOGW(TAG, "Backend returned status: %d", status_code);
        }
      } else {
        ESP_LOGW(TAG, "Failed to send result to backend: %s",
                 esp_err_to_name(err));
      }

      free(json_str);
      cJSON_Delete(json);
      esp_http_client_cleanup(client);
    }
  }

  if (recognition_callback_) {
    recognition_callback_(text, is_final, is_emergency);
  }
}

void ASRService::OnWebSocketConnected(bool connected) {
  if (connected) {
    ESP_LOGI(TAG, "WebSocket connected to ASR server");
  } else {
    ESP_LOGW(TAG, "WebSocket disconnected from ASR server");
    // 재연결 시도는 WebSocketClient에서 자동 처리
    // reconnect_timeout_ms (5초) 후 자동 재연결 시도
    // 세션이 활성 상태이면 재연결 후 계속 사용 가능
  }
}

void ASRService::SendAudioToASR() {
  if (!session_active_ || !ws_client_ || !ws_client_->IsConnected() ||
      !audio_service_) {
    return;
  }

  std::vector<int16_t> buffer(AUDIO_STREAM_BUFFER_SIZE);
  if (audio_service_->ReadPCM(buffer, AUDIO_STREAM_BUFFER_SIZE)) {
    // PCM 데이터를 WebSocket으로 전송
    ws_client_->SendAudio((const uint8_t *)buffer.data(),
                          buffer.size() * sizeof(int16_t));
  }
}

void ASRService::AudioStreamTask(void *arg) {
  ASRService *service = static_cast<ASRService *>(arg);
  service->AudioStreamTaskImpl();
}

void ASRService::AudioStreamTaskImpl() {
  const TickType_t delay = pdMS_TO_TICKS(20); // 20ms = 1 frame

  while (session_active_) {
    SendAudioToASR();
    vTaskDelay(delay);
  }

  vTaskDelete(nullptr);
}
