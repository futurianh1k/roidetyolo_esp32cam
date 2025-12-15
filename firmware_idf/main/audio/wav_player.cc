/**
 * @file wav_player.cc
 * @brief WAV 파일 재생 유틸리티 구현
 *
 * 참고자료:
 * - WAV 파일 포맷: http://soundfile.sapp.org/doc/WaveFormat/
 * - ESP-IDF SPIFFS:
 * https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/storage/spiffs.html
 */

#include "wav_player.h"
#include <cmath>
#include <cstring>
#include <esp_log.h>
#include <esp_spiffs.h>
#include <stdio.h>

#define TAG "WavPlayer"

// 오디오 출력 설정
#define OUTPUT_SAMPLE_RATE 16000
#define OUTPUT_CHUNK_SAMPLES 512

// 내장 알람음 정의 (주파수, 지속시간, 반복)
struct AlarmPattern {
  int frequency;
  int duration_ms;
  int pause_ms;
  int repeats;
};

static const AlarmPattern ALARM_BEEP = {1000, 100, 0, 1};
static const AlarmPattern ALARM_ALERT = {800, 200, 100, 3};
static const AlarmPattern ALARM_NOTIFICATION = {1200, 150, 50, 2};
static const AlarmPattern ALARM_EMERGENCY = {1500, 300, 200, 5};

WavPlayer::WavPlayer() {}

WavPlayer::~WavPlayer() { Stop(); }

bool WavPlayer::Initialize(AudioCodec *codec) {
  if (!codec) {
    ESP_LOGE(TAG, "AudioCodec is null");
    return false;
  }

  codec_ = codec;
  ESP_LOGI(TAG, "WAV player initialized");
  return true;
}

bool WavPlayer::ParseWavHeader(const uint8_t *data, size_t size,
                               WavHeader &header) {
  if (size < sizeof(WavHeader)) {
    ESP_LOGE(TAG, "Data too small for WAV header");
    return false;
  }

  memcpy(&header, data, sizeof(WavHeader));

  // RIFF 헤더 확인
  if (strncmp(header.riff, "RIFF", 4) != 0) {
    ESP_LOGE(TAG, "Invalid RIFF header");
    return false;
  }

  // WAVE 포맷 확인
  if (strncmp(header.wave, "WAVE", 4) != 0) {
    ESP_LOGE(TAG, "Invalid WAVE format");
    return false;
  }

  // PCM 포맷 확인
  if (header.audio_fmt != 1) {
    ESP_LOGE(TAG, "Only PCM format supported (got %d)", header.audio_fmt);
    return false;
  }

  ESP_LOGI(TAG, "WAV: %d Hz, %d ch, %d bits, %lu bytes", header.sample_rate,
           header.channels, header.bits_per_sample,
           (unsigned long)header.data_size);

  return true;
}

bool WavPlayer::PlayFile(const std::string &path) {
  if (!codec_) {
    ESP_LOGE(TAG, "Codec not initialized");
    return false;
  }

  FILE *file = fopen(path.c_str(), "rb");
  if (!file) {
    ESP_LOGE(TAG, "Failed to open file: %s", path.c_str());
    return false;
  }

  // 파일 크기 확인
  fseek(file, 0, SEEK_END);
  size_t file_size = ftell(file);
  fseek(file, 0, SEEK_SET);
  ESP_LOGI(TAG, "Opening WAV file: %s (%zu bytes)", path.c_str(), file_size);

  // WAV 헤더 읽기
  WavHeader header;
  if (fread(&header, 1, sizeof(header), file) != sizeof(header)) {
    ESP_LOGE(TAG, "Failed to read WAV header");
    fclose(file);
    return false;
  }

  // 헤더 파싱
  if (!ParseWavHeader(reinterpret_cast<uint8_t *>(&header), sizeof(header),
                      header)) {
    fclose(file);
    return false;
  }

  is_playing_ = true;
  // 출력 채널은 항상 활성화 상태로 유지 (Initialize에서 이미 활성화됨)

  // PCM 데이터 읽기 및 재생
  std::vector<int16_t> buffer(OUTPUT_CHUNK_SAMPLES);
  size_t bytes_to_read = OUTPUT_CHUNK_SAMPLES * sizeof(int16_t);

  while (is_playing_) {
    size_t bytes_read = fread(buffer.data(), 1, bytes_to_read, file);
    if (bytes_read == 0) {
      break; // EOF
    }

    size_t samples_read = bytes_read / sizeof(int16_t);

    // 모노로 변환 (스테레오인 경우)
    if (header.channels == 2) {
      for (size_t i = 0; i < samples_read / 2; i++) {
        buffer[i] = (buffer[i * 2] + buffer[i * 2 + 1]) / 2;
      }
      samples_read /= 2;
    }

    // 코덱으로 출력
    std::vector<int16_t> output_data(buffer.begin(),
                                     buffer.begin() + samples_read);
    codec_->OutputData(output_data);
  }

  fclose(file);
  // 출력 채널 비활성화 제거 - 항상 활성화 상태 유지
  is_playing_ = false;

  ESP_LOGI(TAG, "Finished playing: %s", path.c_str());
  return true;
}

bool WavPlayer::PlayMemory(const uint8_t *data, size_t size) {
  if (!codec_ || !data || size == 0) {
    ESP_LOGE(TAG, "Invalid parameters");
    return false;
  }

  WavHeader header;
  if (!ParseWavHeader(data, size, header)) {
    return false;
  }

  // PCM 데이터 시작 위치
  const int16_t *pcm_data =
      reinterpret_cast<const int16_t *>(data + sizeof(WavHeader));
  size_t total_samples = header.data_size / sizeof(int16_t);

  if (header.channels == 2) {
    total_samples /= 2;
  }

  return OutputPCM(pcm_data, total_samples, header.sample_rate,
                   header.channels);
}

