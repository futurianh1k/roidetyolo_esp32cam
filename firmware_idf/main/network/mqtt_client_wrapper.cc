#include <cstring>
#include <esp_err.h>
#include <esp_log.h>
#include <string>

// Include our wrapper header (which includes ESP-IDF's mqtt_client.h)
#include "mqtt_client_wrapper.h"

#define TAG "MQTTClient"

MQTTClient::MQTTClient() {}

MQTTClient::~MQTTClient() {
  Disconnect();
  if (mqtt_client_) {
    esp_mqtt_client_destroy((esp_mqtt_client_handle_t)mqtt_client_);
    mqtt_client_ = nullptr;
  }
}

bool MQTTClient::Initialize(const std::string &broker, int port,
                            const std::string &username,
                            const std::string &password) {
  broker_ = broker;
  port_ = port;
  username_ = username;
  password_ = password;

  // MQTT URI 구성
  std::string uri = "mqtt://" + broker + ":" + std::to_string(port);

  esp_mqtt_client_config_t mqtt_cfg = {};
  mqtt_cfg.broker.address.uri = uri.c_str();

  if (!username_.empty()) {
    mqtt_cfg.credentials.username = username_.c_str();
    mqtt_cfg.credentials.authentication.password = password_.c_str();
  }

  mqtt_client_ = esp_mqtt_client_init(&mqtt_cfg);
  if (!mqtt_client_) {
    ESP_LOGE(TAG, "Failed to initialize MQTT client");
    return false;
  }

  // 이벤트 핸들러 등록
  esp_mqtt_client_register_event((esp_mqtt_client_handle_t)mqtt_client_,
                                 MQTT_EVENT_ANY, MQTTEventHandler, this);

  ESP_LOGI(TAG, "MQTT client initialized: %s", uri.c_str());
  return true;
}

bool MQTTClient::Connect(const std::string &client_id) {
  if (!mqtt_client_) {
    ESP_LOGE(TAG, "MQTT client not initialized");
    return false;
  }

  // Note: client_id는 현재 사용되지 않음 (Initialize에서 설정)
  (void)client_id; // unused

  esp_err_t ret = esp_mqtt_client_start((esp_mqtt_client_handle_t)mqtt_client_);
  if (ret != ESP_OK) {
    ESP_LOGE(TAG, "Failed to start MQTT client: %s", esp_err_to_name(ret));
    return false;
  }

  ESP_LOGI(TAG, "MQTT client connecting...");
  return true;
}

void MQTTClient::Disconnect() {
  if (mqtt_client_ && connected_) {
    esp_mqtt_client_stop((esp_mqtt_client_handle_t)mqtt_client_);
    connected_ = false;
  }
}

bool MQTTClient::IsConnected() const { return connected_; }

bool MQTTClient::Publish(const std::string &topic, const std::string &payload,
                         int qos) {
  if (!mqtt_client_ || !connected_) {
    return false;
  }

  int msg_id = esp_mqtt_client_publish((esp_mqtt_client_handle_t)mqtt_client_,
                                       topic.c_str(), payload.c_str(),
                                       payload.length(), qos, 0);
  return msg_id >= 0;
}

bool MQTTClient::Subscribe(const std::string &topic, int qos) {
  if (!mqtt_client_ || !connected_) {
    return false;
  }

  int msg_id = esp_mqtt_client_subscribe((esp_mqtt_client_handle_t)mqtt_client_,
                                         topic.c_str(), qos);
  return msg_id >= 0;
}

void MQTTClient::SetMessageCallback(MessageCallback callback) {
  message_callback_ = callback;
}

void MQTTClient::SetConnectionCallback(ConnectionCallback callback) {
  connection_callback_ = callback;
}

void MQTTClient::Loop() {
  // ESP-IDF MQTT 클라이언트는 이벤트 기반이므로 별도 루프 불필요
}

void MQTTClient::MQTTEventHandler(void *handler_args, esp_event_base_t base,
                                  int32_t event_id, void *event_data) {
  MQTTClient *client = static_cast<MQTTClient *>(handler_args);
  esp_mqtt_event_handle_t event = (esp_mqtt_event_handle_t)event_data;

  switch (event->event_id) {
  case MQTT_EVENT_CONNECTED:
    ESP_LOGI(TAG, "MQTT connected");
    client->connected_ = true;
    if (client->connection_callback_) {
      client->connection_callback_(true);
    }
    break;

  case MQTT_EVENT_DISCONNECTED:
    ESP_LOGI(TAG, "MQTT disconnected");
    client->connected_ = false;
    if (client->connection_callback_) {
      client->connection_callback_(false);
    }
    break;

  case MQTT_EVENT_DATA:
    if (client->message_callback_) {
      std::string topic(event->topic, event->topic_len);
      std::string payload(event->data, event->data_len);
      client->message_callback_(topic, payload);
    }
    break;

  case MQTT_EVENT_ERROR:
    if (event->error_handle) {
      if (event->error_handle->error_type == MQTT_ERROR_TYPE_ESP_TLS) {
        ESP_LOGE(TAG, "MQTT TLS error: %s",
                 esp_err_to_name(event->error_handle->esp_tls_last_esp_err));
      } else {
        ESP_LOGE(TAG, "MQTT error occurred");
      }
    }
    break;

  default:
    break;
  }
}
