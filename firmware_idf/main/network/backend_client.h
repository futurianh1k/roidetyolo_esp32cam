/**
 * @file backend_client.h
 * @brief 백엔드 서버와 HTTP 통신을 담당하는 클라이언트
 *
 * 기능:
 * - 장비 상태 전송 (POST /devices/{id}/status)
 * - 장비 정보 업데이트
 *
 * 참고자료:
 * - ESP-IDF HTTP Client:
 * https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/protocols/esp_http_client.html
 */

#ifndef BACKEND_CLIENT_H
#define BACKEND_CLIENT_H

#include <functional>
#include <string>

/**
 * @brief 장비 상태 데이터 구조체
 */
struct DeviceStatusData {
  int battery_level;         // 배터리 잔량 (0-100, -1=미지원)
  int memory_usage;          // 힙 메모리 사용량 (bytes)
  int storage_usage;         // 스토리지 사용량 (bytes, -1=미지원)
  float temperature;         // CPU 온도 (°C)
  int cpu_usage;             // CPU 사용률 (0-100)
  std::string camera_status; // active, paused, stopped
  std::string mic_status;    // active, paused, stopped
};

/**
 * @brief 백엔드 HTTP 클라이언트 클래스
 */
class BackendClient {
public:
  BackendClient();
  ~BackendClient();

  /**
   * @brief 클라이언트 초기화
   * @param base_url 백엔드 서버 URL (예: http://10.10.11.18:8000)
   * @param device_id 장비 DB ID (숫자)
   * @return 초기화 성공 여부
   */
  bool Initialize(const std::string &base_url, int device_id);

  /**
   * @brief 장비 상태 전송
   * @param status 상태 데이터
   * @return 전송 성공 여부
   */
  bool SendDeviceStatus(const DeviceStatusData &status);

  /**
   * @brief 장비 정보 조회
   * @param out_device_info 조회된 정보 (JSON 문자열)
   * @return 조회 성공 여부
   */
  bool GetDeviceInfo(std::string &out_device_info);

  /**
   * @brief 장비 온라인 상태 업데이트 (Heartbeat)
   * @return 전송 성공 여부
   */
  bool SendHeartbeat();

  /**
   * @brief 연결 상태 확인
   * @return 마지막 요청 성공 여부
   */
  bool IsConnected() const { return is_connected_; }

  /**
   * @brief device_id 문자열로 DB ID 조회
   * @param device_id 장비 고유 식별자 문자열 (예: "core_s3_001")
   * @param out_db_id 조회된 DB ID 반환
   * @return 조회 성공 여부
   */
  bool LookupDeviceDbId(const std::string &device_id, int &out_db_id);

  /**
   * @brief 현재 설정된 device DB ID 반환
   */
  int GetDeviceId() const { return device_id_; }

  /**
   * @brief device DB ID 설정 (런타임에 변경 가능)
   */
  void SetDeviceId(int device_id) { device_id_ = device_id; }

  /**
   * @brief 콜백 타입 정의
   */
  using ResponseCallback =
      std::function<void(bool success, const std::string &response)>;

  /**
   * @brief 비동기 상태 전송
   */
  void SendDeviceStatusAsync(const DeviceStatusData &status,
                             ResponseCallback callback);

private:
  std::string base_url_;
  int device_id_;
  bool is_connected_;
  bool initialized_;

  /**
   * @brief HTTP POST 요청 전송
   */
  bool HttpPost(const std::string &path, const std::string &json_body,
                std::string &response);

  /**
   * @brief HTTP GET 요청 전송
   */
  bool HttpGet(const std::string &path, std::string &response);
};

#endif // BACKEND_CLIENT_H
