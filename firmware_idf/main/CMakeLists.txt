# Main component CMakeLists.txt

# Define source files
set(SOURCES
    "main.cc"
    "application.cc"
    "device_state_machine.cc"
    "device_state.h"
    
    # Audio module
    "audio/audio_service.cc"
    "audio/audio_codec.cc"
    
    # Camera module
    "camera/camera_service.cc"
    
    # Network module
    "network/wifi_manager.cc"
    "network/mqtt_client.cc"
)

# Include directories
set(INCLUDE_DIRS
    "."
    "audio"
    "camera"
    "network"
    "display"
    "status"
)

# Register component
idf_component_register(
    SRCS ${SOURCES}
    INCLUDE_DIRS ${INCLUDE_DIRS}
    REQUIRES 
        driver
        esp_wifi
        esp_http_client
        nvs_flash
        esp_camera
        mqtt
        esp_event
        esp_netif
)

