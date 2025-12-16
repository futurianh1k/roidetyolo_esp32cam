#ifndef CAMERA_SERVICE_H
#define CAMERA_SERVICE_H

#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <freertos/queue.h>
#include <functional>
#include <string>
#include <vector>

/**
 * CameraService - 카메라 서비스
 * 
 * FreeRTOS 태스크를 사용한 카메라 프레임 캡처 및 전송
 */
class CameraService {
public:
    CameraService();
    ~CameraService();

    bool Initialize();
    void Start();
    void Stop();
    
    void StartStream(const std::string& sink_url, const std::string& stream_mode, int frame_interval_ms);
    void StopStream();
    
    bool CaptureFrame(std::vector<uint8_t>& jpeg_data);
    
    bool IsStreaming() const { return streaming_active_; }
    void PauseStream();
    void SetPreviewCallbacks(
        std::function<void(const uint8_t*, int, int)> on_frame,
        std::function<void()> on_stop);

private:
    TaskHandle_t camera_task_handle_ = nullptr;
    bool initialized_ = false;
    bool streaming_active_ = false;
    bool preview_enabled_ = false;
    bool service_running_ = false;
    
    std::string sink_url_;
    std::string stream_mode_;
    int frame_interval_ms_ = 1000;
    
    static void CameraTask(void* arg);
    void CameraTaskImpl();
    
    bool SendFrameHTTP(const std::vector<uint8_t>& jpeg_data);
  void HandleCaptureFailure(const char* context);

  std::function<void(const uint8_t*, int, int)> preview_callback_;
  std::function<void()> preview_stop_callback_;

  int capture_failures_ = 0;
};

#endif // CAMERA_SERVICE_H

