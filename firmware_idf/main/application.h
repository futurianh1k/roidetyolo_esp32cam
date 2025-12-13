#ifndef APPLICATION_H
#define APPLICATION_H

#include <esp_timer.h>
#include <freertos/FreeRTOS.h>
#include <freertos/event_groups.h>
#include <freertos/task.h>

#include <deque>
#include <functional>
#include <memory>
#include <mutex>
#include <string>

#include "device_state.h"
#include "device_state_machine.h"
#include "input/button_service.h"

// Main event bits
#define MAIN_EVENT_SCHEDULE (1 << 0)
#define MAIN_EVENT_NETWORK_CONNECTED (1 << 1)
#define MAIN_EVENT_NETWORK_DISCONNECTED (1 << 2)
#define MAIN_EVENT_STATE_CHANGED (1 << 3)
#define MAIN_EVENT_ERROR (1 << 4)
#define MAIN_EVENT_CLOCK_TICK (1 << 5)

/**
 * Application - Main application class (Singleton)
 *
 * Manages the main event loop and coordinates all system components.
 *
 * 참고: xiaozhi-esp32/main/application.h 기반
 */
class Application {
public:
  static Application &GetInstance() {
    static Application instance;
    return instance;
  }

  // Delete copy constructor and assignment operator
  Application(const Application &) = delete;
  Application &operator=(const Application &) = delete;

  /**
   * Initialize the application
   * This sets up all components, network, etc.
   */
  void Initialize();

  /**
   * Run the main event loop
   * This function runs in the main task and never returns.
   */
  void Run();

  /**
   * Get current device state
   */
  DeviceState GetDeviceState() const { return state_machine_.GetState(); }

  /**
   * Request state transition
   * Returns true if transition was successful
   */
  bool SetDeviceState(DeviceState state);

  /**
   * Schedule a callback to be executed in the main task
   */
  void Schedule(std::function<void()> callback);

private:
  Application();
  ~Application();

  EventGroupHandle_t event_group_ = nullptr;
  esp_timer_handle_t clock_timer_handle_ = nullptr;
  esp_timer_handle_t display_timer_handle_ = nullptr;
  DeviceStateMachine state_machine_;

  std::mutex mutex_;
  std::deque<std::function<void()>> main_tasks_;

  std::string last_error_message_;

  // Event handlers
  void HandleStateChangedEvent();
  void HandleNetworkConnectedEvent();
  void HandleNetworkDisconnectedEvent();
  void HandleErrorEvent();

  // Button event handler
  void HandleButtonEvent(ButtonId button, ButtonEvent event);

  // State change handler called by state machine
  void OnStateChanged(DeviceState old_state, DeviceState new_state);
};

#endif // APPLICATION_H
