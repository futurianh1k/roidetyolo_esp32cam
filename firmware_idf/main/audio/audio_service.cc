#include "audio_service.h"
#include "../config.h"
#include <esp_log.h>

#define TAG "AudioService"

#define AUDIO_QUEUE_SIZE 10
#define AUDIO_FRAME_SAMPLES 320  // 20ms @ 16kHz

struct AudioFrame {
    std::vector<int16_t> data;
};

AudioService::AudioService() {
}

AudioService::~AudioService() {
    Stop();
}

bool AudioService::Initialize(AudioCodec* codec) {
    if (!codec) {
        ESP_LOGE(TAG, "AudioCodec is null");
        return false;
    }
    
    codec_ = codec;
    
    // 큐 생성
    audio_input_queue_ = xQueueCreate(AUDIO_QUEUE_SIZE, sizeof(AudioFrame*));
    audio_output_queue_ = xQueueCreate(AUDIO_QUEUE_SIZE, sizeof(AudioFrame*));
    
    if (!audio_input_queue_ || !audio_output_queue_) {
        ESP_LOGE(TAG, "Failed to create audio queues");
        return false;
    }
    
    ESP_LOGI(TAG, "Audio service initialized");
    return true;
}

void AudioService::Start() {
    if (service_running_) {
        return;
    }
    
    service_running_ = true;
    
    // 오디오 입력 태스크 생성
    xTaskCreatePinnedToCore(
        AudioInputTask,
        "audio_input",
        4096,
        this,
        5,  // 우선순위
        &audio_input_task_handle_,
        1   // Core 1
    );
    
    // 오디오 출력 태스크 생성
    xTaskCreatePinnedToCore(
        AudioOutputTask,
        "audio_output",
        4096,
        this,
        4,  // 우선순위
        &audio_output_task_handle_,
        1   // Core 1
    );
    
    ESP_LOGI(TAG, "Audio service started");
}

void AudioService::Stop() {
    if (!service_running_) {
        return;
    }
    
    service_running_ = false;
    StopMicrophone();
    StopSpeaker();
    
    // 태스크 종료 대기
    if (audio_input_task_handle_) {
        vTaskDelete(audio_input_task_handle_);
        audio_input_task_handle_ = nullptr;
    }
    if (audio_output_task_handle_) {
        vTaskDelete(audio_output_task_handle_);
        audio_output_task_handle_ = nullptr;
    }
    
    // 큐 정리
    if (audio_input_queue_) {
        AudioFrame* frame = nullptr;
        while (xQueueReceive(audio_input_queue_, &frame, 0) == pdTRUE) {
            delete frame;
        }
        vQueueDelete(audio_input_queue_);
        audio_input_queue_ = nullptr;
    }
    
    if (audio_output_queue_) {
        AudioFrame* frame = nullptr;
        while (xQueueReceive(audio_output_queue_, &frame, 0) == pdTRUE) {
            delete frame;
        }
        vQueueDelete(audio_output_queue_);
        audio_output_queue_ = nullptr;
    }
    
    ESP_LOGI(TAG, "Audio service stopped");
}

void AudioService::StartMicrophone() {
    if (microphone_active_) {
        return;
    }
    
    if (codec_) {
        codec_->EnableInput(true);
        microphone_active_ = true;
        ESP_LOGI(TAG, "Microphone started");
    }
}

void AudioService::StopMicrophone() {
    if (!microphone_active_) {
        return;
    }
    
    if (codec_) {
        codec_->EnableInput(false);
        microphone_active_ = false;
        ESP_LOGI(TAG, "Microphone stopped");
    }
}

void AudioService::StartSpeaker() {
    if (speaker_active_) {
        return;
    }
    
    if (codec_) {
        codec_->EnableOutput(true);
        speaker_active_ = true;
        ESP_LOGI(TAG, "Speaker started");
    }
}

void AudioService::StopSpeaker() {
    if (!speaker_active_) {
        return;
    }
    
    if (codec_) {
        codec_->EnableOutput(false);
        speaker_active_ = false;
        ESP_LOGI(TAG, "Speaker stopped");
    }
}

bool AudioService::ReadPCM(std::vector<int16_t>& data, size_t samples) {
    if (!codec_ || !microphone_active_) {
        return false;
    }
    
    return codec_->InputData(data, samples);
}

bool AudioService::WritePCM(const std::vector<int16_t>& data) {
    if (!codec_ || !speaker_active_) {
        return false;
    }
    
    return codec_->OutputData(data);
}

void AudioService::SetVolume(int volume) {
    if (codec_) {
        codec_->SetOutputVolume(volume);
    }
}

void AudioService::AudioInputTask(void* arg) {
    AudioService* service = static_cast<AudioService*>(arg);
    service->AudioInputTaskImpl();
}

void AudioService::AudioInputTaskImpl() {
    std::vector<int16_t> buffer(AUDIO_FRAME_SAMPLES);
    
    while (service_running_) {
        if (microphone_active_ && codec_) {
            if (codec_->InputData(buffer, AUDIO_FRAME_SAMPLES)) {
                // 큐에 데이터 전송 (필요시)
                AudioFrame* frame = new AudioFrame();
                frame->data = buffer;
                
                if (xQueueSend(audio_input_queue_, &frame, 0) != pdTRUE) {
                    // 큐가 가득 찬 경우 프레임 삭제
                    delete frame;
                }
            }
        } else {
            vTaskDelay(pdMS_TO_TICKS(10));
        }
    }
    
    vTaskDelete(nullptr);
}

void AudioService::AudioOutputTask(void* arg) {
    AudioService* service = static_cast<AudioService*>(arg);
    service->AudioOutputTaskImpl();
}

void AudioService::AudioOutputTaskImpl() {
    AudioFrame* frame = nullptr;
    
    while (service_running_) {
        if (speaker_active_ && codec_) {
            if (xQueueReceive(audio_output_queue_, &frame, pdMS_TO_TICKS(100)) == pdTRUE) {
                if (frame) {
                    codec_->OutputData(frame->data);
                    delete frame;
                }
            }
        } else {
            vTaskDelay(pdMS_TO_TICKS(10));
        }
    }
    
    vTaskDelete(nullptr);
}

