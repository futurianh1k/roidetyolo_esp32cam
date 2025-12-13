/**
 * @file power_manager.cc
 * @brief M5Stack CoreS3 전원 관리 구현
 *
 * References:
 * - Tasmota M5CoreS3.be: https://github.com/arendst/Tasmota
 * - M5Unified Power_Class.cpp: https://github.com/m5stack/M5Unified
 * - ESP-BSP m5stack_core_s3.c
 */

#include "power_manager.h"
#include <esp_log.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

#define TAG "PowerManager"

PowerManager::PowerManager() {}

PowerManager::~PowerManager() {
  // I2C 디바이스 핸들 해제는 ESP-IDF가 관리
  // 버스 해제는 하지 않음 (다른 서비스에서 사용 중일 수 있음)
}

bool PowerManager::Initialize() {
  if (initialized_) {
    ESP_LOGW(TAG, "Already initialized");
    return true;
  }

  ESP_LOGI(TAG, "Initializing power management...");

  // Step 1: I2C 버스 초기화
  if (!InitializeI2C()) {
    ESP_LOGE(TAG, "I2C initialization failed");
    return false;
  }

  // Step 2: AXP2101 PMU 초기화
  if (!InitializeAXP2101()) {
    ESP_LOGE(TAG, "AXP2101 initialization failed");
    return false;
  }

  // Step 3: AW9523 GPIO Expander 초기화
  if (!InitializeAW9523()) {
    ESP_LOGE(TAG, "AW9523 initialization failed");
    return false;
  }

  // 전원 안정화 대기
  vTaskDelay(pdMS_TO_TICKS(50));

  initialized_ = true;
  ESP_LOGI(TAG, "Power management initialized successfully");
  return true;
}

bool PowerManager::InitializeI2C() {
  // M5Stack CoreS3: I2C_NUM_1, GPIO11=SCL, GPIO12=SDA
  const i2c_master_bus_config_t i2c_config = {
      .i2c_port = I2C_NUM_1,
      .sda_io_num = GPIO_NUM_12,
      .scl_io_num = GPIO_NUM_11,
      .clk_source = I2C_CLK_SRC_DEFAULT,
      .glitch_ignore_cnt = 7,
      .flags =
          {
              .enable_internal_pullup = true,
          },
  };

  esp_err_t ret = i2c_new_master_bus(&i2c_config, &i2c_bus_handle_);
  if (ret == ESP_OK) {
    ESP_LOGI(TAG, "I2C master bus initialized on port 1");
    return true;
  } else if (ret == ESP_ERR_INVALID_STATE) {
    // 이미 초기화됨 - 기존 핸들 가져오기 시도
    ESP_LOGW(TAG, "I2C bus already initialized");
    // TODO: 기존 핸들 가져오기 구현
    return false;
  } else {
    ESP_LOGE(TAG, "I2C init failed: %s", esp_err_to_name(ret));
    return false;
  }
}

bool PowerManager::InitializeAXP2101() {
  const i2c_device_config_t config = {
      .dev_addr_length = I2C_ADDR_BIT_LEN_7,
      .device_address = AXP2101_ADDR,
      .scl_speed_hz = 400000,
  };

  esp_err_t ret =
      i2c_master_bus_add_device(i2c_bus_handle_, &config, &axp2101_handle_);
  if (ret != ESP_OK) {
    ESP_LOGE(TAG, "Failed to add AXP2101 device: %s", esp_err_to_name(ret));
    return false;
  }

  ESP_LOGI(TAG, "Configuring AXP2101 power rails...");

  // LDOS ON/OFF control - Enable all ALDOs and DLDOs
  // Reference: M5Unified Power_Class.cpp
  if (!WriteAXP2101(AXP_REG_LDO_ONOFF, 0xBF)) {
    return false;
  }

  // ALDO1 = 1.8V (for AW88298 speaker amp)
  // Formula: voltage = (reg_value + 5) * 100mV, so 1.8V = (18-5)*100mV = 0x0D
  if (!WriteAXP2101(AXP_REG_ALDO1_VOLT, 18 - 5)) {
    return false;
  }

  // ALDO2 = 3.3V (for ES7210 codec)
  if (!WriteAXP2101(AXP_REG_ALDO2_VOLT, 33 - 5)) {
    return false;
  }

  // ALDO3 = 3.3V (for Camera)
  if (!WriteAXP2101(AXP_REG_ALDO3_VOLT, 33 - 5)) {
    return false;
  }

  // ALDO4 = 3.3V (for TF card)
  if (!WriteAXP2101(AXP_REG_ALDO4_VOLT, 33 - 5)) {
    return false;
  }

  // Enable ADC for battery voltage measurement
  if (!WriteAXP2101(AXP_REG_ADC_ENABLE, 0x0F)) {
    return false;
  }

  ESP_LOGI(TAG, "AXP2101 configured: ALDO1=1.8V, ALDO2-4=3.3V");
  return true;
}

