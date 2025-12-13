/**
 * @file backend_client.cc
 * @brief 백엔드 서버와 HTTP 통신을 담당하는 클라이언트 구현
 *
 * ESP-IDF HTTP Client를 사용하여 백엔드 서버와 통신합니다.
 *
 * 참고자료:
 * - ESP-IDF HTTP Client:
 * https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/protocols/esp_http_client.html
 */

#include "backend_client.h"
#include <cJSON.h>
#include <cstring>
#include <esp_http_client.h>
#include <esp_log.h>

#define TAG "BackendClient"

// HTTP 응답 버퍼 최대 크기
#define HTTP_RESPONSE_BUFFER_SIZE 2048

// HTTP 타임아웃 (ms)
#define HTTP_TIMEOUT_MS 10000

BackendClient::BackendClient()
    : device_id_(0), is_connected_(false), initialized_(false) {}

BackendClient::~BackendClient() {}

bool BackendClient::Initialize(const std::string &base_url, int device_id) {
  if (base_url.empty() || device_id <= 0) {
    ESP_LOGE(TAG, "Invalid parameters: base_url=%s, device_id=%d",
             base_url.c_str(), device_id);
    return false;
  }

  base_url_ = base_url;
  device_id_ = device_id;
  initialized_ = true;

  ESP_LOGI(TAG, "Initialized with base_url=%s, device_id=%d", base_url_.c_str(),
           device_id_);

  return true;
}

bool BackendClient::SendDeviceStatus(const DeviceStatusData &status) {
  if (!initialized_) {
    ESP_LOGE(TAG, "Client not initialized");
    return false;
  }

  // JSON 페이로드 생성
  cJSON *json = cJSON_CreateObject();
  if (!json) {
    ESP_LOGE(TAG, "Failed to create JSON object");
    return false;
  }

  // 배터리 레벨 (-1이면 null)
  if (status.battery_level >= 0) {
    cJSON_AddNumberToObject(json, "battery_level", status.battery_level);
  } else {
    cJSON_AddNullToObject(json, "battery_level");
  }

  // 메모리 사용량
  cJSON_AddNumberToObject(json, "memory_usage", status.memory_usage);

  // 스토리지 사용량 (-1이면 null)
  if (status.storage_usage >= 0) {
    cJSON_AddNumberToObject(json, "storage_usage", status.storage_usage);
  } else {
    cJSON_AddNullToObject(json, "storage_usage");
  }

  // 온도
  cJSON_AddNumberToObject(json, "temperature", status.temperature);

  // CPU 사용률
  cJSON_AddNumberToObject(json, "cpu_usage", status.cpu_usage);

  // 카메라 상태
  cJSON_AddStringToObject(json, "camera_status", status.camera_status.c_str());

  // 마이크 상태
  cJSON_AddStringToObject(json, "mic_status", status.mic_status.c_str());

  char *json_str = cJSON_PrintUnformatted(json);
  if (!json_str) {
    cJSON_Delete(json);
    ESP_LOGE(TAG, "Failed to print JSON");
    return false;
  }

  std::string json_body = json_str;
  cJSON_free(json_str);
  cJSON_Delete(json);

  // API 경로 생성
  char path[64];
  snprintf(path, sizeof(path), "/devices/%d/status", device_id_);

  // HTTP POST 전송
  std::string response;
  bool success = HttpPost(path, json_body, response);

  if (success) {
    ESP_LOGI(TAG, "Device status sent successfully");
    is_connected_ = true;
  } else {
    ESP_LOGW(TAG, "Failed to send device status");
    is_connected_ = false;
  }

  return success;
}

bool BackendClient::GetDeviceInfo(std::string &out_device_info) {
  if (!initialized_) {
    ESP_LOGE(TAG, "Client not initialized");
    return false;
  }

  char path[64];
  snprintf(path, sizeof(path), "/devices/%d", device_id_);

  return HttpGet(path, out_device_info);
}

bool BackendClient::SendHeartbeat() {
  // Heartbeat는 최소한의 상태만 전송
  DeviceStatusData status;
  status.battery_level = -1; // 미지원
  status.memory_usage = esp_get_free_heap_size();
  status.storage_usage = -1; // 미지원
  status.temperature = 0;    // 센서 없음
  status.cpu_usage = 0;      // 측정 안함
  status.camera_status = "stopped";
  status.mic_status = "stopped";

  return SendDeviceStatus(status);
}

void BackendClient::SendDeviceStatusAsync(const DeviceStatusData &status,
                                          ResponseCallback callback) {
  // ESP-IDF에서는 FreeRTOS Task로 비동기 처리
  // 현재는 동기 방식으로 구현
  std::string response;
  bool success = SendDeviceStatus(status);
  if (callback) {
    callback(success, response);
  }
}

// HTTP 이벤트 핸들러용 구조체
struct HttpEventData {
  char *buffer;
  int buffer_len;
  int data_len;
};

// HTTP 이벤트 핸들러
static esp_err_t http_event_handler(esp_http_client_event_t *evt) {
  HttpEventData *data = (HttpEventData *)evt->user_data;

  switch (evt->event_id) {
  case HTTP_EVENT_ON_DATA:
    if (data && data->buffer && evt->data_len > 0) {
      // 버퍼 오버플로우 방지
      int copy_len = evt->data_len;
      if (data->data_len + copy_len >= data->buffer_len) {
        copy_len = data->buffer_len - data->data_len - 1;
      }
      if (copy_len > 0) {
        memcpy(data->buffer + data->data_len, evt->data, copy_len);
        data->data_len += copy_len;
        data->buffer[data->data_len] = '\0';
      }
    }
    break;
  default:
    break;
  }
  return ESP_OK;
}

