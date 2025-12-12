#include "application.h"
#include "asr/asr_service.h"
#include "audio/audio_codec.h"
#include "audio/audio_service.h"
#include "camera/camera_service.h"
#include "config.h"
#include "display/display_service.h"
#include "network/mqtt_client_wrapper.h"
#include "network/wifi_manager.h"
#include <algorithm>
#include <cJSON.h>
#include <cstring>
#include <driver/i2c_master.h>
#include <esp_log.h>

#define TAG "Application"

// 전역 인스턴스
static AudioCodec *audio_codec_ = nullptr;
static AudioService *audio_service_ = nullptr;
static CameraService *camera_service_ = nullptr;
static WiFiManager *wifi_manager_ = nullptr;
static MQTTClient *mqtt_client_ = nullptr;
static ASRService *asr_service_ = nullptr;
static DisplayService *display_service_ = nullptr;

Application::Application() {
  event_group_ = xEventGroupCreate();

  // Create clock timer
  esp_timer_create_args_t clock_timer_args = {
      .callback =
          [](void *arg) {
            Application *app = (Application *)arg;
            xEventGroupSetBits(app->event_group_, MAIN_EVENT_CLOCK_TICK);
          },
      .arg = this,
      .dispatch_method = ESP_TIMER_TASK,
      .name = "clock_timer",
      .skip_unhandled_events = true};
  esp_timer_create(&clock_timer_args, &clock_timer_handle_);
}

Application::~Application() {
  if (clock_timer_handle_ != nullptr) {
    esp_timer_stop(clock_timer_handle_);
    esp_timer_delete(clock_timer_handle_);
  }
  if (display_timer_handle_ != nullptr) {
    esp_timer_stop(display_timer_handle_);
    esp_timer_delete(display_timer_handle_);
  }
  if (event_group_ != nullptr) {
    vEventGroupDelete(event_group_);
  }
}

bool Application::SetDeviceState(DeviceState state) {
  return state_machine_.TransitionTo(state);
}

