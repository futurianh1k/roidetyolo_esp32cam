#ifndef DISPLAY_SERVICE_H
#define DISPLAY_SERVICE_H

#include <string>
#include <vector>

#include <esp_lcd_types.h>

extern "C" {
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
}

/**
 * DisplayService - 디스플레이 서비스
 *
 * 기능:
 * - 텍스트 표시
 * - 음성인식 중 표시 (마이크 아이콘 등)
 * - 상태 표시
 *
 * 참고: 실제 디스플레이 하드웨어는 나중에 구현
 * 현재는 로그만 출력
 */
class DisplayService {
public:
  DisplayService();
  ~DisplayService();

  /**
   * 초기화
   */
  bool Initialize();

  /**
   * 텍스트 표시
   * @param text 표시할 텍스트
   * @param duration_ms 표시 시간 (0이면 무한)
   */
  void ShowText(const std::string &text, int duration_ms = 0);

  /**
   * 음성인식 중 표시
   * @param is_listening true면 마이크 아이콘 표시
   */
  void ShowListening(bool is_listening);

  /**
   * 화면 클리어
   */
  void Clear();

  /**
   * 상태 표시 (온라인/오프라인 등)
   */
  void ShowStatus(const std::string &status,
                  const std::string &color = "white");

  void UpdateListeningAnimation();

  void ShowCameraFrameRGB565(const uint8_t *frame, int width, int height);
  void DisableCameraPreview();

private:
  // --- Low-level LCD helpers (ILI9341, RGB565) ---
  bool InitPanel();
  void DeinitPanel();
  void FillScreen(uint16_t color_rgb565);
  void DrawAsciiText(int x, int y, const std::string &text, uint16_t fg,
                     uint16_t bg, int scale = 2);
  void DrawEmoji(const std::string &emoji_id);

  bool IsAsciiRenderable(const std::string &text) const;
  void RenderUnicodeNotice(const std::string &text);
  void DrawListeningScreen(int level);
  void DrawMicShape(int center_x, int center_y, int radius, uint16_t color);
  std::vector<std::string> WrapText(const std::string &text,
                                    size_t max_chars) const;
  void DrawCenteredLines(const std::vector<std::string> &lines, uint16_t fg,
                         uint16_t bg);
  void DisableCameraPreviewLocked();
  void FillRect(int x1, int y1, int x2, int y2, uint16_t color);

  static uint16_t Rgb565(uint8_t r, uint8_t g, uint8_t b);

  bool initialized_ = false;
  std::string current_text_;
  bool is_listening_ = false;
  int listening_animation_frame_ = 0;
  int64_t last_animation_update_ = 0;
  bool camera_preview_active_ = false;

  // LCD handles
  esp_lcd_panel_io_handle_t io_ = nullptr;
  esp_lcd_panel_handle_t panel_ = nullptr;
  SemaphoreHandle_t render_mutex_ = nullptr;
  std::vector<uint16_t> camera_buffer_;
};

#endif // DISPLAY_SERVICE_H
