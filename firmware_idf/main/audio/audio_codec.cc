/**
 * @file audio_codec.cc
 * @brief Audio Codec for M5Stack CoreS3
 * @note Based on esp-bsp/m5stack_core_s3/m5stack_core_s3_idf5.c
 *
 * M5Stack CoreS3 Audio Hardware:
 *   - Speaker: AW88298 codec (I2C control, I2S data)
 *   - Microphone: ES7210 ADC (I2C control, I2S data)
 *   - Shared I2S bus: MCLK=GPIO0, BCK=GPIO34, WS=GPIO33
 *   - DOUT=GPIO13 (speaker), DIN=GPIO14 (microphone)
 */

#include "audio_codec.h"
#include "../config.h"
#include "../pins.h"
#include <driver/i2s_std.h>
#include <esp_log.h>
#include <freertos/task.h>

// esp_codec_dev (AW88298 speaker initialization)
extern "C" {
#include "esp_codec_dev_defaults.h"
}

#define TAG "AudioCodec"

// M5Stack CoreS3 I2S Pin Configuration
// Reference: esp-bsp/m5stack_core_s3/include/bsp/m5stack_core_s3.h
#define BSP_I2S_MCLK GPIO_NUM_0
#define BSP_I2S_SCLK GPIO_NUM_34 // BCK
#define BSP_I2S_LCLK GPIO_NUM_33 // WS (LRCK)
#define BSP_I2S_DOUT GPIO_NUM_13 // Speaker data out
#define BSP_I2S_DSIN GPIO_NUM_14 // Microphone data in

AudioCodec::AudioCodec() {
  input_sample_rate_ = I2S_SAMPLE_RATE;
  output_sample_rate_ = I2S_SAMPLE_RATE;
}

AudioCodec::~AudioCodec() {
  Stop();
  if (speaker_dev_) {
    esp_codec_dev_close(speaker_dev_);
    esp_codec_dev_delete(speaker_dev_);
    speaker_dev_ = nullptr;
  }
  if (tx_handle_) {
    i2s_channel_disable(tx_handle_);
    i2s_del_channel(tx_handle_);
  }
  if (rx_handle_) {
    i2s_channel_disable(rx_handle_);
    i2s_del_channel(rx_handle_);
  }
}

