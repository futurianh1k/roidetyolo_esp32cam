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
  if (tx_handle_) {
    i2s_channel_disable(tx_handle_);
    i2s_del_channel(tx_handle_);
  }
  if (rx_handle_) {
    i2s_channel_disable(rx_handle_);
    i2s_del_channel(rx_handle_);
  }
}

bool AudioCodec::Initialize() {
  esp_err_t ret;

  // Check if already initialized
  if (tx_handle_ && rx_handle_) {
    ESP_LOGI(TAG, "Audio codec already initialized");
    return true;
  }

  ESP_LOGI(TAG, "Initializing audio codec (BSP-compatible)...");

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
    ESP_LOGI(TAG, "RX channel (Microphone) initialized and enabled");
  }

  ESP_LOGI(TAG, "Audio codec initialized successfully");
  return true;

err:
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
  // TODO: Implement actual volume control via AW88298 I2C
}

void AudioCodec::SetInputGain(float gain) {
  input_gain_ = gain;
  // TODO: Implement actual gain control via ES7210 I2C
}

void AudioCodec::EnableInput(bool enable) {
  input_enabled_ = enable;
  if (rx_handle_) {
    if (enable) {
      i2s_channel_enable(rx_handle_);
    } else {
      i2s_channel_disable(rx_handle_);
    }
  }
}

void AudioCodec::EnableOutput(bool enable) {
  output_enabled_ = enable;
  if (tx_handle_) {
    if (enable) {
      i2s_channel_enable(tx_handle_);
    } else {
      i2s_channel_disable(tx_handle_);
    }
  }
}

bool AudioCodec::OutputData(const std::vector<int16_t> &data) {
  if (!tx_handle_) {
    return false;
  }

  size_t bytes_written = 0;
  // Use 100ms timeout instead of portMAX_DELAY to prevent blocking
  esp_err_t ret =
      i2s_channel_write(tx_handle_, data.data(), data.size() * sizeof(int16_t),
                        &bytes_written, pdMS_TO_TICKS(100));

  if (ret != ESP_OK) {
    ESP_LOGE(TAG, "Failed to write audio data: %s", esp_err_to_name(ret));
    return false;
  }

  return bytes_written == data.size() * sizeof(int16_t);
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
