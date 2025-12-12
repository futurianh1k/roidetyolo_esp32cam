#include "websocket_client.h"
#include "../config.h"
#include <cJSON.h>
#include <cstring>
#include <esp_http_client.h>
#include <esp_log.h>
#include <esp_timer.h>
#include <esp_websocket_client.h>
#include <string>

#define TAG "WebSocketClient"
#define WS_SEND_QUEUE_SIZE 10
#define WS_RECONNECT_DELAY_MS 5000

struct SendMessage {
  enum Type { Audio, Text };
  Type type;
  std::vector<uint8_t> data;
  std::string text;
};

WebSocketClient::WebSocketClient() {
  send_queue_ = xQueueCreate(WS_SEND_QUEUE_SIZE, sizeof(SendMessage *));
}

WebSocketClient::~WebSocketClient() {
  Disconnect();
  if (send_queue_) {
    SendMessage *msg = nullptr;
    while (xQueueReceive(send_queue_, &msg, 0) == pdTRUE) {
      delete msg;
    }
    vQueueDelete(send_queue_);
  }
}

static void websocket_event_handler(void *handler_args, esp_event_base_t base,
                                    int32_t event_id, void *event_data) {
  WebSocketClient *client = static_cast<WebSocketClient *>(handler_args);
  esp_websocket_event_id_t ws_event_id = (esp_websocket_event_id_t)event_id;
  esp_websocket_event_data_t *data = (esp_websocket_event_data_t *)event_data;

  switch (ws_event_id) {
  case WEBSOCKET_EVENT_CONNECTED:
    ESP_LOGI(TAG, "WebSocket connected");
    client->SetConnected(true);
    client->InvokeConnectionCallback(true);
    break;

  case WEBSOCKET_EVENT_DISCONNECTED:
    ESP_LOGI(TAG, "WebSocket disconnected");
    client->SetConnected(false);
    client->InvokeConnectionCallback(false);
    // 재연결은 ESP-IDF WebSocket 클라이언트가 자동으로 처리
    // reconnect_timeout_ms 설정에 따라 자동 재연결 시도
    break;

  case WEBSOCKET_EVENT_DATA:
    if (data->op_code == 0x08) {
      ESP_LOGI(TAG, "WebSocket closed by server");
      client->SetConnected(false);
    } else if (data->op_code == 0x01) {
      // Text frame
      std::string message((char *)data->data_ptr, data->data_len);
      client->ProcessReceivedMessage(message);
    } else if (data->op_code == 0x02) {
      // Binary frame
      ESP_LOGD(TAG, "Received binary data: %d bytes", data->data_len);
    }
    break;

  case WEBSOCKET_EVENT_ERROR:
    ESP_LOGE(TAG, "WebSocket error");
    client->SetConnected(false);
    break;

  default:
    break;
  }
}

bool WebSocketClient::Connect(const std::string &url) {
  if (connected_) {
    ESP_LOGW(TAG, "Already connected");
    return true;
  }

  url_ = url;
  return ConnectInternal();
}

bool WebSocketClient::ConnectInternal() {
  esp_websocket_client_config_t websocket_cfg = {};
  websocket_cfg.uri = url_.c_str();
  websocket_cfg.reconnect_timeout_ms = WS_RECONNECT_DELAY_MS;

  ws_handle_ = esp_websocket_client_init(&websocket_cfg);
  if (!ws_handle_) {
    ESP_LOGE(TAG, "Failed to initialize WebSocket client");
    return false;
  }

  esp_websocket_register_events(ws_handle_, WEBSOCKET_EVENT_ANY,
                                websocket_event_handler, this);

  esp_err_t ret = esp_websocket_client_start(ws_handle_);
  if (ret != ESP_OK) {
    ESP_LOGE(TAG, "Failed to start WebSocket client: %s", esp_err_to_name(ret));
    esp_websocket_client_destroy(ws_handle_);
    ws_handle_ = nullptr;
    return false;
  }

  // WebSocket 태스크 시작
  if (task_handle_ == nullptr) {
    xTaskCreate(WebSocketTask, "ws_task", 8192, this, 5, &task_handle_);
  }

  ESP_LOGI(TAG, "WebSocket connecting to: %s", url_.c_str());
  return true;
}

void WebSocketClient::Disconnect() { DisconnectInternal(); }

void WebSocketClient::DisconnectInternal() {
  if (task_handle_) {
    TaskHandle_t handle = task_handle_;
    task_handle_ = nullptr;
    vTaskDelay(pdMS_TO_TICKS(100));
    vTaskDelete(handle);
  }

  if (ws_handle_) {
    esp_websocket_client_stop(ws_handle_);
    esp_websocket_client_destroy(ws_handle_);
    ws_handle_ = nullptr;
  }

  SetConnected(false);
  InvokeConnectionCallback(false);
}

