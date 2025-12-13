/**
 * @file status_reporter.h
 * @brief 장비 상태를 백엔드 서버에 주기적으로 보고하는 서비스
 *
 * 기능:
 * - 주기적인 상태 보고 (10초 기본)
 * - 시스템 정보 수집 (메모리, CPU 등)
 * - 컴포넌트 상태 수집 (카메라, 마이크 등)
 */

#ifndef STATUS_REPORTER_H
#define STATUS_REPORTER_H

#include "../network/backend_client.h"
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <freertos/timers.h>
#include <functional>
#include <string>

/**
 * @brief 상태 보고 서비스 클래스
 */
class StatusReporter {
public:
  StatusReporter();
  ~StatusReporter();

  /**
   * @brief 서비스 초기화
   * @param backend_url 백엔드 서버 URL (예: http://10.10.11.18:8000)
   * @param device_id 장비 DB ID (숫자)
   * @param report_interval_ms 보고 주기 (밀리초, 기본 10000)
   * @return 초기화 성공 여부
   */
  bool Initialize(const std::string &backend_url, int device_id,
                  uint32_t report_interval_ms = 10000);

  /**
   * @brief 서비스 시작
   */
  void Start();

  /**
   * @brief 서비스 중지
   */
  void Stop();

  /**
   * @brief 서비스 실행 중 여부
   */
  bool IsRunning() const { return is_running_; }

  /**
   * @brief 즉시 상태 보고 (타이머와 별도로)
   */
  bool ReportNow();

  /**
   * @brief 카메라 상태 설정
   */
  void SetCameraStatus(const std::string &status) { camera_status_ = status; }

  /**
   * @brief 마이크 상태 설정
   */
  void SetMicStatus(const std::string &status) { mic_status_ = status; }

  /**
   * @brief 보고 주기 변경 (런타임)
   * @param interval_ms 새 주기 (밀리초)
   * @return 성공 여부
   */
  bool SetInterval(uint32_t interval_ms);

  /**
   * @brief 현재 보고 주기 조회
   * @return 현재 주기 (밀리초)
   */
  uint32_t GetInterval() const { return report_interval_ms_; }

  /**
   * @brief 상태 보고 콜백 설정
   */
  using ReportCallback = std::function<void(bool success)>;
  void SetReportCallback(ReportCallback callback) {
    report_callback_ = callback;
  }

private:
  BackendClient backend_client_;
  uint32_t report_interval_ms_;
  bool is_running_;
  bool initialized_;

  // 컴포넌트 상태
  std::string camera_status_;
  std::string mic_status_;

  // FreeRTOS 타이머
  TimerHandle_t report_timer_;

  // 콜백
  ReportCallback report_callback_;

  /**
   * @brief 시스템 상태 수집
   */
  DeviceStatusData CollectStatus();

  /**
   * @brief 타이머 콜백 (static)
   */
  static void TimerCallback(TimerHandle_t timer);
};

#endif // STATUS_REPORTER_H
