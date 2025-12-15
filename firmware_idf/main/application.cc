#include "application.h"
#include "asr/asr_service.h"
#include "audio/audio_codec.h"
#include "audio/audio_service.h"
#include "audio/wav_player.h"
#include "camera/camera_service.h"
#include "camera/camera_stream_server.h"
#include "camera/rtsp_server.h"
#include "config.h"
#include "display/display_service.h"
#include "input/button_service.h"
#include "network/backend_client.h"
#include "network/mqtt_client_wrapper.h"
#include "network/wifi_manager.h"
#include "power/power_manager.h"
#include "status/status_reporter.h"
#include <algorithm>
#include <cJSON.h>
#include <cstring>
#include <esp_log.h>
#include <esp_system.h>
#include <nvs.h>
#include <nvs_flash.h>
#include <string>

#define TAG "Application"

// NVS namespace and key for device DB ID
#define NVS_NAMESPACE "device_cfg"
#define NVS_KEY_DEVICE_DB_ID "device_db_id"

// 동적으로 로드된 Device DB ID (런타임에 설정됨)
static int device_db_id_ = 0;

// NVS에서 device_db_id 로드
static bool LoadDeviceDbIdFromNVS(int &out_id) {
  nvs_handle_t handle;
  esp_err_t err = nvs_open(NVS_NAMESPACE, NVS_READONLY, &handle);
  if (err != ESP_OK) {
    ESP_LOGW(TAG, "NVS namespace not found: %s", esp_err_to_name(err));
    return false;
  }

  int32_t stored_id = 0;
  err = nvs_get_i32(handle, NVS_KEY_DEVICE_DB_ID, &stored_id);
  nvs_close(handle);

  if (err == ESP_OK && stored_id > 0) {
    out_id = stored_id;
    ESP_LOGI(TAG, "Loaded device_db_id from NVS: %d", out_id);
    return true;
  }

  ESP_LOGW(TAG, "device_db_id not found in NVS");
  return false;
}

// NVS에 device_db_id 저장
static bool SaveDeviceDbIdToNVS(int id) {
  nvs_handle_t handle;
  esp_err_t err = nvs_open(NVS_NAMESPACE, NVS_READWRITE, &handle);
  if (err != ESP_OK) {
    ESP_LOGE(TAG, "Failed to open NVS namespace: %s", esp_err_to_name(err));
    return false;
  }

  err = nvs_set_i32(handle, NVS_KEY_DEVICE_DB_ID, id);
  if (err == ESP_OK) {
    err = nvs_commit(handle);
  }
  nvs_close(handle);

  if (err == ESP_OK) {
    ESP_LOGI(TAG, "Saved device_db_id to NVS: %d", id);
    return true;
  }

  ESP_LOGE(TAG, "Failed to save device_db_id to NVS: %s", esp_err_to_name(err));
  return false;
}

// 백엔드에서 device_id로 DB ID를 조회하여 설정
static bool ResolveDeviceDbId() {
  // 1. NVS에서 먼저 확인
  if (LoadDeviceDbIdFromNVS(device_db_id_)) {
    return true;
  }

  // 2. 백엔드에서 조회
  ESP_LOGI(TAG, "Looking up device_db_id from backend for: %s", DEVICE_ID);

  BackendClient lookup_client;
  std::string backend_url = "http://" + std::string(BACKEND_HOST) + ":" +
                            std::to_string(BACKEND_PORT);

  // 임시로 device_id=1로 초기화 (LookupDeviceDbId만 사용하므로 무관)
  lookup_client.Initialize(backend_url, 1);

  int db_id = 0;
  if (lookup_client.LookupDeviceDbId(DEVICE_ID, db_id)) {
    device_db_id_ = db_id;
    // NVS에 저장
    SaveDeviceDbIdToNVS(device_db_id_);
    ESP_LOGI(TAG, "Resolved device_db_id: %s -> %d", DEVICE_ID, device_db_id_);
    return true;
  }

  ESP_LOGE(TAG, "Failed to resolve device_db_id for: %s", DEVICE_ID);
  return false;
}

