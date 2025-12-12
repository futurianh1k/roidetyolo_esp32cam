#include "audio_codec.h"
#include "../pins.h"
#include "../config.h"
#include <esp_log.h>
#include <driver/i2s_std.h>

#define TAG "AudioCodec"

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

    // I2S 채널 그룹 생성
    i2s_chan_config_t chan_cfg = I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_AUTO, I2S_ROLE_MASTER);
    
    // TX 채널 (Speaker) 생성
    ret = i2s_new_channel(&chan_cfg, &tx_handle_, nullptr);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to create TX channel: %s", esp_err_to_name(ret));
        return false;
    }

    // RX 채널 (Microphone) 생성
    ret = i2s_new_channel(&chan_cfg, nullptr, &rx_handle_);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to create RX channel: %s", esp_err_to_name(ret));
        return false;
    }

    // TX 채널 설정
    i2s_std_config_t tx_std_cfg = {
        .clk_cfg = I2S_STD_CLK_DEFAULT_CONFIG(output_sample_rate_),
        .slot_cfg = I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_MONO),
        .gpio_cfg = {
            .mclk = I2S_GPIO_UNUSED,
            .bclk = (gpio_num_t)I2S_OUT_BCK,
            .ws = (gpio_num_t)I2S_OUT_WS,
            .dout = (gpio_num_t)I2S_OUT_DATA,
            .din = I2S_GPIO_UNUSED,
            .invert_flags = {
                .mclk_inv = false,
                .bclk_inv = false,
                .ws_inv = false,
            },
        },
    };
    ret = i2s_channel_init_std_mode(tx_handle_, &tx_std_cfg);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to init TX channel: %s", esp_err_to_name(ret));
        return false;
    }

    // RX 채널 설정
    i2s_std_config_t rx_std_cfg = {
        .clk_cfg = I2S_STD_CLK_DEFAULT_CONFIG(input_sample_rate_),
        .slot_cfg = I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_MONO),
        .gpio_cfg = {
            .mclk = I2S_GPIO_UNUSED,
            .bclk = (gpio_num_t)I2S_IN_BCK,
            .ws = (gpio_num_t)I2S_IN_WS,
            .dout = I2S_GPIO_UNUSED,
            .din = (gpio_num_t)I2S_IN_DATA,
            .invert_flags = {
                .mclk_inv = false,
                .bclk_inv = false,
                .ws_inv = false,
            },
        },
    };
    ret = i2s_channel_init_std_mode(rx_handle_, &rx_std_cfg);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to init RX channel: %s", esp_err_to_name(ret));
        return false;
    }

    ESP_LOGI(TAG, "Audio codec initialized");
    return true;
}

void AudioCodec::Start() {
    if (output_enabled_ && tx_handle_) {
        i2s_channel_enable(tx_handle_);
    }
    if (input_enabled_ && rx_handle_) {
        i2s_channel_enable(rx_handle_);
    }
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
    if (volume < 0) volume = 0;
    if (volume > 100) volume = 100;
    output_volume_ = volume;
    // TODO: 실제 볼륨 제어 구현 (AW88298 드라이버 필요)
}

void AudioCodec::SetInputGain(float gain) {
    input_gain_ = gain;
    // TODO: 실제 게인 제어 구현 (ES7210 드라이버 필요)
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

bool AudioCodec::OutputData(const std::vector<int16_t>& data) {
    if (!tx_handle_ || !output_enabled_) {
        return false;
    }

    size_t bytes_written = 0;
    esp_err_t ret = i2s_channel_write(tx_handle_, data.data(), data.size() * sizeof(int16_t), &bytes_written, portMAX_DELAY);
    
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to write audio data: %s", esp_err_to_name(ret));
        return false;
    }
    
    return bytes_written == data.size() * sizeof(int16_t);
}

bool AudioCodec::InputData(std::vector<int16_t>& data, size_t samples) {
    if (!rx_handle_ || !input_enabled_) {
        return false;
    }

    data.resize(samples);
    size_t bytes_read = 0;
    esp_err_t ret = i2s_channel_read(rx_handle_, data.data(), samples * sizeof(int16_t), &bytes_read, portMAX_DELAY);
    
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to read audio data: %s", esp_err_to_name(ret));
        return false;
    }
    
    return bytes_read == samples * sizeof(int16_t);
}

