/**
 * @file button_service.cc
 * @brief M5Stack CoreS3 버튼 및 터치 입력 서비스 구현
 *
 * References:
 * - M5Unified Touch_Class.cpp
 * - ESP-IDF GPIO 인터럽트
 */

#include "button_service.h"
#include <esp_log.h>
#include <esp_timer.h>

#define TAG "ButtonService"

// 정적 인스턴스 (ISR에서 사용)
static ButtonService *s_instance = nullptr;

ButtonService::ButtonService() { s_instance = this; }

ButtonService::~ButtonService() {
  Stop();
  s_instance = nullptr;
}

bool ButtonService::Initialize() {
  if (initialized_) {
    ESP_LOGW(TAG, "Already initialized");
    return true;
  }

  ESP_LOGI(TAG, "Initializing button service...");

  // 이벤트 큐 생성
  event_queue_ = xQueueCreate(10, sizeof(ButtonEventData));
  if (event_queue_ == nullptr) {
    ESP_LOGE(TAG, "Failed to create event queue");
    return false;
  }

  // 전원 버튼 IRQ 설정 (GPIO35 = AXP2101 IRQ)
  gpio_config_t io_conf = {};
  io_conf.intr_type = GPIO_INTR_NEGEDGE; // 하강 에지 (눌림)
  io_conf.mode = GPIO_MODE_INPUT;
  io_conf.pin_bit_mask = (1ULL << GPIO_POWER_IRQ);
  io_conf.pull_up_en = GPIO_PULLUP_ENABLE;
  io_conf.pull_down_en = GPIO_PULLDOWN_DISABLE;

  esp_err_t ret = gpio_config(&io_conf);
  if (ret != ESP_OK) {
    ESP_LOGW(TAG, "Failed to configure power button GPIO: %s",
             esp_err_to_name(ret));
    // 계속 진행 (터치 버튼은 사용 가능)
  } else {
    // ISR 핸들러 등록
    gpio_install_isr_service(0);
    gpio_isr_handler_add(GPIO_POWER_IRQ, PowerButtonISR, this);
    ESP_LOGI(TAG, "Power button IRQ configured");
  }

  initialized_ = true;
  ESP_LOGI(TAG, "Button service initialized");
  return true;
}

void ButtonService::Start() {
  if (!initialized_) {
    ESP_LOGE(TAG, "Not initialized");
    return;
  }

  if (is_running_) {
    ESP_LOGW(TAG, "Already running");
    return;
  }

  // 버튼 처리 태스크 생성
  BaseType_t result = xTaskCreate(ButtonTaskFunc, "button_task", 4096, this, 5,
                                  &button_task_handle_);

  if (result != pdPASS) {
    ESP_LOGE(TAG, "Failed to create button task");
    return;
  }

  is_running_ = true;
  ESP_LOGI(TAG, "Button service started");
}

void ButtonService::Stop() {
  if (!is_running_) {
    return;
  }

  is_running_ = false;

  if (button_task_handle_ != nullptr) {
    vTaskDelete(button_task_handle_);
    button_task_handle_ = nullptr;
  }

  ESP_LOGI(TAG, "Button service stopped");
}

bool ButtonService::IsPressed(ButtonId button) const {
  int index = static_cast<int>(button);
  if (index >= 0 && index < 4) {
    return button_states_[index];
  }
  return false;
}

void ButtonService::ButtonTaskFunc(void *param) {
  ButtonService *service = static_cast<ButtonService *>(param);
  service->ProcessButtonEvents();
}

void ButtonService::ProcessButtonEvents() {
  ButtonEventData event_data;

  while (is_running_) {
    // 이벤트 큐에서 이벤트 수신
    if (xQueueReceive(event_queue_, &event_data, pdMS_TO_TICKS(100)) ==
        pdTRUE) {
      // 콜백 호출
      if (button_callback_) {
        button_callback_(event_data.button, event_data.event);
      }
    }

    // 터치 이벤트 폴링 (TODO: 터치 드라이버 구현 필요)
    // ProcessTouchEvents();

    // 롱프레스 체크
    uint32_t now = esp_timer_get_time() / 1000; // ms
    for (int i = 0; i < 4; i++) {
      if (button_states_[i] && button_press_time_[i] > 0) {
        if ((now - button_press_time_[i]) >= LONG_PRESS_TIME_MS) {
          // 롱프레스 이벤트 발생
          ButtonEventData long_press_event = {.button =
                                                  static_cast<ButtonId>(i),
                                              .event = ButtonEvent::kLongPress,
                                              .timestamp = now};

          if (button_callback_) {
            button_callback_(long_press_event.button, long_press_event.event);
          }

          // 롱프레스는 한 번만 발생
          button_press_time_[i] = 0;
        }
      }
    }
  }

  vTaskDelete(nullptr);
}

void IRAM_ATTR ButtonService::PowerButtonISR(void *arg) {
  ButtonService *service = static_cast<ButtonService *>(arg);
  if (service) {
    service->HandlePowerButtonIRQ();
  }
}

void ButtonService::HandlePowerButtonIRQ() {
  uint32_t now = esp_timer_get_time() / 1000; // ms
  int index = static_cast<int>(ButtonId::kButtonPower);

  // 디바운싱 (50ms)
  static uint32_t last_irq_time = 0;
  if ((now - last_irq_time) < 50) {
    return;
  }
  last_irq_time = now;

  // 버튼 상태 토글 (간단한 처리)
  button_states_[index] = !button_states_[index];

  ButtonEventData event_data;
  event_data.timestamp = now;
  event_data.button = ButtonId::kButtonPower;

  if (button_states_[index]) {
    // 버튼 눌림
    event_data.event = ButtonEvent::kPressed;
    button_press_time_[index] = now;

    // 더블클릭 체크
    if ((now - last_click_time_[index]) < DOUBLE_CLICK_TIME_MS) {
      event_data.event = ButtonEvent::kDoubleClick;
      last_click_time_[index] = 0;
    } else {
      last_click_time_[index] = now;
    }
  } else {
    // 버튼 놓음
    event_data.event = ButtonEvent::kReleased;
    button_press_time_[index] = 0;
  }

  // ISR에서 큐로 이벤트 전송
  BaseType_t higher_priority_task_woken = pdFALSE;
  xQueueSendFromISR(event_queue_, &event_data, &higher_priority_task_woken);

  if (higher_priority_task_woken) {
    portYIELD_FROM_ISR();
  }
}

void ButtonService::ProcessTouchEvents() {
  // TODO: FT6336 터치 컨트롤러 드라이버 통합
  // M5Stack CoreS3는 FT6336 터치 컨트롤러 사용
  // 터치 좌표를 읽고 버튼 영역에 따라 이벤트 생성

  // 현재는 전원 버튼만 지원
  // 터치 버튼은 향후 터치 드라이버 추가 시 구현
}