bool PowerManager::InitializeAW9523() {
  const i2c_device_config_t config = {
      .dev_addr_length = I2C_ADDR_BIT_LEN_7,
      .device_address = AW9523_ADDR,
      .scl_speed_hz = 400000,
  };

  esp_err_t ret =
      i2c_master_bus_add_device(i2c_bus_handle_, &config, &aw9523_handle_);
  if (ret != ESP_OK) {
    ESP_LOGE(TAG, "Failed to add AW9523 device: %s", esp_err_to_name(ret));
    return false;
  }

  ESP_LOGI(TAG, "Configuring AW9523 GPIO expander...");

  // Soft reset
  if (!WriteAW9523(AW_REG_RESET, 0x00)) {
    return false;
  }
  vTaskDelay(pdMS_TO_TICKS(10));

  // Set P0 and P1 as output (0 = output)
  if (!WriteAW9523(AW_REG_P0_CONFIG, 0x00)) {
    return false;
  }
  if (!WriteAW9523(AW_REG_P1_CONFIG, 0x00)) {
    return false;
  }

  // Set P0 to push-pull mode
  if (!WriteAW9523(AW_REG_P0_MODE, 0x10)) {
    return false;
  }

  // Set initial P0 output (speaker codec enable)
  aw9523_p0_output_ = 0x06;
  if (!WriteAW9523(AW_REG_P0_OUTPUT, aw9523_p0_output_)) {
    return false;
  }

  // Set initial P1 output (defaults only, camera/LCD disabled)
  aw9523_p1_output_ = AW_P1_DEFAULTS;
  if (!WriteAW9523(AW_REG_P1_OUTPUT, aw9523_p1_output_)) {
    return false;
  }

  ESP_LOGI(TAG, "AW9523 configured");
  return true;
}

bool PowerManager::EnableFeature(PowerFeature feature) {
  if (!initialized_) {
    ESP_LOGE(TAG, "Not initialized");
    return false;
  }

  bool success = true;

  switch (feature) {
  case PowerFeature::kCamera:
    // Enable camera via AW9523 P1.0
    success = UpdateAW9523Output(AW_REG_P1_OUTPUT, AW_P1_CAMERA, true);
    if (success) {
      ESP_LOGI(TAG, "Camera power enabled");
    }
    break;

  case PowerFeature::kDisplay:
    // Enable LCD via AW9523 P1.1
    success = UpdateAW9523Output(AW_REG_P1_OUTPUT, AW_P1_LCD, true);
    if (success) {
      // Set DLDO1 voltage for backlight (3.0V)
      WriteAXP2101(AXP_REG_DLDO1_VOLT, 0b00011000);
      ESP_LOGI(TAG, "Display power enabled");
    }
    break;

  case PowerFeature::kSpeaker:
    // Speaker uses ALDO1, ALDO2, ALDO3 (already configured in init)
    // Enable speaker amp via AW9523 P0.2
    success = UpdateAW9523Output(AW_REG_P0_OUTPUT, (1 << 2), true);
    if (success) {
      ESP_LOGI(TAG, "Speaker power enabled");
    }
    break;

  case PowerFeature::kSDCard:
    // SD card uses ALDO4 (already configured in init)
    // Enable via AW9523 P0.4
    success = UpdateAW9523Output(AW_REG_P0_OUTPUT, (1 << 4), true);
    if (success) {
      ESP_LOGI(TAG, "SD card power enabled");
    }
    break;

  case PowerFeature::kAll:
    success = EnableFeature(PowerFeature::kCamera) &&
              EnableFeature(PowerFeature::kDisplay) &&
              EnableFeature(PowerFeature::kSpeaker) &&
              EnableFeature(PowerFeature::kSDCard);
    break;
  }

  return success;
}

