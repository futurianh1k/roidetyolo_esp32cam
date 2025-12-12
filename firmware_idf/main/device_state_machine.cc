#include "device_state_machine.h"
#include <algorithm>
#include <esp_log.h>

#define TAG "StateMachine"

DeviceStateMachine::DeviceStateMachine() {
  current_state_ = kDeviceStateUnknown;
  next_listener_id_ = 0;
}

bool DeviceStateMachine::TransitionTo(DeviceState new_state) {
  DeviceState old_state;
  bool should_notify = false;

  // Critical section - lock only for state manipulation
  {
    std::lock_guard<std::mutex> lock(mutex_);

    old_state = current_state_.load();

    if (old_state == new_state) {
      // Already in target state
      return true;
    }

    if (!IsValidTransition(old_state, new_state)) {
      ESP_LOGW(TAG, "Invalid state transition: %s -> %s",
               GetStateName(old_state), GetStateName(new_state));
      return false;
    }

    ESP_LOGI(TAG, "State transition: %s -> %s", GetStateName(old_state),
             GetStateName(new_state));

    current_state_.store(new_state);
    should_notify = true;
  }
  // Lock released here

  // Notify listeners AFTER releasing the lock to prevent deadlock
  if (should_notify) {
    NotifyStateChange(old_state, new_state);
  }

  return true;
}

bool DeviceStateMachine::CanTransitionTo(DeviceState target) const {
  DeviceState current = current_state_.load();
  return IsValidTransition(current, target);
}

int DeviceStateMachine::AddStateChangeListener(StateCallback callback) {
  std::lock_guard<std::mutex> lock(mutex_);
  int id = next_listener_id_++;
  listeners_.emplace_back(id, callback);
  return id;
}

void DeviceStateMachine::RemoveStateChangeListener(int listener_id) {
  std::lock_guard<std::mutex> lock(mutex_);
  listeners_.erase(std::remove_if(listeners_.begin(), listeners_.end(),
                                  [listener_id](const auto &pair) {
                                    return pair.first == listener_id;
                                  }),
                   listeners_.end());
}

const char *DeviceStateMachine::GetStateName(DeviceState state) {
  switch (state) {
  case kDeviceStateUnknown:
    return "Unknown";
  case kDeviceStateStarting:
    return "Starting";
  case kDeviceStateIdle:
    return "Idle";
  case kDeviceStateConnecting:
    return "Connecting";
  case kDeviceStateConnected:
    return "Connected";
  case kDeviceStateListening:
    return "Listening";
  case kDeviceStateProcessing:
    return "Processing";
  case kDeviceStateSpeaking:
    return "Speaking";
  case kDeviceStateCameraActive:
    return "CameraActive";
  case kDeviceStateError:
    return "Error";
  default:
    return "Invalid";
  }
}

bool DeviceStateMachine::IsValidTransition(DeviceState from,
                                           DeviceState to) const {
  // Allow transition to Error from any state
  if (to == kDeviceStateError) {
    return true;
  }

  // Allow transition from Error to Idle (recovery)
  if (from == kDeviceStateError && to == kDeviceStateIdle) {
    return true;
  }

  // Allow initial transitions from Unknown
  if (from == kDeviceStateUnknown) {
    return to == kDeviceStateStarting || to == kDeviceStateIdle;
  }

  // Starting can transition to Idle or Connecting
  if (from == kDeviceStateStarting) {
    return to == kDeviceStateIdle || to == kDeviceStateConnecting;
  }

  // Idle can transition to Connecting, Listening, or CameraActive
  if (from == kDeviceStateIdle) {
    return to == kDeviceStateConnecting || to == kDeviceStateListening ||
           to == kDeviceStateCameraActive;
  }

  // Connecting can transition to Connected or Idle
  if (from == kDeviceStateConnecting) {
    return to == kDeviceStateConnected || to == kDeviceStateIdle;
  }

  // Connected can transition to Idle, Listening, or CameraActive
  if (from == kDeviceStateConnected) {
    return to == kDeviceStateIdle || to == kDeviceStateListening ||
           to == kDeviceStateCameraActive;
  }

  // Listening can transition to Processing, Idle, or Connected
  if (from == kDeviceStateListening) {
    return to == kDeviceStateProcessing || to == kDeviceStateIdle ||
           to == kDeviceStateConnected;
  }

  // Processing can transition to Speaking, Idle, or Connected
  if (from == kDeviceStateProcessing) {
    return to == kDeviceStateSpeaking || to == kDeviceStateIdle ||
           to == kDeviceStateConnected;
  }

  // Speaking can transition to Idle or Connected
  if (from == kDeviceStateSpeaking) {
    return to == kDeviceStateIdle || to == kDeviceStateConnected;
  }

  // CameraActive can transition to Idle or Connected
  if (from == kDeviceStateCameraActive) {
    return to == kDeviceStateIdle || to == kDeviceStateConnected;
  }

  return false;
}

void DeviceStateMachine::NotifyStateChange(DeviceState old_state,
                                           DeviceState new_state) {
  // Make a copy of listeners to avoid holding lock during callback
  std::vector<std::pair<int, StateCallback>> listeners_copy;
  {
    std::lock_guard<std::mutex> lock(mutex_);
    listeners_copy = listeners_;
  }

  // Invoke callbacks (without holding lock)
  // ESP-IDF는 기본적으로 C++ 예외를 비활성화하므로 try-catch 사용 불가
  // 대신 callback 함수 내부에서 오류 처리를 수행해야 함
  for (const auto &[id, callback] : listeners_copy) {
    callback(old_state, new_state);
  }
}
