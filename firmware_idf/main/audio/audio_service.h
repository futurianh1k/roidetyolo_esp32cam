#ifndef AUDIO_SERVICE_H
#define AUDIO_SERVICE_H

#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <freertos/queue.h>
#include <memory>
#include <vector>
#include "audio_codec.h"

/**
 * AudioService - 오디오 서비스
 * 
 * FreeRTOS 태스크를 사용한 오디오 입출력 관리
 */
class AudioService {
public:
    AudioService();
    ~AudioService();

    bool Initialize(AudioCodec* codec);
    void Start();
    void Stop();

    void StartMicrophone();
    void StopMicrophone();
    void StartSpeaker();
    void StopSpeaker();

    // PCM 데이터 읽기 (마이크에서)
    bool ReadPCM(std::vector<int16_t>& data, size_t samples);

    // PCM 데이터 쓰기 (스피커로)
    bool WritePCM(const std::vector<int16_t>& data);

    void SetVolume(int volume);

private:
    AudioCodec* codec_ = nullptr;
    
    TaskHandle_t audio_input_task_handle_ = nullptr;
    TaskHandle_t audio_output_task_handle_ = nullptr;
    
    QueueHandle_t audio_input_queue_ = nullptr;
    QueueHandle_t audio_output_queue_ = nullptr;
    
    bool service_running_ = false;
    bool microphone_active_ = false;
    bool speaker_active_ = false;

    static void AudioInputTask(void* arg);
    static void AudioOutputTask(void* arg);
    
    void AudioInputTaskImpl();
    void AudioOutputTaskImpl();
};

#endif // AUDIO_SERVICE_H