bool AudioCodec::Initialize(i2c_master_bus_handle_t i2c_bus) {
  esp_err_t ret;

  if (!i2c_bus) {
    ESP_LOGE(TAG,
             "I2C bus handle is null. PowerManager must initialize I2C first.");
    return false;
  }
  i2c_bus_handle_ = i2c_bus;

  // Check if already initialized
  if (speaker_dev_ && tx_handle_ && rx_handle_) {
    ESP_LOGI(TAG, "Audio codec already initialized");
    return true;
  }

  ESP_LOGI(TAG, "Initializing audio codec (esp_codec_dev + AW88298)...");

  // Create I2S channel - Duplex mode (TX + RX together)
  // Reference: esp-bsp/m5stack_core_s3/m5stack_core_s3_idf5.c
  i2s_chan_config_t chan_cfg =
      I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_0, I2S_ROLE_MASTER);
  chan_cfg.auto_clear = true; // Auto clear legacy data in DMA buffer

  ret = i2s_new_channel(&chan_cfg, &tx_handle_, &rx_handle_);
  if (ret != ESP_OK) {
    ESP_LOGE(TAG, "Failed to create I2S duplex channel: %s",
             esp_err_to_name(ret));
    return false;
  }
  ESP_LOGI(TAG, "I2S duplex channel created");

  // I2S Standard Configuration - SAME config for BOTH TX and RX
  // This is critical! BSP uses identical config for both channels
  i2s_std_config_t std_cfg = {
      .clk_cfg = I2S_STD_CLK_DEFAULT_CONFIG(output_sample_rate_),
      .slot_cfg = I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(I2S_DATA_BIT_WIDTH_16BIT,
                                                      I2S_SLOT_MODE_MONO),
      .gpio_cfg =
          {
              .mclk = BSP_I2S_MCLK,
              .bclk = BSP_I2S_SCLK,
              .ws = BSP_I2S_LCLK,
              .dout = BSP_I2S_DOUT, // Both dout AND din in same config!
              .din = BSP_I2S_DSIN,
              .invert_flags =
                  {
                      .mclk_inv = false,
                      .bclk_inv = false,
                      .ws_inv = false,
                  },
          },
  };

  // Initialize TX channel (Speaker)
  if (tx_handle_ != NULL) {
    ret = i2s_channel_init_std_mode(tx_handle_, &std_cfg);
    if (ret != ESP_OK) {
      ESP_LOGE(TAG, "Failed to init TX channel: %s", esp_err_to_name(ret));
      goto err;
    }
    ret = i2s_channel_enable(tx_handle_);
    if (ret != ESP_OK) {
      ESP_LOGE(TAG, "Failed to enable TX channel: %s", esp_err_to_name(ret));
      goto err;
    }
    output_enabled_ = true; // 플래그 업데이트
    ESP_LOGI(TAG, "TX channel (Speaker) initialized and enabled");
  }

  // Initialize RX channel (Microphone) - USE SAME CONFIG
  if (rx_handle_ != NULL) {
    ret = i2s_channel_init_std_mode(rx_handle_, &std_cfg);
    if (ret != ESP_OK) {
      ESP_LOGE(TAG, "Failed to init RX channel: %s", esp_err_to_name(ret));
      goto err;
    }
    ret = i2s_channel_enable(rx_handle_);
    if (ret != ESP_OK) {
      ESP_LOGE(TAG, "Failed to enable RX channel: %s", esp_err_to_name(ret));
      goto err;
    }
    input_enabled_ = true; // 플래그 업데이트
    ESP_LOGI(TAG, "RX channel (Microphone) initialized and enabled");
  }

  // Create I2S data interface for esp_codec_dev
  {
    audio_codec_i2s_cfg_t i2s_cfg = {
        .port = I2S_NUM_0,
        .rx_handle = rx_handle_,
        .tx_handle = tx_handle_,
    };
    i2s_data_if_ = audio_codec_new_i2s_data(&i2s_cfg);
    if (!i2s_data_if_) {
      ESP_LOGE(TAG, "Failed to create I2S data interface (esp_codec_dev)");
      goto err;
    }
  }

  // Initialize AW88298 speaker codec via esp_codec_dev
  {
    audio_codec_i2c_cfg_t i2c_cfg = {
        .port = I2C_NUM_1,
        .addr = AW88298_CODEC_DEFAULT_ADDR,
        .bus_handle = i2c_bus_handle_,
    };

    const audio_codec_ctrl_if_t *out_ctrl_if =
        audio_codec_new_i2c_ctrl(&i2c_cfg);
    if (!out_ctrl_if) {
      ESP_LOGE(TAG, "Failed to create I2C ctrl interface for AW88298");
      goto err;
    }

    const audio_codec_gpio_if_t *gpio_if = audio_codec_new_gpio();
    if (!gpio_if) {
      ESP_LOGE(TAG, "Failed to create GPIO interface for AW88298");
      goto err;
    }

    aw88298_codec_cfg_t aw88298_cfg = {
        .ctrl_if = out_ctrl_if,
        .gpio_if = gpio_if,
        .hw_gain =
            {
                .pa_gain = 15, // BSP default
            },
        // .reset_pin = -1,
    };

    const audio_codec_if_t *out_codec_if = aw88298_codec_new(&aw88298_cfg);
    if (!out_codec_if) {
      ESP_LOGE(TAG, "Failed to create AW88298 codec interface");
      goto err;
    }

    esp_codec_dev_cfg_t codec_dev_cfg = {
        .dev_type = ESP_CODEC_DEV_TYPE_OUT,
        .codec_if = out_codec_if,
        .data_if = i2s_data_if_,
    };

    speaker_dev_ = esp_codec_dev_new(&codec_dev_cfg);
    if (!speaker_dev_) {
      ESP_LOGE(TAG, "Failed to create speaker codec device");
      goto err;
    }

    esp_codec_dev_set_out_vol(speaker_dev_, output_volume_);

    // C++ designated initializer는 필드 선언 순서 제약이 있고(-Werror),
    // IDF 빌드 옵션에서는 경고가 에러로 승격될 수 있음.
    // 따라서 명시 할당 방식으로 초기화한다.
    esp_codec_dev_sample_info_t fs{};
    fs.bits_per_sample = 16;
    fs.channel = 1;
    fs.channel_mask = 0;
    fs.sample_rate = output_sample_rate_;
    fs.mclk_multiple = 0;
    ret = esp_codec_dev_open(speaker_dev_, &fs);
    if (ret != ESP_OK) {
      ESP_LOGE(TAG, "esp_codec_dev_open(speaker) failed: %s",
               esp_err_to_name(ret));
      goto err;
    }
  }

  ESP_LOGI(TAG, "Audio codec initialized successfully (AW88298 ready)");
  return true;

err:
  if (speaker_dev_) {
    esp_codec_dev_close(speaker_dev_);
    esp_codec_dev_delete(speaker_dev_);
    speaker_dev_ = nullptr;
  }
  if (tx_handle_) {
    i2s_del_channel(tx_handle_);
    tx_handle_ = nullptr;
  }
  if (rx_handle_) {
    i2s_del_channel(rx_handle_);
    rx_handle_ = nullptr;
  }
  return false;
}

