#ifndef AUDIO_CODEC_H
#define AUDIO_CODEC_H

#include <driver/i2c_master.h>
#include <driver/i2s_std.h>
#include <freertos/FreeRTOS.h> // For portMAX_DELAY
#include <vector>

// esp_codec_dev (official audio codec framework)
extern "C" {
#include "esp_codec_dev.h"
#include "esp_codec_dev_defaults.h"
}

/**
 * AudioCodec - I2S 오디오 코덱 추상화
 *
 * ESP-IDF I2S 드라이버를 사용한 오디오 입출력
 */
class AudioCodec {
public:
  AudioCodec();
  virtual ~AudioCodec();

  // CoreS3는 스피커(AW88298) 제어를 위해 I2C 초기화/코덱 초기화가 필수.
  // PowerManager가 만든 I2C 버스 핸들을 주입받아 esp_codec_dev를 통해
  // 초기화한다.
  bool Initialize(i2c_master_bus_handle_t i2c_bus);
  void Start();
  void Stop();

  void SetOutputVolume(int volume);
  void SetInputGain(float gain);
  void EnableInput(bool enable);
  void EnableOutput(bool enable);

  bool OutputData(const std::vector<int16_t> &data);
  bool InputData(std::vector<int16_t> &data, size_t samples);

  inline int input_sample_rate() const { return input_sample_rate_; }
  inline int output_sample_rate() const { return output_sample_rate_; }
  inline int output_volume() const { return output_volume_; }
  inline bool input_enabled() const { return input_enabled_; }
  inline bool output_enabled() const { return output_enabled_; }

private:
  i2s_chan_handle_t tx_handle_ = nullptr; // Speaker
  i2s_chan_handle_t rx_handle_ = nullptr; // Microphone

  // esp_codec_dev handles (CoreS3: AW88298 speaker / ES7210 mic)
  i2c_master_bus_handle_t i2c_bus_handle_ = nullptr;
  const audio_codec_data_if_t *i2s_data_if_ = nullptr;
  esp_codec_dev_handle_t speaker_dev_ = nullptr;

  bool input_enabled_ = false;
  bool output_enabled_ = false;
  uint32_t input_sample_rate_ = 16000;
  uint32_t output_sample_rate_ = 16000;
  int output_volume_ = 70;
  float input_gain_ = 1.0f;
};

#endif // AUDIO_CODEC_H