void Application::Initialize() {
  ESP_LOGI(TAG, "Initializing Core S3 Management System...");

  SetDeviceState(kDeviceStateStarting);

  // Add state change listener
  state_machine_.AddStateChangeListener(
      [this](DeviceState old_state, DeviceState new_state) {
        xEventGroupSetBits(event_group_, MAIN_EVENT_STATE_CHANGED);
      });

  // ==========================================================
  // STEP 1: Initialize I2C FIRST (required by audio codecs and camera)
  // M5Stack CoreS3: I2C_NUM_1, GPIO11=SCL, GPIO12=SDA
  // Reference: esp-bsp/m5stack_core_s3/m5stack_core_s3.c
  // ==========================================================
  ESP_LOGI(TAG, "STEP 1: Initializing I2C...");
  static i2c_master_bus_handle_t i2c_bus_handle = NULL;
  const i2c_master_bus_config_t i2c_bus_config = {
      .i2c_port = I2C_NUM_1,
      .sda_io_num = GPIO_NUM_12,
      .scl_io_num = GPIO_NUM_11,
      .clk_source = I2C_CLK_SRC_DEFAULT,
      .glitch_ignore_cnt = 7,
      .flags =
          {
              .enable_internal_pullup = true,
          },
  };

  esp_err_t i2c_ret = i2c_new_master_bus(&i2c_bus_config, &i2c_bus_handle);
  if (i2c_ret == ESP_OK) {
    ESP_LOGI(TAG, "I2C master bus initialized");
  } else {
    ESP_LOGW(TAG, "I2C init: %s (may be already initialized)",
             esp_err_to_name(i2c_ret));
  }

  // ==========================================================
  // STEP 2: Initialize Audio (I2S)
  // ==========================================================
  ESP_LOGI(TAG, "STEP 2: Initializing Audio...");
  audio_codec_ = new AudioCodec();
  if (audio_codec_->Initialize()) {
    ESP_LOGI(TAG, "Audio codec initialized, creating service...");
    audio_service_ = new AudioService();
    if (audio_service_->Initialize(audio_codec_)) {
      audio_service_->Start();
      ESP_LOGI(TAG, "Audio service initialized");
    } else {
      ESP_LOGW(TAG, "Audio service init failed");
    }
  } else {
    ESP_LOGW(TAG, "Audio codec initialization failed, continuing...");
  }

  // ==========================================================
  // STEP 3: Initialize Camera (requires I2C to be ready)
  // ==========================================================
  ESP_LOGI(TAG, "STEP 3: Initializing Camera...");
  camera_service_ = new CameraService();
  if (camera_service_->Initialize()) {
    camera_service_->Start();
    ESP_LOGI(TAG, "Camera service initialized");
  } else {
    ESP_LOGW(TAG, "Camera initialization failed, continuing...");
  }

  // Initialize WiFi
  wifi_manager_ = &WiFiManager::GetInstance();
  wifi_manager_->SetEventCallback(
      [this](NetworkEvent event, const std::string &data) {
        if (event == NetworkEvent::Connected) {
          xEventGroupSetBits(event_group_, MAIN_EVENT_NETWORK_CONNECTED);
        } else if (event == NetworkEvent::Disconnected) {
          xEventGroupSetBits(event_group_, MAIN_EVENT_NETWORK_DISCONNECTED);
        }
      });

  if (wifi_manager_->Initialize(WIFI_SSID, WIFI_PASSWORD)) {
    wifi_manager_->Start();
    ESP_LOGI(TAG, "WiFi manager initialized");
  }

  // Initialize Display
  display_service_ = new DisplayService();
  if (display_service_->Initialize()) {
    ESP_LOGI(TAG, "Display service initialized");
  }

  // Initialize ASR Service
  if (audio_service_) {
    asr_service_ = new ASRService();
    if (asr_service_->Initialize(audio_service_)) {
      // 인식 결과 콜백 설정
      asr_service_->SetRecognitionCallback(
          [this](const std::string &text, bool is_final, bool is_emergency) {
            // 음성인식 결과를 디스플레이에 표시
            if (display_service_ && is_final && !text.empty()) {
              std::string display_text = text;
              if (is_emergency) {
                display_text = "🚨 " + text;
              }
              // 최종 결과는 10초간 표시
              display_service_->ShowText(display_text, 10000);
            }

            // 부분 결과도 디스플레이에 표시 (짧게)
            if (display_service_ && !is_final && !text.empty()) {
              display_service_->ShowText(text, 1000); // 1초간 표시
            }

            ESP_LOGI(TAG, "Recognition result: %s (final=%d, emergency=%d)",
                     text.c_str(), is_final, is_emergency);
          });
      ESP_LOGI(TAG, "ASR service initialized");
    }
  }

  // Initialize MQTT (after WiFi connected)
  mqtt_client_ = new MQTTClient();
  mqtt_client_->Initialize(MQTT_BROKER, MQTT_PORT, MQTT_USERNAME,
                           MQTT_PASSWORD);

  // MQTT 연결 콜백 설정 (연결 후 자동 구독)
  mqtt_client_->SetConnectionCallback([this](bool connected) {
    if (connected) {
      ESP_LOGI(TAG, "MQTT connected, subscribing to topics...");
      // 토픽 구독
      mqtt_client_->Subscribe(TOPIC_CONTROL_CAMERA, MQTT_QOS);
      mqtt_client_->Subscribe(TOPIC_CONTROL_MICROPHONE, MQTT_QOS);
      mqtt_client_->Subscribe(TOPIC_CONTROL_SPEAKER, MQTT_QOS);
      mqtt_client_->Subscribe(TOPIC_CONTROL_DISPLAY, MQTT_QOS);
      mqtt_client_->Subscribe(TOPIC_CONTROL_SYSTEM, MQTT_QOS);
      mqtt_client_->Subscribe(TOPIC_COMMAND, MQTT_QOS); // 통합 명령 토픽
      ESP_LOGI(TAG, "MQTT topics subscribed");
    }
  });

  mqtt_client_->SetMessageCallback([](const std::string &topic,
                                      const std::string &payload) {
    ESP_LOGI(TAG, "MQTT message: %s -> %s", topic.c_str(), payload.c_str());

    // MQTT 메시지 처리
    cJSON *json = cJSON_Parse(payload.c_str());
    if (!json) {
      ESP_LOGW(TAG, "Failed to parse MQTT payload as JSON");
      return;
    }

    // devices/{device_id}/command 토픽 처리 (통합 명령)
    if (topic.find("/command") != std::string::npos) {
      cJSON *command_item = cJSON_GetObjectItem(json, "command");
      cJSON *action_item = cJSON_GetObjectItem(json, "action");

      if (command_item && cJSON_IsString(command_item) && action_item &&
          cJSON_IsString(action_item)) {
        std::string command = command_item->valuestring;
        std::string action = action_item->valuestring;

        if (command == "start_asr" && asr_service_) {
          cJSON *language_item = cJSON_GetObjectItem(json, "language");
          std::string language = "ko";
          if (language_item && cJSON_IsString(language_item)) {
            language = language_item->valuestring;
          }

          if (asr_service_->StartSession(language)) {
            if (display_service_) {
              display_service_->ShowListening(true);
            }
            Application::GetInstance().SetDeviceState(kDeviceStateListening);
          }
        } else if (command == "stop_asr" && asr_service_) {
          asr_service_->StopSession();
          if (display_service_) {
            display_service_->ShowListening(false);
          }
          Application::GetInstance().SetDeviceState(kDeviceStateIdle);
        }
      }
    }

    // devices/{device_id}/control/microphone 토픽 처리
    if (topic.find("/control/microphone") != std::string::npos) {
      cJSON *action_item = cJSON_GetObjectItem(json, "action");

      if (action_item && cJSON_IsString(action_item) && asr_service_) {
        std::string action = action_item->valuestring;

        if (action == "start_asr") {
          cJSON *language_item = cJSON_GetObjectItem(json, "language");
          cJSON *ws_url_item = cJSON_GetObjectItem(json, "ws_url");
          std::string language = "ko";
          std::string ws_url = "";

          if (language_item && cJSON_IsString(language_item)) {
            language = language_item->valuestring;
          }

          // ws_url이 제공되면 사용
          if (ws_url_item && cJSON_IsString(ws_url_item)) {
            ws_url = ws_url_item->valuestring;
            ESP_LOGI(TAG, "Using provided ws_url: %s", ws_url.c_str());
          }

          if (asr_service_->StartSession(language, ws_url)) {
            if (display_service_) {
              display_service_->ShowListening(true);
            }
            Application::GetInstance().SetDeviceState(kDeviceStateListening);
          }
        } else if (action == "stop_asr") {
          asr_service_->StopSession();
          if (display_service_) {
            display_service_->ShowListening(false);
          }
          Application::GetInstance().SetDeviceState(kDeviceStateIdle);
        }
      }
    }

    // devices/{device_id}/control/display 토픽 처리
    if (topic.find("/control/display") != std::string::npos) {
      cJSON *action_item = cJSON_GetObjectItem(json, "action");
      cJSON *text_item = cJSON_GetObjectItem(json, "text");

      if (action_item && cJSON_IsString(action_item) && display_service_) {
        std::string action = action_item->valuestring;

        if (action == "show_text" && text_item && cJSON_IsString(text_item)) {
          std::string text = text_item->valuestring;
          display_service_->ShowText(text, 0); // 무한 표시
        } else if (action == "clear") {
          display_service_->Clear();
        }
      }
    }

    cJSON_Delete(json);
  });

  // Start clock timer (1 second interval)
  esp_timer_start_periodic(clock_timer_handle_, 1000000);

  // Start display animation timer (500ms interval for listening animation)
  esp_timer_create_args_t display_timer_args = {
      .callback =
          [](void *arg) {
            (void)arg; // unused
            if (display_service_) {
              display_service_->UpdateListeningAnimation();
            }
          },
      .arg = this,
      .dispatch_method = ESP_TIMER_TASK,
      .name = "display_animation_timer",
      .skip_unhandled_events = true};
  esp_timer_create(&display_timer_args, &display_timer_handle_);
  esp_timer_start_periodic(display_timer_handle_, 500000); // 500ms

  SetDeviceState(kDeviceStateIdle);

  ESP_LOGI(TAG, "Initialization complete");
}

