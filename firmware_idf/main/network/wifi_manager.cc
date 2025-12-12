#include "wifi_manager.h"
#include <esp_log.h>
#include <esp_wifi.h>
#include <esp_event.h>
#include <esp_netif.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <string.h>
#include <lwip/ip4_addr.h>

#define TAG "WiFiManager"

bool WiFiManager::Initialize(const std::string& ssid, const std::string& password) {
    ssid_ = ssid;
    password_ = password;
    
    // 네트워크 인터페이스 초기화
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    
    esp_netif_t* sta_netif = esp_netif_create_default_wifi_sta();
    if (!sta_netif) {
        ESP_LOGE(TAG, "Failed to create WiFi STA netif");
        return false;
    }
    
    // WiFi 초기화
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));
    
    // 이벤트 핸들러 등록
    ESP_ERROR_CHECK(esp_event_handler_instance_register(
        WIFI_EVENT, ESP_EVENT_ANY_ID, &WiFiEventHandler, this, nullptr));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(
        IP_EVENT, IP_EVENT_STA_GOT_IP, &WiFiEventHandler, this, nullptr));
    
    // WiFi 모드 설정
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    
    initialized_ = true;
    ESP_LOGI(TAG, "WiFi manager initialized");
    return true;
}

void WiFiManager::Start() {
    if (!initialized_) {
        ESP_LOGE(TAG, "WiFi manager not initialized");
        return;
    }
    
    // WiFi 설정
    wifi_config_t wifi_config = {};
    strncpy((char*)wifi_config.sta.ssid, ssid_.c_str(), sizeof(wifi_config.sta.ssid) - 1);
    strncpy((char*)wifi_config.sta.password, password_.c_str(), sizeof(wifi_config.sta.password) - 1);
    wifi_config.sta.threshold.authmode = WIFI_AUTH_WPA2_PSK;
    
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    
    // WiFi 시작
    ESP_ERROR_CHECK(esp_wifi_start());
    ESP_ERROR_CHECK(esp_wifi_connect());
    
    ESP_LOGI(TAG, "WiFi connection started");
    
    if (event_callback_) {
        event_callback_(NetworkEvent::Connecting, ssid_);
    }
}

void WiFiManager::Stop() {
    if (initialized_) {
        esp_wifi_disconnect();
        esp_wifi_stop();
        connected_ = false;
        
        if (event_callback_) {
            event_callback_(NetworkEvent::Disconnected, "");
        }
    }
}

bool WiFiManager::IsConnected() const {
    return connected_;
}

std::string WiFiManager::GetIPAddress() const {
    if (!connected_) {
        return "";
    }
    
    esp_netif_ip_info_t ip_info;
    esp_netif_t* netif = esp_netif_get_handle_from_ifkey("WIFI_STA_DEF");
    if (netif && esp_netif_get_ip_info(netif, &ip_info) == ESP_OK) {
        char ip_str[16];
        snprintf(ip_str, sizeof(ip_str), IPSTR, IP2STR(&ip_info.ip));
        return std::string(ip_str);
    }
    return "";
}

int WiFiManager::GetRSSI() const {
    if (!connected_) {
        return 0;
    }
    
    wifi_ap_record_t ap_info;
    if (esp_wifi_sta_get_ap_info(&ap_info) == ESP_OK) {
        return ap_info.rssi;
    }
    return 0;
}

void WiFiManager::SetEventCallback(NetworkEventCallback callback) {
    event_callback_ = callback;
}

void WiFiManager::WiFiEventHandler(void* arg, esp_event_base_t event_base,
                                   int32_t event_id, void* event_data) {
    WiFiManager* manager = static_cast<WiFiManager*>(arg);
    manager->OnWiFiEvent(event_base, event_id, event_data);
}

void WiFiManager::OnWiFiEvent(esp_event_base_t event_base, int32_t event_id, void* event_data) {
    if (event_base == WIFI_EVENT) {
        switch (event_id) {
            case WIFI_EVENT_STA_START:
                ESP_LOGI(TAG, "WiFi STA started");
                break;
                
            case WIFI_EVENT_STA_CONNECTED: {
                wifi_event_sta_connected_t* event = (wifi_event_sta_connected_t*)event_data;
                ESP_LOGI(TAG, "Connected to AP: %s", event->ssid);
                break;
            }
            
            case WIFI_EVENT_STA_DISCONNECTED: {
                wifi_event_sta_disconnected_t* event = (wifi_event_sta_disconnected_t*)event_data;
                ESP_LOGW(TAG, "Disconnected from AP: %s, reason: %d", event->ssid, event->reason);
                connected_ = false;
                
                if (event_callback_) {
                    event_callback_(NetworkEvent::Disconnected, "");
                }
                
                // 재연결 시도
                esp_wifi_connect();
                break;
            }
            
            default:
                break;
        }
    } else if (event_base == IP_EVENT) {
        if (event_id == IP_EVENT_STA_GOT_IP) {
            ip_event_got_ip_t* event = (ip_event_got_ip_t*)event_data;
            ESP_LOGI(TAG, "Got IP: " IPSTR, IP2STR(&event->ip_info.ip));
            connected_ = true;
            
            if (event_callback_) {
                event_callback_(NetworkEvent::Connected, GetIPAddress());
            }
        }
    }
}