bool BackendClient::HttpPost(const std::string &path,
                             const std::string &json_body,
                             std::string &response) {
  std::string url = base_url_ + path;

  // 응답 버퍼
  char *response_buffer = (char *)malloc(HTTP_RESPONSE_BUFFER_SIZE);
  if (!response_buffer) {
    ESP_LOGE(TAG, "Failed to allocate response buffer");
    return false;
  }
  memset(response_buffer, 0, HTTP_RESPONSE_BUFFER_SIZE);

  HttpEventData event_data = {
      .buffer = response_buffer,
      .buffer_len = HTTP_RESPONSE_BUFFER_SIZE,
      .data_len = 0,
  };

  esp_http_client_config_t config = {};
  config.url = url.c_str();
  config.method = HTTP_METHOD_POST;
  config.timeout_ms = HTTP_TIMEOUT_MS;
  config.event_handler = http_event_handler;
  config.user_data = &event_data;
  config.disable_auto_redirect = false;

  esp_http_client_handle_t client = esp_http_client_init(&config);
  if (!client) {
    ESP_LOGE(TAG, "Failed to init HTTP client");
    free(response_buffer);
    return false;
  }

  // Content-Type 설정
  esp_http_client_set_header(client, "Content-Type", "application/json");

  // POST 데이터 설정
  esp_http_client_set_post_field(client, json_body.c_str(), json_body.length());

  // 요청 전송
  esp_err_t err = esp_http_client_perform(client);

  bool success = false;
  if (err == ESP_OK) {
    int status_code = esp_http_client_get_status_code(client);
    ESP_LOGD(TAG, "HTTP POST %s: status=%d", path.c_str(), status_code);

    if (status_code >= 200 && status_code < 300) {
      response = response_buffer;
      success = true;
    } else {
      ESP_LOGW(TAG, "HTTP error: status=%d, response=%s", status_code,
               response_buffer);
    }
  } else {
    ESP_LOGE(TAG, "HTTP POST failed: %s", esp_err_to_name(err));
  }

  esp_http_client_cleanup(client);
  free(response_buffer);

  return success;
}

bool BackendClient::LookupDeviceDbId(const std::string &device_id,
                                     int &out_db_id) {
  // 백엔드 API: GET /devices/?device_id=core_s3_001
  std::string path = "/devices/?device_id=" + device_id;
  std::string response;

  if (!HttpGet(path, response)) {
    ESP_LOGE(TAG, "Failed to lookup device: %s", device_id.c_str());
    return false;
  }

  // JSON 파싱
  cJSON *json = cJSON_Parse(response.c_str());
  if (!json) {
    ESP_LOGE(TAG, "Failed to parse device lookup response");
    return false;
  }

  // devices 배열에서 첫 번째 장비의 id 추출
  cJSON *devices = cJSON_GetObjectItem(json, "devices");
  if (!devices || !cJSON_IsArray(devices) || cJSON_GetArraySize(devices) == 0) {
    ESP_LOGE(TAG, "Device not found: %s", device_id.c_str());
    cJSON_Delete(json);
    return false;
  }

  cJSON *first_device = cJSON_GetArrayItem(devices, 0);
  cJSON *id_item = cJSON_GetObjectItem(first_device, "id");

  if (!id_item || !cJSON_IsNumber(id_item)) {
    ESP_LOGE(TAG, "Invalid device ID in response");
    cJSON_Delete(json);
    return false;
  }

  out_db_id = id_item->valueint;
  ESP_LOGI(TAG, "Device lookup success: %s -> DB ID %d", device_id.c_str(),
           out_db_id);

  cJSON_Delete(json);
  return true;
}

bool BackendClient::HttpGet(const std::string &path, std::string &response) {
  std::string url = base_url_ + path;

  // 응답 버퍼
  char *response_buffer = (char *)malloc(HTTP_RESPONSE_BUFFER_SIZE);
  if (!response_buffer) {
    ESP_LOGE(TAG, "Failed to allocate response buffer");
    return false;
  }
  memset(response_buffer, 0, HTTP_RESPONSE_BUFFER_SIZE);

  HttpEventData event_data = {
      .buffer = response_buffer,
      .buffer_len = HTTP_RESPONSE_BUFFER_SIZE,
      .data_len = 0,
  };

  esp_http_client_config_t config = {};
  config.url = url.c_str();
  config.method = HTTP_METHOD_GET;
  config.timeout_ms = HTTP_TIMEOUT_MS;
  config.event_handler = http_event_handler;
  config.user_data = &event_data;
  config.disable_auto_redirect = false;

  esp_http_client_handle_t client = esp_http_client_init(&config);
  if (!client) {
    ESP_LOGE(TAG, "Failed to init HTTP client");
    free(response_buffer);
    return false;
  }

  // 요청 전송
  esp_err_t err = esp_http_client_perform(client);

  bool success = false;
  if (err == ESP_OK) {
    int status_code = esp_http_client_get_status_code(client);
    ESP_LOGD(TAG, "HTTP GET %s: status=%d", path.c_str(), status_code);

    if (status_code >= 200 && status_code < 300) {
      response = response_buffer;
      success = true;
    } else {
      ESP_LOGW(TAG, "HTTP error: status=%d", status_code);
    }
  } else {
    ESP_LOGE(TAG, "HTTP GET failed: %s", esp_err_to_name(err));
  }

  esp_http_client_cleanup(client);
  free(response_buffer);

  return success;
}