void Application::Run() {
  const EventBits_t ALL_EVENTS =
      MAIN_EVENT_SCHEDULE | MAIN_EVENT_NETWORK_CONNECTED |
      MAIN_EVENT_NETWORK_DISCONNECTED | MAIN_EVENT_STATE_CHANGED |
      MAIN_EVENT_ERROR | MAIN_EVENT_CLOCK_TICK;

  ESP_LOGI(TAG, "Main event loop started");

  while (true) {
    auto bits = xEventGroupWaitBits(event_group_, ALL_EVENTS,
                                    pdTRUE,  // Clear bits on exit
                                    pdFALSE, // Wait for any bit
                                    portMAX_DELAY);

    if (bits & MAIN_EVENT_ERROR) {
      HandleErrorEvent();
    }

    if (bits & MAIN_EVENT_NETWORK_CONNECTED) {
      HandleNetworkConnectedEvent();
    }

    if (bits & MAIN_EVENT_NETWORK_DISCONNECTED) {
      HandleNetworkDisconnectedEvent();
    }

    if (bits & MAIN_EVENT_STATE_CHANGED) {
      HandleStateChangedEvent();
    }

    // Process scheduled tasks
    if (bits & MAIN_EVENT_SCHEDULE) {
      std::deque<std::function<void()>> tasks;
      {
        std::lock_guard<std::mutex> lock(mutex_);
        tasks = std::move(main_tasks_);
      }

      for (auto &task : tasks) {
        // ESP-IDF는 기본적으로 C++ 예외를 비활성화하므로 try-catch 사용 불가
        // 대신 task 함수 내부에서 오류 처리를 수행해야 함
        task();
      }
    }

    // MQTT loop
    if (mqtt_client_) {
      mqtt_client_->Loop();
    }
  }
}

