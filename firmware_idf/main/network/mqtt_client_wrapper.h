#ifndef MQTT_CLIENT_WRAPPER_H
#define MQTT_CLIENT_WRAPPER_H

#include "esp_event.h"
#include <functional>
#include <memory>
#include <mqtt_client.h> // ESP-IDF MQTT client header
#include <string>

class MQTTClient {
public:
  MQTTClient();
  ~MQTTClient();

  bool Initialize(const std::string &broker, int port,
                  const std::string &username = "",
                  const std::string &password = "");
  bool Connect(const std::string &client_id);
  void Disconnect();
  bool IsConnected() const;

  bool Publish(const std::string &topic, const std::string &payload,
               int qos = 1);
  bool Subscribe(const std::string &topic, int qos = 1);

  using MessageCallback =
      std::function<void(const std::string &topic, const std::string &payload)>;
  void SetMessageCallback(MessageCallback callback);

  using ConnectionCallback = std::function<void(bool connected)>;
  void SetConnectionCallback(ConnectionCallback callback);

  void Loop();

private:
  void *mqtt_client_ = nullptr; // mqtt_client_handle_t
  std::string broker_;
  int port_ = 1883;
  std::string username_;
  std::string password_;
  bool connected_ = false;
  MessageCallback message_callback_;
  ConnectionCallback connection_callback_;

  static void MQTTEventHandler(void *handler_args, esp_event_base_t base,
                               int32_t event_id, void *event_data);
};

#endif // MQTT_CLIENT_WRAPPER_H
