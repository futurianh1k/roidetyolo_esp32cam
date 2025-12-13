/**
 * @file status_reporter.cc
 * @brief 장비 상태를 백엔드 서버에 주기적으로 보고하는 서비스 구현
 */

#include "status_reporter.h"
#include <esp_log.h>
#include <esp_system.h>
#include <esp_timer.h>

#define TAG "StatusReporter"

StatusReporter::StatusReporter()
    : report_interval_ms_(10000), is_running_(false), initialized_(false),
      camera_status_("stopped"), mic_status_("stopped"), report_timer_(nullptr),
      report_callback_(nullptr) {}

StatusReporter::~StatusReporter() { Stop(); }

bool StatusReporter::Initialize(const std::string &backend_url, int device_id,
                                uint32_t report_interval_ms) {
  if (backend_url.empty() || device_id <= 0) {
    ESP_LOGE(TAG, "Invalid parameters");
    return false;
  }

  // 백엔드 클라이언트 초기화
  if (!backend_client_.Initialize(backend_url, device_id)) {
    ESP_LOGE(TAG, "Failed to initialize backend client");
    return false;
  }

  report_interval_ms_ = report_interval_ms;
  initialized_ = true;

  ESP_LOGI(TAG, "Initialized: backend=%s, device_id=%d, interval=%dms",
           backend_url.c_str(), device_id, report_interval_ms);

  return true;
}

void StatusReporter::Start() {
  if (!initialized_) {
    ESP_LOGE(TAG, "Not initialized");
    return;
  }

  if (is_running_) {
    ESP_LOGW(TAG, "Already running");
    return;
  }

  // FreeRTOS 소프트웨어 타이머 생성
  report_timer_ =
      xTimerCreate("status_timer", pdMS_TO_TICKS(report_interval_ms_),
                   pdTRUE, // 반복 타이머
                   this,   // 타이머 ID로 this 포인터 사용
                   TimerCallback);

  if (report_timer_ == nullptr) {
    ESP_LOGE(TAG, "Failed to create timer");
    return;
  }

  // 타이머 시작
  if (xTimerStart(report_timer_, 0) != pdPASS) {
    ESP_LOGE(TAG, "Failed to start timer");
    xTimerDelete(report_timer_, 0);
    report_timer_ = nullptr;
    return;
  }

  is_running_ = true;
  ESP_LOGI(TAG, "Started with interval %d ms", report_interval_ms_);

  // 즉시 첫 번째 보고 실행
  ReportNow();
}

void StatusReporter::Stop() {
  if (!is_running_) {
    return;
  }

  if (report_timer_ != nullptr) {
    xTimerStop(report_timer_, 0);
    xTimerDelete(report_timer_, 0);
    report_timer_ = nullptr;
  }

  is_running_ = false;
  ESP_LOGI(TAG, "Stopped");
}

bool StatusReporter::ReportNow() {
  if (!initialized_) {
    ESP_LOGE(TAG, "Not initialized");
    return false;
  }

  // 상태 수집
  DeviceStatusData status = CollectStatus();

  // 백엔드로 전송
  bool success = backend_client_.SendDeviceStatus(status);

  if (success) {
    ESP_LOGD(TAG, "Status reported: mem=%d, cam=%s, mic=%s",
             status.memory_usage, status.camera_status.c_str(),
             status.mic_status.c_str());
  } else {
    ESP_LOGW(TAG, "Failed to report status");
  }

  // 콜백 호출
  if (report_callback_) {
    report_callback_(success);
  }

  return success;
}

DeviceStatusData StatusReporter::CollectStatus() {
  DeviceStatusData status;

  // 배터리 레벨 (-1 = 지원하지 않음 / 센서 없음)
  // TODO: AXP2101에서 실제 배터리 레벨 읽기
  status.battery_level = -1;

  // 힙 메모리 사용량 (남은 바이트)
  status.memory_usage = esp_get_free_heap_size();

  // 스토리지 사용량 (-1 = 지원하지 않음)
  status.storage_usage = -1;

  // CPU 온도 (ESP32-S3에서는 직접 측정 불가)
  // TODO: 외부 온도 센서가 있다면 읽기
  status.temperature = 0.0f;

  // CPU 사용률 (간단한 추정)
  // TODO: 더 정확한 CPU 사용률 계산
  status.cpu_usage = 0;

  // 컴포넌트 상태
  status.camera_status = camera_status_;
  status.mic_status = mic_status_;

  return status;
}

void StatusReporter::TimerCallback(TimerHandle_t timer) {
  // 타이머 ID에서 StatusReporter 포인터 가져오기
  StatusReporter *reporter =
      static_cast<StatusReporter *>(pvTimerGetTimerID(timer));
  if (reporter) {
    reporter->ReportNow();
  }
}
