#include "application.h"
#include "audio/audio_service.h"
#include "audio/audio_codec.h"
#include "camera/camera_service.h"
#include "network/wifi_manager.h"
#include "network/mqtt_client.h"
#include "config.h"
#include <esp_log.h>
#include <cstring>
#include <algorithm>

#define TAG "Application"

// 전역 인스턴스
static AudioCodec* audio_codec_ = nullptr;
static AudioService* audio_service_ = nullptr;
static CameraService* camera_service_ = nullptr;
static WiFiManager* wifi_manager_ = nullptr;
static MQTTClient* mqtt_client_ = nullptr;

Application::Application() {
    event_group_ = xEventGroupCreate();
    
    // Create clock timer
    esp_timer_create_args_t clock_timer_args = {
        .callback = [](void* arg) {
            Application* app = (Application*)arg;
            xEventGroupSetBits(app->event_group_, MAIN_EVENT_CLOCK_TICK);
        },
        .arg = this,
        .dispatch_method = ESP_TIMER_TASK,
        .name = "clock_timer",
        .skip_unhandled_events = true
    };
    esp_timer_create(&clock_timer_args, &clock_timer_handle_);
}

Application::~Application() {
    if (clock_timer_handle_ != nullptr) {
        esp_timer_stop(clock_timer_handle_);
        esp_timer_delete(clock_timer_handle_);
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
    state_machine_.AddStateChangeListener([this](DeviceState old_state, DeviceState new_state) {
        xEventGroupSetBits(event_group_, MAIN_EVENT_STATE_CHANGED);
    });
    
    // Initialize audio
    audio_codec_ = new AudioCodec();
    if (audio_codec_->Initialize()) {
        audio_service_ = new AudioService();
        if (audio_service_->Initialize(audio_codec_)) {
            audio_service_->Start();
            ESP_LOGI(TAG, "Audio service initialized");
        }
    }
    
    // Initialize camera
    camera_service_ = new CameraService();
    if (camera_service_->Initialize()) {
        camera_service_->Start();
        ESP_LOGI(TAG, "Camera service initialized");
    }
    
    // Initialize WiFi
    wifi_manager_ = &WiFiManager::GetInstance();
    wifi_manager_->SetEventCallback([this](NetworkEvent event, const std::string& data) {
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
    
    // Initialize MQTT (after WiFi connected)
    mqtt_client_ = new MQTTClient();
    mqtt_client_->Initialize(MQTT_BROKER, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD);
    mqtt_client_->SetMessageCallback([](const std::string& topic, const std::string& payload) {
        ESP_LOGI(TAG, "MQTT message: %s -> %s", topic.c_str(), payload.c_str());
        // TODO: MQTT 메시지 처리
    });
    
    // Start clock timer (1 second interval)
    esp_timer_start_periodic(clock_timer_handle_, 1000000);
    
    SetDeviceState(kDeviceStateIdle);
    
    ESP_LOGI(TAG, "Initialization complete");
}

void Application::Run() {
    const EventBits_t ALL_EVENTS = 
        MAIN_EVENT_SCHEDULE |
        MAIN_EVENT_NETWORK_CONNECTED |
        MAIN_EVENT_NETWORK_DISCONNECTED |
        MAIN_EVENT_STATE_CHANGED |
        MAIN_EVENT_ERROR |
        MAIN_EVENT_CLOCK_TICK;
    
    ESP_LOGI(TAG, "Main event loop started");
    
    while (true) {
        auto bits = xEventGroupWaitBits(
            event_group_, 
            ALL_EVENTS, 
            pdTRUE,  // Clear bits on exit
            pdFALSE, // Wait for any bit
            portMAX_DELAY
        );
        
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
            
            for (auto& task : tasks) {
                try {
                    task();
                } catch (...) {
                    ESP_LOGE(TAG, "Exception in scheduled task");
                }
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
}

void Application::HandleNetworkConnectedEvent() {
    ESP_LOGI(TAG, "Network connected");
    SetDeviceState(kDeviceStateConnected);
    
    // MQTT 연결
    if (mqtt_client_) {
        std::string client_id = MQTT_CLIENT_ID_PREFIX + std::string(DEVICE_ID);
        mqtt_client_->Connect(client_id);
        
        // 토픽 구독
        mqtt_client_->Subscribe(TOPIC_CONTROL_CAMERA, MQTT_QOS);
        mqtt_client_->Subscribe(TOPIC_CONTROL_MICROPHONE, MQTT_QOS);
        mqtt_client_->Subscribe(TOPIC_CONTROL_SPEAKER, MQTT_QOS);
        mqtt_client_->Subscribe(TOPIC_CONTROL_DISPLAY, MQTT_QOS);
        mqtt_client_->Subscribe(TOPIC_CONTROL_SYSTEM, MQTT_QOS);
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
