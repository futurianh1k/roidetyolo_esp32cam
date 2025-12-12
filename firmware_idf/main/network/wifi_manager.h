#ifndef WIFI_MANAGER_H
#define WIFI_MANAGER_H

#include <string>
#include <functional>

enum class NetworkEvent {
    Scanning,
    Connecting,
    Connected,
    Disconnected,
    Error
};

using NetworkEventCallback = std::function<void(NetworkEvent event, const std::string& data)>;

class WiFiManager {
public:
    static WiFiManager& GetInstance() {
        static WiFiManager instance;
        return instance;
    }

    bool Initialize(const std::string& ssid, const std::string& password);
    void Start();
    void Stop();
    bool IsConnected() const;
    std::string GetIPAddress() const;
    int GetRSSI() const;
    
    void SetEventCallback(NetworkEventCallback callback);

private:
    WiFiManager() = default;
    ~WiFiManager() = default;
    WiFiManager(const WiFiManager&) = delete;
    WiFiManager& operator=(const WiFiManager&) = delete;

    std::string ssid_;
    std::string password_;
    bool initialized_ = false;
    bool connected_ = false;
    NetworkEventCallback event_callback_;

    static void WiFiEventHandler(void* arg, esp_event_base_t event_base,
                                 int32_t event_id, void* event_data);
    void OnWiFiEvent(esp_event_base_t event_base, int32_t event_id, void* event_data);
};

#endif // WIFI_MANAGER_H