void Application::Schedule(std::function<void()> callback) {
  std::lock_guard<std::mutex> lock(mutex_);
  main_tasks_.push_back(callback);
  xEventGroupSetBits(event_group_, MAIN_EVENT_SCHEDULE);
}

void Application::HandleStateChangedEvent() {
  DeviceState state = state_machine_.GetState();
  ESP_LOGD(TAG, "State changed to: %d", state);

  // 상태에 따른 디스플레이 업데이트
  if (display_service_) {
    switch (state) {
    case kDeviceStateListening:
      display_service_->ShowListening(true);
      break;
    case kDeviceStateProcessing:
      display_service_->ShowText("처리 중...", 0);
      break;
    case kDeviceStateIdle:
      display_service_->ShowListening(false);
      break;
    default:
      break;
    }
  }
}

void Application::HandleNetworkConnectedEvent() {
  ESP_LOGI(TAG, "Network connected");
  SetDeviceState(kDeviceStateConnected);

  // MQTT 연결
  if (mqtt_client_) {
    std::string client_id = MQTT_CLIENT_ID_PREFIX + std::string(DEVICE_ID);
    if (mqtt_client_->Connect(client_id)) {
      ESP_LOGI(TAG, "MQTT connection initiated");
      // 토픽 구독은 MQTT 연결 콜백에서 자동으로 처리됨
    } else {
      ESP_LOGW(TAG, "MQTT connection failed, will retry");
    }
  }
}

void Application::HandleNetworkDisconnectedEvent() {
  ESP_LOGI(TAG, "Network disconnected");
  SetDeviceState(kDeviceStateConnecting);
}

void Application::HandleErrorEvent() {
  ESP_LOGE(TAG, "Error event: %s", last_error_message_.c_str());
  SetDeviceState(kDeviceStateError);
}

void Application::OnStateChanged(DeviceState old_state, DeviceState new_state) {
  ESP_LOGI(TAG, "State changed: %d -> %d", old_state, new_state);
}
