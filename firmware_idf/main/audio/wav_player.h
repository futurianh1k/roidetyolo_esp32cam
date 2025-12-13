/**
 * @file wav_player.h
 * @brief WAV 파일 재생 유틸리티
 *
 * 기능:
 * - WAV 헤더 파싱
 * - SPIFFS/메모리에서 WAV 재생
 * - 내장 알람음 재생
 *
 * 참고자료:
 * - WAV 파일 포맷: http://soundfile.sapp.org/doc/WaveFormat/
 */

#ifndef WAV_PLAYER_H
#define WAV_PLAYER_H

#include "audio_codec.h"
#include <cstdint>
#include <string>
#include <vector>

/**
 * @brief WAV 파일 헤더 구조체
 */
struct WavHeader {
  char riff[4];             // "RIFF"
  uint32_t file_size;       // 파일 크기 - 8
  char wave[4];             // "WAVE"
  char fmt[4];              // "fmt "
  uint32_t fmt_size;        // 포맷 청크 크기 (16 for PCM)
  uint16_t audio_fmt;       // 오디오 포맷 (1 = PCM)
  uint16_t channels;        // 채널 수
  uint32_t sample_rate;     // 샘플 레이트
  uint32_t byte_rate;       // 바이트 레이트
  uint16_t block_align;     // 블록 정렬
  uint16_t bits_per_sample; // 비트 깊이
  char data[4];             // "data"
  uint32_t data_size;       // 데이터 크기
} __attribute__((packed));

/**
 * @brief 내장 알람 타입
 */
enum class AlarmType {
  kBeep,         // 짧은 비프음
  kAlert,        // 경고음
  kNotification, // 알림음
  kEmergency,    // 긴급 알람
};

/**
 * @brief WAV 플레이어 클래스
 */
class WavPlayer {
public:
  WavPlayer();
  ~WavPlayer();

  /**
   * @brief 초기화
   * @param codec 오디오 코덱
   * @return 성공 여부
   */
  bool Initialize(AudioCodec *codec);

  /**
   * @brief SPIFFS에서 WAV 파일 재생
   * @param path 파일 경로 (예: "/spiffs/alarm.wav")
   * @return 성공 여부
   */
  bool PlayFile(const std::string &path);

  /**
   * @brief 메모리에서 WAV 데이터 재생
   * @param data WAV 데이터 포인터
   * @param size 데이터 크기
   * @return 성공 여부
   */
  bool PlayMemory(const uint8_t *data, size_t size);

  /**
   * @brief 내장 알람음 재생
   * @param type 알람 타입
   * @param repeat 반복 횟수 (기본 1)
   * @return 성공 여부
   */
  bool PlayAlarm(AlarmType type, int repeat = 1);

  /**
   * @brief 단순 비프음 생성 및 재생
   * @param frequency 주파수 (Hz)
   * @param duration_ms 지속 시간 (ms)
   * @param volume 볼륨 (0-100)
   * @return 성공 여부
   */
  bool PlayBeep(int frequency, int duration_ms, int volume = 80);

  /**
   * @brief 재생 중지
   */
  void Stop();

  /**
   * @brief 재생 중 여부
   */
  bool IsPlaying() const { return is_playing_; }

private:
  AudioCodec *codec_ = nullptr;
  bool is_playing_ = false;

  /**
   * @brief WAV 헤더 파싱
   */
  bool ParseWavHeader(const uint8_t *data, size_t size, WavHeader &header);

  /**
   * @brief PCM 데이터를 코덱으로 출력
   */
  bool OutputPCM(const int16_t *pcm_data, size_t samples, uint32_t sample_rate,
                 uint16_t channels);

  /**
   * @brief 사인파 생성 (비프음용)
   */
  void GenerateSineWave(std::vector<int16_t> &buffer, int frequency,
                        int sample_rate, int duration_ms, int volume);
};

#endif // WAV_PLAYER_H
