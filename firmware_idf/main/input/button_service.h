/**
 * @file button_service.h
 * @brief M5Stack CoreS3 버튼 및 터치 입력 서비스
 *
 * 기능:
 * - 터치 버튼 (화면 하단 3개 영역) 감지
 * - 전원 버튼 (AXP2101 IRQ) 감지
 * - 버튼 이벤트 콜백 제공
 *
 * References:
 * - M5Unified Touch_Class.cpp
 * - ESP-IDF GPIO 인터럽트
 */

#ifndef BUTTON_SERVICE_H
#define BUTTON_SERVICE_H

#include <driver/gpio.h>
#include <esp_err.h>
#include <freertos/FreeRTOS.h>
#include <freertos/queue.h>
#include <freertos/task.h>
#include <functional>

/**
 * @brief 버튼 ID
 */
enum class ButtonId {
  kButtonA,    ///< 터치 버튼 A (왼쪽)
  kButtonB,    ///< 터치 버튼 B (가운데)
  kButtonC,    ///< 터치 버튼 C (오른쪽)
  kButtonPower ///< 전원 버튼
};

/**
 * @brief 버튼 이벤트 타입
 */
enum class ButtonEvent {
  kPressed,    ///< 버튼 눌림
  kReleased,   ///< 버튼 놓음
  kLongPress,  ///< 길게 누름 (1초 이상)
  kDoubleClick ///< 더블 클릭
};

/**
 * @brief 버튼 이벤트 데이터
 */
struct ButtonEventData {
  ButtonId button;
  ButtonEvent event;
  uint32_t timestamp;
};

/**
 * @brief 버튼 이벤트 콜백 타입
 */
using ButtonCallback = std::function<void(ButtonId, ButtonEvent)>;

/**
 * @brief M5Stack CoreS3 버튼 서비스 클래스
 */
class ButtonService {
public:
  ButtonService();
  ~ButtonService();

  // 복사 금지
  ButtonService(const ButtonService &) = delete;
  ButtonService &operator=(const ButtonService &) = delete;

  /**
   * @brief 버튼 서비스 초기화
   * @return 초기화 성공 여부
   */
  bool Initialize();

  /**
   * @brief 버튼 서비스 시작
   */
  void Start();

  /**
   * @brief 버튼 서비스 중지
   */
  void Stop();

  /**
   * @brief 버튼 이벤트 콜백 설정
   * @param callback 버튼 이벤트 발생 시 호출될 콜백
   */
  void SetButtonCallback(ButtonCallback callback) {
    button_callback_ = callback;
  }

  /**
   * @brief 버튼 상태 확인
   * @param button 확인할 버튼
   * @return 버튼이 현재 눌려있으면 true
   */
  bool IsPressed(ButtonId button) const;

  /**
   * @brief 버튼 서비스가 실행 중인지 확인
   */
  bool IsRunning() const { return is_running_; }

private:
  // GPIO 핀 정의 (M5Stack CoreS3)
  // 전원 버튼 IRQ는 AXP2101에서 처리
  static constexpr gpio_num_t GPIO_POWER_IRQ = GPIO_NUM_35; // AXP2101 IRQ

  // 터치 영역 정의 (화면 하단)
  // CoreS3 화면: 320x240, 하단 버튼 영역: y > 200
  static constexpr int TOUCH_BUTTON_Y_MIN = 200;
  static constexpr int BUTTON_A_X_MIN = 0;
  static constexpr int BUTTON_A_X_MAX = 106;
  static constexpr int BUTTON_B_X_MIN = 107;
  static constexpr int BUTTON_B_X_MAX = 213;
  static constexpr int BUTTON_C_X_MIN = 214;
  static constexpr int BUTTON_C_X_MAX = 320;

  // 롱프레스 감지 시간 (ms)
  static constexpr uint32_t LONG_PRESS_TIME_MS = 1000;

  // 더블클릭 감지 시간 (ms)
  static constexpr uint32_t DOUBLE_CLICK_TIME_MS = 300;

  // 버튼 처리 태스크
  static void ButtonTaskFunc(void *param);
  void ProcessButtonEvents();

  // 전원 버튼 IRQ 핸들러
  static void IRAM_ATTR PowerButtonISR(void *arg);
  void HandlePowerButtonIRQ();

  // 터치 이벤트 처리
  void ProcessTouchEvents();

  // 상태 변수
  bool initialized_ = false;
  bool is_running_ = false;
  ButtonCallback button_callback_;

  // 태스크 핸들
  TaskHandle_t button_task_handle_ = nullptr;
  QueueHandle_t event_queue_ = nullptr;

  // 버튼 상태
  bool button_states_[4] = {false, false, false, false};
  uint32_t button_press_time_[4] = {0, 0, 0, 0};
  uint32_t last_click_time_[4] = {0, 0, 0, 0};
};

#endif // BUTTON_SERVICE_H
