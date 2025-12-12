#include "display_service.h"
#include <esp_log.h>
#include <esp_timer.h>

#define TAG "DisplayService"
#define LISTENING_ANIMATION_INTERVAL_MS 500 // 0.5초마다 애니메이션 업데이트

DisplayService::DisplayService() {
  initialized_ = false;
  is_listening_ = false;
  listening_animation_frame_ = 0;
  last_animation_update_ = 0;
}

DisplayService::~DisplayService() {}

bool DisplayService::Initialize() {
  // TODO: 실제 디스플레이 하드웨어 초기화 (ILI9341 등)
  // 현재는 로그만 출력
  ESP_LOGI(TAG, "Display service initialized (log only)");
  initialized_ = true;
  return true;
}

void DisplayService::ShowText(const std::string &text, int duration_ms) {
  if (!initialized_) {
    return;
  }

  current_text_ = text;
  ESP_LOGI(TAG, "Display: %s", text.c_str());

  // TODO: 실제 디스플레이에 텍스트 렌더링
  // - LVGL 또는 비트맵 폰트 사용
  // - 텍스트를 화면 중앙에 표시
  // - duration_ms가 0이 아니면 타이머 설정
}

void DisplayService::ShowListening(bool is_listening) {
  if (!initialized_) {
    return;
  }

  is_listening_ = is_listening;
  listening_animation_frame_ = 0;
  last_animation_update_ = 0;

  if (is_listening) {
    ESP_LOGI(TAG, "Display: 🎤 음성인식 중...");
    // 마이크 아이콘 표시 시작
    UpdateListeningAnimation();
  } else {
    ESP_LOGI(TAG, "Display: 음성인식 종료");
    // 마이크 아이콘 숨기기
    // TODO: 실제 디스플레이에서 마이크 아이콘 제거
  }
}

void DisplayService::UpdateListeningAnimation() {
  if (!initialized_ || !is_listening_) {
    return;
  }

  int64_t now = esp_timer_get_time() / 1000; // milliseconds
  if (now - last_animation_update_ < LISTENING_ANIMATION_INTERVAL_MS) {
    return;
  }

  last_animation_update_ = now;
  listening_animation_frame_ = (listening_animation_frame_ + 1) % 4;

  // 마이크 아이콘 애니메이션 (4단계)
  const char *mic_icons[] = {"🎤", "🎤.", "🎤..", "🎤..."};
  std::string display_text = mic_icons[listening_animation_frame_];
  display_text += " 음성인식 중";

  ESP_LOGI(TAG, "Display: %s", display_text.c_str());
  // TODO: 실제 디스플레이에 마이크 아이콘과 애니메이션 표시
  // - 화면 상단 또는 중앙에 마이크 아이콘 표시
  // - 펄스 애니메이션 또는 점 애니메이션
}

void DisplayService::Clear() {
  if (!initialized_) {
    return;
  }

  current_text_.clear();
  is_listening_ = false;
  ESP_LOGI(TAG, "Display: Cleared");

  // TODO: 실제 디스플레이 클리어
}

void DisplayService::ShowStatus(const std::string &status,
                                const std::string &color) {
  if (!initialized_) {
    return;
  }

  ESP_LOGI(TAG, "Display Status: %s (color: %s)", status.c_str(),
           color.c_str());
  // TODO: 상태 표시 (상단 바 등)
}