// 전역 인스턴스
static PowerManager *power_manager_ = nullptr;
static AudioCodec *audio_codec_ = nullptr;
static AudioService *audio_service_ = nullptr;
static CameraService *camera_service_ = nullptr;
static CameraStreamServer *camera_stream_server_ = nullptr;
static RTSPServer *rtsp_server_ = nullptr;
static WiFiManager *wifi_manager_ = nullptr;
static MQTTClient *mqtt_client_ = nullptr;
static ASRService *asr_service_ = nullptr;
static DisplayService *display_service_ = nullptr;
static StatusReporter *status_reporter_ = nullptr;
static ButtonService *button_service_ = nullptr;
static WavPlayer *wav_player_ = nullptr;

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
  // STEP 1: Initialize Power Management (AXP2101 + AW9523)
  // Reference: power/power_manager.cc
  // ==========================================================
  ESP_LOGI(TAG, "STEP 1: Initializing power management...");
  power_manager_ = new PowerManager();
  if (power_manager_->Initialize()) {
    // Enable Camera and Display power
    power_manager_->EnableFeature(PowerFeature::kCamera);
    power_manager_->EnableFeature(PowerFeature::kDisplay);
    ESP_LOGI(TAG, "Power management initialized");
  } else {
    ESP_LOGW(TAG, "Power management initialization failed, continuing...");
  }

  // Power stabilization delay
  vTaskDelay(pdMS_TO_TICKS(100));

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

    // WAV 플레이어 초기화
    wav_player_ = new WavPlayer();
    if (wav_player_->Initialize(audio_codec_)) {
      ESP_LOGI(TAG, "WAV player initialized");
    } else {
      ESP_LOGW(TAG, "WAV player init failed");
    }
  } else {
    ESP_LOGW(TAG, "Audio codec initialization failed, continuing...");
  }

  // ==========================================================
  // STEP 3: Initialize Camera (power already enabled via AW9523)
  // ==========================================================
  ESP_LOGI(TAG, "STEP 3: Initializing Camera...");
  camera_service_ = new CameraService();
  if (camera_service_->Initialize()) {
    camera_service_->Start();
    ESP_LOGI(TAG, "Camera service initialized");
    // Note: Camera Stream Servers will be started after WiFi connection
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

  // Status Reporter는 네트워크 연결 후 device_db_id 조회 후 초기화됨
  // (HandleNetworkConnectedEvent에서 처리)
  status_reporter_ = new StatusReporter();
  ESP_LOGI(
      TAG,
      "Status reporter created (will initialize after network connection)");

  // Initialize Button Service (버튼 입력 처리)
  button_service_ = new ButtonService();
  if (button_service_->Initialize()) {
    // 버튼 이벤트 콜백 설정
    button_service_->SetButtonCallback(
        [this](ButtonId button, ButtonEvent event) {
          HandleButtonEvent(button, event);
        });
    button_service_->Start();
    ESP_LOGI(TAG, "Button service initialized");
  } else {
    ESP_LOGW(TAG, "Button service initialization failed");
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
            if (status_reporter_) {
              status_reporter_->SetMicStatus("active");
            }
            Application::GetInstance().SetDeviceState(kDeviceStateListening);
          }
        } else if (command == "stop_asr" && asr_service_) {
          asr_service_->StopSession();
          if (display_service_) {
            display_service_->ShowListening(false);
          }
          if (status_reporter_) {
            status_reporter_->SetMicStatus("stopped");
          }
          Application::GetInstance().SetDeviceState(kDeviceStateIdle);
        }
      }
    }

    // devices/{device_id}/control/camera 토픽 처리
    if (topic.find("/control/camera") != std::string::npos) {
      cJSON *action_item = cJSON_GetObjectItem(json, "action");

      if (action_item && cJSON_IsString(action_item) && camera_service_) {
        std::string action = action_item->valuestring;

        if (action == "start") {
          // sink_url, stream_mode, frame_interval 파싱
          cJSON *sink_url_item = cJSON_GetObjectItem(json, "sink_url");
          cJSON *stream_mode_item = cJSON_GetObjectItem(json, "stream_mode");
          cJSON *frame_interval_item =
              cJSON_GetObjectItem(json, "frame_interval");

          std::string sink_url = "";
          std::string stream_mode = "mjpeg_stills";
          int frame_interval_ms = 1000;

          if (sink_url_item && cJSON_IsString(sink_url_item)) {
            sink_url = sink_url_item->valuestring;
          }
          if (stream_mode_item && cJSON_IsString(stream_mode_item)) {
            stream_mode = stream_mode_item->valuestring;
          }
          if (frame_interval_item && cJSON_IsNumber(frame_interval_item)) {
            frame_interval_ms = frame_interval_item->valueint;
          }

          // sink_url이 있으면 스트림 전송 모드로 시작
          if (!sink_url.empty()) {
            camera_service_->StartStream(sink_url, stream_mode,
                                         frame_interval_ms);
            ESP_LOGI(TAG,
                     "Camera stream started -> %s (mode: %s, interval: %dms)",
                     sink_url.c_str(), stream_mode.c_str(), frame_interval_ms);
          } else {
            camera_service_->Start();
            ESP_LOGI(TAG, "Camera started (local mode)");
          }

          if (status_reporter_) {
            status_reporter_->SetCameraStatus("active");
          }
        } else if (action == "stop") {
          camera_service_->Stop();
          if (status_reporter_) {
            status_reporter_->SetCameraStatus("stopped");
          }
          ESP_LOGI(TAG, "Camera stopped");
        } else if (action == "pause") {
          camera_service_->Stop(); // 일시정지는 정지와 동일하게 처리
          if (status_reporter_) {
            status_reporter_->SetCameraStatus("paused");
          }
          ESP_LOGI(TAG, "Camera paused");
        }
      }
    }

    // devices/{device_id}/control/microphone 토픽 처리
    if (topic.find("/control/microphone") != std::string::npos) {
      cJSON *action_item = cJSON_GetObjectItem(json, "action");

      if (action_item && cJSON_IsString(action_item)) {
        std::string action = action_item->valuestring;

        if (action == "start" || action == "start_asr") {
          if (asr_service_) {
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
              if (status_reporter_) {
                status_reporter_->SetMicStatus("active");
              }
              Application::GetInstance().SetDeviceState(kDeviceStateListening);
            }
          }
        } else if (action == "stop" || action == "stop_asr") {
          if (asr_service_) {
            asr_service_->StopSession();
          }
          if (display_service_) {
            display_service_->ShowListening(false);
          }
          if (status_reporter_) {
            status_reporter_->SetMicStatus("stopped");
          }
          Application::GetInstance().SetDeviceState(kDeviceStateIdle);
        } else if (action == "pause") {
          // 일시정지 처리
          if (status_reporter_) {
            status_reporter_->SetMicStatus("paused");
          }
        }
      }
    }

    // devices/{device_id}/control/speaker 토픽 처리
    if (topic.find("/control/speaker") != std::string::npos) {
      cJSON *action_item = cJSON_GetObjectItem(json, "action");

      if (action_item && cJSON_IsString(action_item)) {
        std::string action = action_item->valuestring;

        if (action == "play_alarm" && wav_player_) {
          // 알람음 재생: {"action": "play_alarm", "type":
          // "beep|alert|notification|emergency", "repeat": 1}
          cJSON *type_item = cJSON_GetObjectItem(json, "type");
          cJSON *repeat_item = cJSON_GetObjectItem(json, "repeat");

          AlarmType alarm_type = AlarmType::kBeep;
          int repeat = 1;

          if (type_item && cJSON_IsString(type_item)) {
            std::string type_str = type_item->valuestring;
            if (type_str == "alert") {
              alarm_type = AlarmType::kAlert;
            } else if (type_str == "notification") {
              alarm_type = AlarmType::kNotification;
            } else if (type_str == "emergency") {
              alarm_type = AlarmType::kEmergency;
            }
          }

          if (repeat_item && cJSON_IsNumber(repeat_item)) {
            repeat = repeat_item->valueint;
            if (repeat < 1)
              repeat = 1;
            if (repeat > 10)
              repeat = 10;
          }

          ESP_LOGI(TAG, "Playing alarm: type=%d, repeat=%d",
                   static_cast<int>(alarm_type), repeat);
          wav_player_->PlayAlarm(alarm_type, repeat);

        } else if (action == "play_beep" && wav_player_) {
          // 비프음 재생: {"action": "play_beep", "frequency": 1000, "duration":
          // 200, "volume": 80}
          cJSON *freq_item = cJSON_GetObjectItem(json, "frequency");
          cJSON *duration_item = cJSON_GetObjectItem(json, "duration");
          cJSON *volume_item = cJSON_GetObjectItem(json, "volume");

          int frequency = 1000;
          int duration = 200;
          int volume = 80;

          if (freq_item && cJSON_IsNumber(freq_item)) {
            frequency = freq_item->valueint;
          }
          if (duration_item && cJSON_IsNumber(duration_item)) {
            duration = duration_item->valueint;
          }
          if (volume_item && cJSON_IsNumber(volume_item)) {
            volume = volume_item->valueint;
          }

          ESP_LOGI(TAG, "Playing beep: freq=%d, dur=%d, vol=%d", frequency,
                   duration, volume);
          wav_player_->PlayBeep(frequency, duration, volume);

        } else if (action == "play" && audio_service_) {
          cJSON *audio_file_item = cJSON_GetObjectItem(json, "audio_file");
          cJSON *volume_item = cJSON_GetObjectItem(json, "volume");

          if (audio_file_item && cJSON_IsString(audio_file_item)) {
            std::string audio_file = audio_file_item->valuestring;

            // 볼륨 설정 (옵션)
            if (volume_item && cJSON_IsNumber(volume_item)) {
              int volume = volume_item->valueint;
              audio_service_->SetVolume(volume);
            }

            // SPIFFS에서 WAV 파일 재생
            if (wav_player_ && audio_file.find(".wav") != std::string::npos) {
              std::string spiffs_path = "/spiffs/" + audio_file;
              ESP_LOGI(TAG, "Playing WAV file: %s", spiffs_path.c_str());
              wav_player_->PlayFile(spiffs_path);
            } else {
              ESP_LOGI(TAG, "Speaker play: %s (not implemented)",
                       audio_file.c_str());
            }
          }
        } else if (action == "stop") {
          if (wav_player_) {
            wav_player_->Stop();
          }
          if (audio_service_) {
            audio_service_->Stop();
          }
          ESP_LOGI(TAG, "Speaker stopped");
        }
      }
    }

    // devices/{device_id}/control/display 토픽 처리
    if (topic.find("/control/display") != std::string::npos) {
      cJSON *action_item = cJSON_GetObjectItem(json, "action");

      if (action_item && cJSON_IsString(action_item) && display_service_) {
        std::string action = action_item->valuestring;

        if (action == "show_text") {
          cJSON *text_item = cJSON_GetObjectItem(json, "text");
          if (text_item && cJSON_IsString(text_item)) {
            std::string text = text_item->valuestring;
            display_service_->ShowText(text, 0); // 무한 표시
            ESP_LOGI(TAG, "Display text: %s", text.c_str());
          }
        } else if (action == "show_emoji") {
          cJSON *emoji_item = cJSON_GetObjectItem(json, "emoji_id");
          if (emoji_item && cJSON_IsString(emoji_item)) {
            std::string emoji = emoji_item->valuestring;
            display_service_->ShowText(emoji, 0);
            ESP_LOGI(TAG, "Display emoji: %s", emoji.c_str());
          }
        } else if (action == "clear") {
          display_service_->Clear();
          ESP_LOGI(TAG, "Display cleared");
        }
      }
    }

    // devices/{device_id}/control/system 토픽 처리
    if (topic.find("/control/system") != std::string::npos) {
      cJSON *action_item = cJSON_GetObjectItem(json, "action");

      if (action_item && cJSON_IsString(action_item)) {
        std::string action = action_item->valuestring;

        if (action == "restart") {
          ESP_LOGI(TAG, "System restart requested via MQTT");
          if (display_service_) {
            display_service_->ShowText("Restarting...", 2000);
          }
          // 2초 후 재시작
          vTaskDelay(pdMS_TO_TICKS(2000));
          esp_restart();
        } else if (action == "wake") {
          // Wake 명령: 즉시 상태 보고하여 온라인 상태로 전환
          ESP_LOGI(TAG, "Wake command received via MQTT");
          if (display_service_) {
            display_service_->ShowText("Waking up...", 2000);
          }
          // 즉시 상태 보고
          if (status_reporter_) {
            status_reporter_->ReportNow();
            ESP_LOGI(TAG, "Status reported - device is now online");
          }
        } else if (action == "sleep") {
          // Sleep 명령: Light Sleep 모드 진입
          ESP_LOGI(TAG, "Sleep command received via MQTT");
          if (display_service_) {
            display_service_->ShowText("Sleeping...", 1000);
          }
          vTaskDelay(pdMS_TO_TICKS(1000));

          // Light Sleep 진입 (5분 후 자동 깨우기)
          if (power_manager_) {
            power_manager_->EnterLightSleep(LIGHT_SLEEP_DURATION_MS);

            // 깨어난 후 즉시 상태 보고
            ESP_LOGI(TAG, "Woke up from Light Sleep");
            if (display_service_) {
              display_service_->ShowText("Woke up!", 2000);
            }
            if (status_reporter_) {
              status_reporter_->ReportNow();
            }
          } else {
            ESP_LOGW(TAG, "Power manager not available for sleep");
          }
        } else if (action == "set_interval") {
          // 상태 보고 주기 변경: {"action": "set_interval", "interval": 60}
          cJSON *interval_item = cJSON_GetObjectItem(json, "interval");
          if (interval_item && cJSON_IsNumber(interval_item)) {
            int interval_sec = interval_item->valueint;
            uint32_t interval_ms = interval_sec * 1000;

            ESP_LOGI(TAG, "Set interval command: %d seconds", interval_sec);

            if (status_reporter_) {
              if (status_reporter_->SetInterval(interval_ms)) {
                if (display_service_) {
                  char msg[32];
                  snprintf(msg, sizeof(msg), "Interval: %ds", interval_sec);
                  display_service_->ShowText(msg, 2000);
                }
              }
            }
          } else {
            ESP_LOGW(TAG, "set_interval: missing interval parameter");
          }
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

  // Device DB ID 조회 (NVS 또는 백엔드에서)
  if (device_db_id_ == 0) {
    if (ResolveDeviceDbId()) {
      ESP_LOGI(TAG, "Device DB ID resolved: %d", device_db_id_);
    } else {
      ESP_LOGE(TAG,
               "Failed to resolve Device DB ID - status reporting disabled");
    }
  }

  // Status Reporter 초기화 및 시작
  if (status_reporter_ && device_db_id_ > 0) {
    std::string backend_url = "http://" + std::string(BACKEND_HOST) + ":" +
                              std::to_string(BACKEND_PORT);
    if (status_reporter_->Initialize(backend_url, device_db_id_,
                                     STATUS_REPORT_INTERVAL_MS)) {
      status_reporter_->Start();
      ESP_LOGI(TAG, "Status reporter initialized and started (device_db_id=%d)",
               device_db_id_);
    } else {
      ESP_LOGW(TAG, "Status reporter initialization failed");
    }
  }

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

  // ==========================================================
  // Camera Stream Servers 시작 (WiFi 연결 후)
  // ==========================================================
  if (camera_service_) {
    ESP_LOGI(TAG, "Starting Camera Stream Servers...");

    // HTTP MJPEG 스트리밍 서버 (포트 81)
    if (!camera_stream_server_) {
      camera_stream_server_ = new CameraStreamServer(camera_service_);
    }
    if (!camera_stream_server_->IsHTTPRunning()) {
      if (camera_stream_server_->Start()) {
        ESP_LOGI(TAG, "HTTP MJPEG stream server started on port 81");
      } else {
        ESP_LOGW(TAG, "HTTP MJPEG stream server failed to start");
      }
    }

    // RTSP 스트리밍 서버 (포트 554)
    if (!rtsp_server_) {
      rtsp_server_ = new RTSPServer();
      rtsp_server_->SetFrameCallback([](uint8_t **buf, size_t *len) -> bool {
        if (!camera_service_) {
          return false;
        }
        static std::vector<uint8_t> frame_buffer;
        if (camera_service_->CaptureFrame(frame_buffer)) {
          *buf = frame_buffer.data();
          *len = frame_buffer.size();
          return true;
        }
        return false;
      });
    }
    if (!rtsp_server_->IsRunning()) {
      if (rtsp_server_->Start()) {
        ESP_LOGI(TAG, "RTSP stream server started on port 554");
      } else {
        ESP_LOGW(TAG, "RTSP stream server failed to start");
      }
    }
  }
}

void Application::HandleNetworkDisconnectedEvent() {
  ESP_LOGI(TAG, "Network disconnected");
  SetDeviceState(kDeviceStateConnecting);

  // 상태 보고 서비스 중지
  if (status_reporter_ && status_reporter_->IsRunning()) {
    status_reporter_->Stop();
    ESP_LOGI(TAG, "Status reporter stopped");
  }
}

void Application::HandleErrorEvent() {
  ESP_LOGE(TAG, "Error event: %s", last_error_message_.c_str());
  SetDeviceState(kDeviceStateError);
}

void Application::OnStateChanged(DeviceState old_state, DeviceState new_state) {
  ESP_LOGI(TAG, "State changed: %d -> %d", old_state, new_state);
}

void Application::HandleButtonEvent(ButtonId button, ButtonEvent event) {
  ESP_LOGI(TAG, "Button event: button=%d, event=%d", static_cast<int>(button),
           static_cast<int>(event));

  // 버튼 A 누름: 즉시 상태 보고 (온라인 전환)
  if (button == ButtonId::kButtonA && event == ButtonEvent::kPressed) {
    if (status_reporter_) {
      ESP_LOGI(TAG, "Button A pressed: Reporting status now (force online)");
      status_reporter_->ReportNow();

      if (display_service_) {
        display_service_->ShowText("상태 보고 완료", 2000);
      }
    }
  }

  // 버튼 B 누름: ASR 토글
  if (button == ButtonId::kButtonB && event == ButtonEvent::kPressed) {
    if (asr_service_) {
      if (asr_service_->IsSessionActive()) {
        // ASR 중지
        asr_service_->StopSession();
        if (display_service_) {
          display_service_->ShowListening(false);
        }
        if (status_reporter_) {
          status_reporter_->SetMicStatus("stopped");
        }
        SetDeviceState(kDeviceStateIdle);
        ESP_LOGI(TAG, "Button B pressed: ASR stopped");
      } else {
        // ASR 시작
        if (asr_service_->StartSession("ko")) {
          if (display_service_) {
            display_service_->ShowListening(true);
          }
          if (status_reporter_) {
            status_reporter_->SetMicStatus("active");
          }
          SetDeviceState(kDeviceStateListening);
          ESP_LOGI(TAG, "Button B pressed: ASR started");
        }
      }
    }
  }

  // 버튼 C 누름: 디스플레이 클리어
  if (button == ButtonId::kButtonC && event == ButtonEvent::kPressed) {
    if (display_service_) {
      display_service_->Clear();
      ESP_LOGI(TAG, "Button C pressed: Display cleared");
    }
  }

  // 전원 버튼 길게 누름: Light Sleep 모드 진입
  if (button == ButtonId::kButtonPower && event == ButtonEvent::kLongPress) {
    ESP_LOGI(TAG, "Power button long press: Entering Light Sleep");
    if (display_service_) {
      display_service_->ShowText("절전 모드...", 1000);
    }
    vTaskDelay(pdMS_TO_TICKS(1000));

    if (power_manager_) {
      // 5분 후 자동 깨우기 또는 버튼으로 깨우기
      power_manager_->EnterLightSleep(300000); // 5분

      // 깨어난 후 즉시 상태 보고
      if (status_reporter_) {
        ESP_LOGI(TAG, "Woke up from Light Sleep, reporting status");
        status_reporter_->ReportNow();
      }
      if (display_service_) {
        display_service_->ShowText("활성화됨", 2000);
      }
    }
  }

  // 전원 버튼 더블클릭: 시스템 재시작
  if (button == ButtonId::kButtonPower && event == ButtonEvent::kDoubleClick) {
    ESP_LOGI(TAG, "Power button double click: Restarting system");
    if (display_service_) {
      display_service_->ShowText("재시작...", 2000);
    }
    vTaskDelay(pdMS_TO_TICKS(2000));
    esp_restart();
  }
}