void AudioCodec::Start() {
  // Channels are enabled in Initialize() following BSP pattern
  // This function is kept for API compatibility
  ESP_LOGD(TAG, "AudioCodec::Start() called (channels already enabled)");
}

void AudioCodec::Stop() {
  if (speaker_dev_) {
    esp_codec_dev_close(speaker_dev_);
  }
  if (tx_handle_) {
    i2s_channel_disable(tx_handle_);
  }
  if (rx_handle_) {
    i2s_channel_disable(rx_handle_);
  }
}

void AudioCodec::SetOutputVolume(int volume) {
  if (volume < 0)
    volume = 0;
  if (volume > 100)
    volume = 100;
  output_volume_ = volume;
  if (speaker_dev_) {
    esp_codec_dev_set_out_vol(speaker_dev_, output_volume_);
  }
}

void AudioCodec::SetInputGain(float gain) {
  input_gain_ = gain;
  // TODO: Implement actual gain control via ES7210 I2C
}

void AudioCodec::EnableInput(bool enable) {
  // 상태가 변경되지 않으면 무시 (중복 활성화 방지)
  if (input_enabled_ == enable) {
    return;
  }

  input_enabled_ = enable;
  if (rx_handle_) {
    esp_err_t ret;
    if (enable) {
      ret = i2s_channel_enable(rx_handle_);
    } else {
      ret = i2s_channel_disable(rx_handle_);
    }
    if (ret != ESP_OK && ret != ESP_ERR_INVALID_STATE) {
      ESP_LOGW(TAG, "Input channel %s failed: %s",
               enable ? "enable" : "disable", esp_err_to_name(ret));
    }
  }
}

void AudioCodec::EnableOutput(bool enable) {
  // 상태가 변경되지 않으면 무시 (중복 활성화 방지)
  if (output_enabled_ == enable) {
    return;
  }

  output_enabled_ = enable;
  if (tx_handle_) {
    esp_err_t ret;
    if (enable) {
      ret = i2s_channel_enable(tx_handle_);
    } else {
      ret = i2s_channel_disable(tx_handle_);
    }
    if (ret != ESP_OK && ret != ESP_ERR_INVALID_STATE) {
      ESP_LOGW(TAG, "Output channel %s failed: %s",
               enable ? "enable" : "disable", esp_err_to_name(ret));
    }
  }
}

bool AudioCodec::OutputData(const std::vector<int16_t> &data) {
  if (!speaker_dev_) {
    ESP_LOGE(TAG, "Speaker device not initialized (AW88298 not ready)");
    return false;
  }

  const uint8_t *buf = reinterpret_cast<const uint8_t *>(data.data());
  const int total_bytes = static_cast<int>(data.size() * sizeof(int16_t));

  int offset = 0;
  int zero_progress_retries = 0;

  // esp_codec_dev_write()는 부분 전송(partial write)이 발생할 수 있으므로
  // 전체 바이트를 모두 쓸 때까지 루프를 돌며 전송한다.
  while (offset < total_bytes) {
    const int remaining = total_bytes - offset;
    int written =
        esp_codec_dev_write(speaker_dev_, (void *)(buf + offset), remaining);

    if (written < 0) {
      ESP_LOGE(TAG, "esp_codec_dev_write failed: %d (offset=%d/%d)", written,
               offset, total_bytes);
      return false;
    }

    if (written == 0) {
      // 일시적으로 DMA/코덱 쪽이 막혀 0이 반환될 수 있음
      zero_progress_retries++;
      if (zero_progress_retries >= 10) {
        ESP_LOGE(TAG, "esp_codec_dev_write made no progress (offset=%d/%d)",
                 offset, total_bytes);
        return false;
      }
      vTaskDelay(pdMS_TO_TICKS(10));
      continue;
    }

    zero_progress_retries = 0;
    offset += written;

    // 긴 전송에서 watchdog/스케줄링에 유리하게 약간 양보
    if (remaining > 4096) {
      taskYIELD();
    }
  }

  return true;
}

bool AudioCodec::InputData(std::vector<int16_t> &data, size_t samples) {
  if (!rx_handle_) {
    return false;
  }

  data.resize(samples);
  size_t bytes_read = 0;
  // Use 100ms timeout instead of portMAX_DELAY to prevent blocking
  esp_err_t ret =
      i2s_channel_read(rx_handle_, data.data(), samples * sizeof(int16_t),
                       &bytes_read, pdMS_TO_TICKS(100));

  if (ret != ESP_OK) {
    ESP_LOGE(TAG, "Failed to read audio data: %s", esp_err_to_name(ret));
    return false;
  }

  return bytes_read == samples * sizeof(int16_t);
}