bool WavPlayer::OutputPCM(const int16_t *pcm_data, size_t samples,
                          uint32_t sample_rate, uint16_t channels) {
  if (!codec_) {
    return false;
  }

  is_playing_ = true;
  // 출력 채널은 항상 활성화 상태로 유지 (Initialize에서 이미 활성화됨)

  std::vector<int16_t> buffer(OUTPUT_CHUNK_SAMPLES);
  size_t offset = 0;

  while (is_playing_ && offset < samples) {
    size_t chunk_samples =
        std::min(static_cast<size_t>(OUTPUT_CHUNK_SAMPLES), samples - offset);

    // 모노로 변환
    if (channels == 2) {
      for (size_t i = 0; i < chunk_samples; i++) {
        buffer[i] =
            (pcm_data[(offset + i) * 2] + pcm_data[(offset + i) * 2 + 1]) / 2;
      }
    } else {
      memcpy(buffer.data(), pcm_data + offset, chunk_samples * sizeof(int16_t));
    }

    std::vector<int16_t> output_data(buffer.begin(),
                                     buffer.begin() + chunk_samples);
    codec_->OutputData(output_data);

    offset += chunk_samples;
  }

  // 출력 채널 비활성화 제거 - 항상 활성화 상태 유지
  is_playing_ = false;

  return true;
}

bool WavPlayer::PlayAlarm(AlarmType type, int repeat) {
  AlarmPattern pattern;

  switch (type) {
  case AlarmType::kBeep:
    pattern = ALARM_BEEP;
    break;
  case AlarmType::kAlert:
    pattern = ALARM_ALERT;
    break;
  case AlarmType::kNotification:
    pattern = ALARM_NOTIFICATION;
    break;
  case AlarmType::kEmergency:
    pattern = ALARM_EMERGENCY;
    break;
  default:
    pattern = ALARM_BEEP;
  }

  ESP_LOGI(TAG, "Playing alarm: freq=%d, duration=%dms, repeats=%d",
           pattern.frequency, pattern.duration_ms, pattern.repeats * repeat);

  // 알람 재생 시작 플래그 설정
  is_playing_ = true;

  for (int r = 0; r < repeat && is_playing_; r++) {
    for (int i = 0; i < pattern.repeats && is_playing_; i++) {
      PlayBeep(pattern.frequency, pattern.duration_ms, 80);

      if (pattern.pause_ms > 0 && i < pattern.repeats - 1) {
        vTaskDelay(pdMS_TO_TICKS(pattern.pause_ms));
      }
    }

    if (r < repeat - 1) {
      vTaskDelay(pdMS_TO_TICKS(500)); // 반복 간 휴식
    }
  }

  return true;
}

void WavPlayer::GenerateSineWave(std::vector<int16_t> &buffer, int frequency,
                                 int sample_rate, int duration_ms, int volume) {
  size_t total_samples = (sample_rate * duration_ms) / 1000;
  buffer.resize(total_samples);

  double amplitude = (32767.0 * volume) / 100.0;
  double angular_freq = 2.0 * M_PI * frequency / sample_rate;

  for (size_t i = 0; i < total_samples; i++) {
    // 페이드 인/아웃 적용 (클릭 방지)
    double fade = 1.0;
    size_t fade_samples = sample_rate / 100; // 10ms 페이드

    if (i < fade_samples) {
      fade = static_cast<double>(i) / fade_samples;
    } else if (i > total_samples - fade_samples) {
      fade = static_cast<double>(total_samples - i) / fade_samples;
    }

    buffer[i] = static_cast<int16_t>(amplitude * fade * sin(angular_freq * i));
  }
}

bool WavPlayer::PlayBeep(int frequency, int duration_ms, int volume) {
  if (!codec_) {
    ESP_LOGE(TAG, "Codec not initialized");
    return false;
  }

  ESP_LOGI(TAG, "Playing beep: %d Hz, %d ms, vol=%d", frequency, duration_ms,
           volume);

  std::vector<int16_t> buffer;
  GenerateSineWave(buffer, frequency, OUTPUT_SAMPLE_RATE, duration_ms, volume);

  is_playing_ = true;
  // 출력 채널은 항상 활성화 상태로 유지 (Initialize에서 이미 활성화됨)
  // codec_->EnableOutput(true); 제거 - 중복 활성화 방지

  // 청크 단위로 출력
  size_t offset = 0;
  size_t success_count = 0;
  size_t fail_count = 0;

  while (is_playing_ && offset < buffer.size()) {
    size_t chunk = std::min(static_cast<size_t>(OUTPUT_CHUNK_SAMPLES),
                            buffer.size() - offset);

    std::vector<int16_t> chunk_data(buffer.begin() + offset,
                                    buffer.begin() + offset + chunk);

    if (codec_->OutputData(chunk_data)) {
      success_count++;
    } else {
      fail_count++;
      // 연속 실패 시 중단
      if (fail_count > 5) {
        ESP_LOGE(TAG, "Too many write failures, stopping playback");
        break;
      }
    }

    offset += chunk;
  }

  // 출력 채널 비활성화 제거 - 항상 활성화 상태 유지
  // codec_->EnableOutput(false);
  is_playing_ = false;

  ESP_LOGI(TAG, "Beep playback finished: %zu/%zu chunks", success_count,
           success_count + fail_count);
  return fail_count == 0;
}

void WavPlayer::Stop() {
  is_playing_ = false;
  // 출력 채널 비활성화 제거 - 항상 활성화 상태 유지
  // Stop()은 현재 재생만 중단하고 채널은 유지
}
