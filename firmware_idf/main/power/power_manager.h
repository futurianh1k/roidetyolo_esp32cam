/**
 * @file power_manager.h
 * @brief M5Stack CoreS3 전원 관리 클래스
 *
 * AXP2101 PMU와 AW9523 GPIO Expander를 통한 전원 관리
 *
 * References:
 * - Tasmota M5CoreS3.be: https://github.com/arendst/Tasmota
 * - M5Unified Power_Class.cpp: https://github.com/m5stack/M5Unified
 * - ESP-BSP m5stack_core_s3.c
 */

#ifndef POWER_MANAGER_H
#define POWER_MANAGER_H

#include <driver/i2c_master.h>
#include <esp_err.h>

/**
 * @brief 전원 관리 기능 플래그
 */
enum class PowerFeature {
  kCamera,  ///< 카메라 전원 (ALDO3 + AW9523 P1.0)
  kDisplay, ///< 디스플레이 전원 (DLDO1 + AW9523 P1.1)
  kSpeaker, ///< 스피커 전원 (ALDO1, ALDO2, ALDO3)
  kSDCard,  ///< SD 카드 전원 (ALDO4)
  kAll      ///< 모든 기능
};

/**
 * @brief M5Stack CoreS3 전원 관리 클래스
 *
 * AXP2101 PMU와 AW9523 GPIO Expander를 초기화하고 제어합니다.
 */
class PowerManager {
public:
  PowerManager();
  ~PowerManager();

  // 복사 금지
  PowerManager(const PowerManager &) = delete;
  PowerManager &operator=(const PowerManager &) = delete;

  /**
   * @brief I2C 버스 및 전원 IC 초기화
   * @return 초기화 성공 여부
   */
  bool Initialize();

  /**
   * @brief 특정 기능의 전원 활성화
   * @param feature 활성화할 기능
   * @return 성공 여부
   */
  bool EnableFeature(PowerFeature feature);

  /**
   * @brief 특정 기능의 전원 비활성화
   * @param feature 비활성화할 기능
   * @return 성공 여부
   */
  bool DisableFeature(PowerFeature feature);

  /**
   * @brief 디스플레이 밝기 설정
   * @param percent 밝기 (0-100%)
   * @return 성공 여부
   */
  bool SetDisplayBrightness(int percent);

  /**
   * @brief 배터리 전압 읽기
   * @return 배터리 전압 (mV), 실패 시 -1
   */
  int GetBatteryVoltage();

  /**
   * @brief 배터리 잔량 읽기
   * @return 배터리 잔량 (0-100%), 실패 시 -1
   */
  int GetBatteryLevel();

  /**
   * @brief I2C 버스 핸들 반환 (다른 서비스에서 사용)
   * @return I2C 버스 핸들
   */
  i2c_master_bus_handle_t GetI2CBusHandle() const { return i2c_bus_handle_; }

  /**
   * @brief 초기화 상태 확인
   * @return 초기화 완료 여부
   */
  bool IsInitialized() const { return initialized_; }

private:
  // AXP2101 레지스터 정의
  static constexpr uint8_t AXP2101_ADDR = 0x34;
  static constexpr uint8_t AXP_REG_LDO_ONOFF = 0x90;  ///< LDOS ON/OFF control
  static constexpr uint8_t AXP_REG_ALDO1_VOLT = 0x92; ///< ALDO1 voltage
  static constexpr uint8_t AXP_REG_ALDO2_VOLT = 0x93; ///< ALDO2 voltage
  static constexpr uint8_t AXP_REG_ALDO3_VOLT =
      0x94; ///< ALDO3 voltage (Camera)
  static constexpr uint8_t AXP_REG_ALDO4_VOLT =
      0x95; ///< ALDO4 voltage (SD Card)
  static constexpr uint8_t AXP_REG_DLDO1_VOLT =
      0x99; ///< DLDO1 voltage (Display BL)
  static constexpr uint8_t AXP_REG_ADC_ENABLE = 0x30; ///< ADC enable
  static constexpr uint8_t AXP_REG_VBAT_H = 0x34; ///< Battery voltage high byte

  // AW9523 레지스터 정의
  static constexpr uint8_t AW9523_ADDR = 0x58;
  static constexpr uint8_t AW_REG_P0_OUTPUT = 0x02; ///< P0 output state
  static constexpr uint8_t AW_REG_P1_OUTPUT = 0x03; ///< P1 output state
  static constexpr uint8_t AW_REG_P0_CONFIG = 0x04; ///< P0 direction config
  static constexpr uint8_t AW_REG_P1_CONFIG = 0x05; ///< P1 direction config
  static constexpr uint8_t AW_REG_P0_MODE = 0x11;   ///< P0 mode (push-pull)
  static constexpr uint8_t AW_REG_RESET = 0x7F;     ///< Soft reset

  // AW9523 P1 핀 정의
  static constexpr uint8_t AW_P1_CAMERA = (1 << 0); ///< P1.0 = Camera enable
  static constexpr uint8_t AW_P1_LCD = (1 << 1);    ///< P1.1 = LCD enable
  static constexpr uint8_t AW_P1_DEFAULTS = 0xA0;   ///< 기본값 (bit 5, 7)

  // 내부 함수
  bool InitializeI2C();
  bool InitializeAXP2101();
  bool InitializeAW9523();
  bool WriteAXP2101(uint8_t reg, uint8_t value);
  bool ReadAXP2101(uint8_t reg, uint8_t *value);
  bool WriteAW9523(uint8_t reg, uint8_t value);
  bool ReadAW9523(uint8_t reg, uint8_t *value);
  bool UpdateAW9523Output(uint8_t reg, uint8_t mask, bool set);

  // 상태 변수
  bool initialized_ = false;
  i2c_master_bus_handle_t i2c_bus_handle_ = nullptr;
  i2c_master_dev_handle_t axp2101_handle_ = nullptr;
  i2c_master_dev_handle_t aw9523_handle_ = nullptr;

  // AW9523 현재 출력 상태 (캐시)
  uint8_t aw9523_p0_output_ = 0x06; ///< P0 기본값
  uint8_t aw9523_p1_output_ = 0xA0; ///< P1 기본값
};

#endif // POWER_MANAGER_H
