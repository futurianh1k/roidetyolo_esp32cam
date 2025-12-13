# Main component CMakeLists.txt

# Define source files
set(SOURCES
    "main.cc"
    "application.cc"
    "device_state_machine.cc"
    "device_state.h"
    
    # Power module (AXP2101, AW9523)
    "power/power_manager.cc"
    
    # Audio module
    "audio/audio_service.cc"
    "audio/audio_codec.cc"
    "audio/wav_player.cc"
    
    # Camera module
    "camera/camera_service.cc"
    
    # Network module
    "network/wifi_manager.cc"
    "network/mqtt_client_wrapper.cc"
    "network/websocket_client.cc"
    "network/backend_client.cc"
    
    # ASR module
    "asr/asr_service.cc"
    
    # Display module
    "display/display_service.cc"
    
    # Status module
    "status/status_reporter.cc"
    
    # Input module
    "input/button_service.cc"
)

# Include directories
set(INCLUDE_DIRS
    "."
    "power"
    "audio"
    "camera"
    "network"
    "display"
    "asr"
    "status"
    "input"
)

# Register component
idf_component_register(
    SRCS ${SOURCES}
    INCLUDE_DIRS ${INCLUDE_DIRS}
    REQUIRES 
        driver
        esp_wifi
        esp_http_client
        esp_websocket_client
        nvs_flash
        esp32-camera
        mqtt
        esp_event
        esp_netif
        json
        spiffs
)