bool PowerManager::DisableFeature(PowerFeature feature) {
  if (!initialized_) {
    ESP_LOGE(TAG, "Not initialized");
    return false;
  }

  bool success = true;

  switch (feature) {
  case PowerFeature::kCamera:
    success = UpdateAW9523Output(AW_REG_P1_OUTPUT, AW_P1_CAMERA, false);
    if (success) {
      ESP_LOGI(TAG, "Camera power disabled");
    }
    break;

  case PowerFeature::kDisplay:
    success = UpdateAW9523Output(AW_REG_P1_OUTPUT, AW_P1_LCD, false);
    if (success) {
      ESP_LOGI(TAG, "Display power disabled");
    }
    break;

  case PowerFeature::kSpeaker:
    success = UpdateAW9523Output(AW_REG_P0_OUTPUT, (1 << 2), false);
    if (success) {
      ESP_LOGI(TAG, "Speaker power disabled");
    }
    break;

  case PowerFeature::kSDCard:
    success = UpdateAW9523Output(AW_REG_P0_OUTPUT, (1 << 4), false);
    if (success) {
      ESP_LOGI(TAG, "SD card power disabled");
    }
    break;

  case PowerFeature::kAll:
    success = DisableFeature(PowerFeature::kCamera) &&
              DisableFeature(PowerFeature::kDisplay) &&
              DisableFeature(PowerFeature::kSpeaker) &&
              DisableFeature(PowerFeature::kSDCard);
    break;
  }

  return success;
}

bool PowerManager::SetDisplayBrightness(int percent) {
  if (!initialized_) {
    return false;
  }

  // Clamp to valid range
  if (percent < 0)
    percent = 0;
  if (percent > 100)
    percent = 100;

  // Map 0-100% to DLDO1 voltage range (2.5V - 3.3V)
  // Register value: voltage = (reg + 5) * 100mV
  // 2.5V = 25, 3.3V = 33, so reg = 20-28
  uint8_t reg_value = 20 + (percent * 8 / 100);

  if (!WriteAXP2101(AXP_REG_DLDO1_VOLT, reg_value)) {
    return false;
  }

  ESP_LOGD(TAG, "Display brightness set to %d%%", percent);
  return true;
}

int PowerManager::GetBatteryVoltage() {
  if (!initialized_) {
    return -1;
  }

  // TODO: Implement battery voltage reading from AXP2101
  // This requires reading ADC registers
  return -1;
}

int PowerManager::GetBatteryLevel() {
  int voltage = GetBatteryVoltage();
  if (voltage < 0) {
    return -1;
  }

  // Estimate battery level from voltage
  // Li-Ion: 3.0V = 0%, 4.2V = 100%
  int level = (voltage - 3000) * 100 / 1200;
  if (level < 0)
    level = 0;
  if (level > 100)
    level = 100;

  return level;
}

bool PowerManager::WriteAXP2101(uint8_t reg, uint8_t value) {
  uint8_t data[2] = {reg, value};
  esp_err_t ret =
      i2c_master_transmit(axp2101_handle_, data, sizeof(data), 1000);
  if (ret != ESP_OK) {
    ESP_LOGE(TAG, "AXP2101 write failed (reg=0x%02X): %s", reg,
             esp_err_to_name(ret));
    return false;
  }
  return true;
}

bool PowerManager::ReadAXP2101(uint8_t reg, uint8_t *value) {
  esp_err_t ret =
      i2c_master_transmit_receive(axp2101_handle_, &reg, 1, value, 1, 1000);
  if (ret != ESP_OK) {
    ESP_LOGE(TAG, "AXP2101 read failed (reg=0x%02X): %s", reg,
             esp_err_to_name(ret));
    return false;
  }
  return true;
}

bool PowerManager::WriteAW9523(uint8_t reg, uint8_t value) {
  uint8_t data[2] = {reg, value};
  esp_err_t ret = i2c_master_transmit(aw9523_handle_, data, sizeof(data), 1000);
  if (ret != ESP_OK) {
    ESP_LOGE(TAG, "AW9523 write failed (reg=0x%02X): %s", reg,
             esp_err_to_name(ret));
    return false;
  }
  return true;
}

bool PowerManager::ReadAW9523(uint8_t reg, uint8_t *value) {
  esp_err_t ret =
      i2c_master_transmit_receive(aw9523_handle_, &reg, 1, value, 1, 1000);
  if (ret != ESP_OK) {
    ESP_LOGE(TAG, "AW9523 read failed (reg=0x%02X): %s", reg,
             esp_err_to_name(ret));
    return false;
  }
  return true;
}

bool PowerManager::UpdateAW9523Output(uint8_t reg, uint8_t mask, bool set) {
  uint8_t *cache =
      (reg == AW_REG_P0_OUTPUT) ? &aw9523_p0_output_ : &aw9523_p1_output_;

  if (set) {
    *cache |= mask;
  } else {
    *cache &= ~mask;
  }

  return WriteAW9523(reg, *cache);
}