bool WebSocketClient::SendAudio(const uint8_t *data, size_t length) {
  if (!connected_ || !ws_handle_) {
    return false;
  }

  // ASR 서버는 JSON 형식으로 Base64 인코딩된 오디오를 받음
  // Base64 인코딩
  const char base64_chars[] =
      "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
  size_t base64_len = ((length + 2) / 3) * 4;
  char *base64_data = (char *)malloc(base64_len + 1);
  if (!base64_data) {
    ESP_LOGE(TAG, "Failed to allocate memory for base64 encoding");
    return false;
  }

  size_t i = 0, j = 0;
  // 3바이트씩 처리
  for (i = 0; i + 2 < length; i += 3) {
    base64_data[j++] = base64_chars[(data[i] >> 2) & 0x3F];
    base64_data[j++] =
        base64_chars[((data[i] & 0x3) << 4) | ((data[i + 1] & 0xF0) >> 4)];
    base64_data[j++] =
        base64_chars[((data[i + 1] & 0xF) << 2) | ((data[i + 2] & 0xC0) >> 6)];
    base64_data[j++] = base64_chars[data[i + 2] & 0x3F];
  }

  // 남은 바이트 처리
  if (i < length) {
    base64_data[j++] = base64_chars[(data[i] >> 2) & 0x3F];
    if (i == length - 1) {
      base64_data[j++] = base64_chars[((data[i] & 0x3) << 4)];
      base64_data[j++] = '=';
      base64_data[j++] = '=';
    } else {
      base64_data[j++] =
          base64_chars[((data[i] & 0x3) << 4) | ((data[i + 1] & 0xF0) >> 4)];
      base64_data[j++] = base64_chars[((data[i + 1] & 0xF) << 2)];
      base64_data[j++] = '=';
    }
  }
  base64_data[j] = '\0';

  // JSON 메시지 생성
  cJSON *json = cJSON_CreateObject();
  cJSON_AddStringToObject(json, "type", "audio_chunk");
  cJSON_AddStringToObject(json, "data", base64_data);
  cJSON_AddNumberToObject(json, "timestamp",
                          esp_timer_get_time() / 1000); // milliseconds

  char *json_str = cJSON_Print(json);
  esp_err_t ret = esp_websocket_client_send_text(
      ws_handle_, json_str, strlen(json_str), portMAX_DELAY);

  free(json_str);
  cJSON_Delete(json);
  free(base64_data);

  return ret == ESP_OK;
}

bool WebSocketClient::SendText(const std::string &message) {
  if (!connected_ || !ws_handle_) {
    return false;
  }

  esp_err_t ret = esp_websocket_client_send_text(
      ws_handle_, message.c_str(), message.length(), portMAX_DELAY);
  return ret == ESP_OK;
}

void WebSocketClient::SetRecognitionCallback(RecognitionCallback callback) {
  recognition_callback_ = callback;
}

void WebSocketClient::SetConnectionCallback(ConnectionCallback callback) {
  connection_callback_ = callback;
}

void WebSocketClient::InvokeConnectionCallback(bool connected) {
  if (connection_callback_) {
    connection_callback_(connected);
  }
}

void WebSocketClient::Loop() {
  // ESP-IDF WebSocket 클라이언트는 이벤트 기반이므로 별도 루프 불필요
  // 재연결은 자동으로 처리됨
}

void WebSocketClient::WebSocketTask(void *arg) {
  WebSocketClient *client = static_cast<WebSocketClient *>(arg);
  client->WebSocketTaskImpl();
}

void WebSocketClient::WebSocketTaskImpl() {
  SendMessage *msg = nullptr;

  while (connected_ || ws_handle_) {
    // 큐에서 메시지 수신
    if (xQueueReceive(send_queue_, &msg, pdMS_TO_TICKS(100)) == pdTRUE) {
      if (msg && connected_) {
        if (msg->type == SendMessage::Audio) {
          SendAudio(msg->data.data(), msg->data.size());
        } else if (msg->type == SendMessage::Text) {
          SendText(msg->text);
        }
      }
      delete msg;
      msg = nullptr;
    }
  }

  vTaskDelete(nullptr);
}

void WebSocketClient::ProcessReceivedMessage(const std::string &message) {
  ESP_LOGD(TAG, "Received message: %s", message.c_str());

  cJSON *json = cJSON_Parse(message.c_str());
  if (!json) {
    ESP_LOGW(TAG, "Failed to parse JSON message");
    return;
  }

  cJSON *type_item = cJSON_GetObjectItem(json, "type");
  if (!type_item || !cJSON_IsString(type_item)) {
    cJSON_Delete(json);
    return;
  }

  std::string type = type_item->valuestring;

  if (type == "recognition_result" || type == "partial_result") {
    cJSON *text_item = cJSON_GetObjectItem(json, "text");
    cJSON *is_final_item = cJSON_GetObjectItem(json, "is_final");
    cJSON *is_emergency_item = cJSON_GetObjectItem(json, "is_emergency");

    if (text_item && cJSON_IsString(text_item)) {
      std::string text = text_item->valuestring;
      bool is_final = is_final_item && cJSON_IsTrue(is_final_item);
      bool is_emergency = is_emergency_item && cJSON_IsTrue(is_emergency_item);

      if (recognition_callback_) {
        recognition_callback_(text, is_final, is_emergency);
      }
    }
  } else if (type == "error") {
    cJSON *error_item = cJSON_GetObjectItem(json, "error");
    if (error_item && cJSON_IsString(error_item)) {
      ESP_LOGE(TAG, "WebSocket error: %s", error_item->valuestring);
    }
  }

  cJSON_Delete(json);
}
