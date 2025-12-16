#include "display_service.h"
#include <algorithm>
#include <cmath>
#include <cctype>
#include <cstddef>
#include <cstring>
#include <sstream>
#include <esp_log.h>
#include <esp_timer.h>
#include <string_view>

#include <driver/gpio.h>
#include <driver/spi_master.h>
#include <freertos/task.h>

#include <esp_lcd_ili9341.h>
#include <esp_lcd_panel_io.h>
#include <esp_lcd_panel_ops.h>
#include <esp_lcd_panel_vendor.h>

// NOTE:
// We intentionally do NOT use the BSP display init path here.
// The BSP's bsp_display_new() toggles AW9523 output defaults which can disable
// the speaker amp enable (AW9523 P0.2) and cause audio regressions.

#define TAG "DisplayService"
#define LISTENING_ANIMATION_INTERVAL_MS 500 // 0.5초마다 애니메이션 업데이트

// CoreS3 LCD (ILI9341) - Reference: esp-bsp m5stack_core_s3.h
static constexpr int kLcdHRes = 320;
static constexpr int kLcdVRes = 240;
static constexpr spi_host_device_t kLcdSpiHost = SPI3_HOST;
static constexpr int kPinMosi = 37;
static constexpr int kPinSclk = 36;
static constexpr int kPinMiso = -1; // NC (avoid conflicts)
static constexpr int kPinCs = 3;
static constexpr int kPinDc = 35;
static constexpr int kPinRst = -1; // NC
static constexpr int kPixelClockHz = 40 * 1000 * 1000;

// BSP_LCD_BIGENDIAN=1 (CoreS3). Direct draw_bitmap needs swapped bytes.
static constexpr bool kSwapRgb565Bytes = true;
static inline uint16_t Swap16(uint16_t v) {
  return (uint16_t)((v << 8) | (v >> 8));
}

namespace {
class DisplayLock {
public:
  explicit DisplayLock(SemaphoreHandle_t mutex) : mutex_(mutex) {
    if (mutex_) {
      xSemaphoreTakeRecursive(mutex_, portMAX_DELAY);
    }
  }
  ~DisplayLock() {
    if (mutex_) {
      xSemaphoreGiveRecursive(mutex_);
    }
  }

private:
  SemaphoreHandle_t mutex_;
};
} // namespace

// Minimal 8x8 glyphs for digits/letters (unknown -> '?')
// Source: derived from classic 8x8 bitmap font patterns (public domain style).
static const uint8_t *GetGlyph(char c) {
  // 8 bytes per glyph, MSB->LSB
  static const uint8_t kSpace[8] = {0, 0, 0, 0, 0, 0, 0, 0};
  static const uint8_t kQmark[8] = {0x3C, 0x42, 0x02, 0x0C,
                                    0x10, 0x00, 0x10, 0x00};
  static const uint8_t kDot[8] = {0, 0, 0, 0, 0, 0, 0x18, 0x18};
  static const uint8_t kDash[8] = {0, 0, 0, 0x7E, 0, 0, 0, 0};
  static const uint8_t kUnd[8] = {0, 0, 0, 0, 0, 0, 0, 0x7E};

  static const uint8_t kDigits[10][8] = {
      {0x3C, 0x42, 0x46, 0x4A, 0x52, 0x62, 0x42, 0x3C}, // 0
      {0x10, 0x30, 0x10, 0x10, 0x10, 0x10, 0x10, 0x38}, // 1
      {0x3C, 0x42, 0x02, 0x0C, 0x30, 0x40, 0x40, 0x7E}, // 2
      {0x3C, 0x42, 0x02, 0x1C, 0x02, 0x02, 0x42, 0x3C}, // 3
      {0x08, 0x18, 0x28, 0x48, 0x7E, 0x08, 0x08, 0x08}, // 4
      {0x7E, 0x40, 0x7C, 0x02, 0x02, 0x02, 0x42, 0x3C}, // 5
      {0x1C, 0x20, 0x40, 0x7C, 0x42, 0x42, 0x42, 0x3C}, // 6
      {0x7E, 0x02, 0x04, 0x08, 0x10, 0x20, 0x20, 0x20}, // 7
      {0x3C, 0x42, 0x42, 0x3C, 0x42, 0x42, 0x42, 0x3C}, // 8
      {0x3C, 0x42, 0x42, 0x42, 0x3E, 0x02, 0x04, 0x38}, // 9
  };

  static const uint8_t kUpper[26][8] = {
      {0x18, 0x24, 0x42, 0x42, 0x7E, 0x42, 0x42, 0x42}, // A
      {0x7C, 0x42, 0x42, 0x7C, 0x42, 0x42, 0x42, 0x7C}, // B
      {0x3C, 0x42, 0x40, 0x40, 0x40, 0x40, 0x42, 0x3C}, // C
      {0x78, 0x44, 0x42, 0x42, 0x42, 0x42, 0x44, 0x78}, // D
      {0x7E, 0x40, 0x40, 0x7C, 0x40, 0x40, 0x40, 0x7E}, // E
      {0x7E, 0x40, 0x40, 0x7C, 0x40, 0x40, 0x40, 0x40}, // F
      {0x3C, 0x42, 0x40, 0x40, 0x4E, 0x42, 0x42, 0x3C}, // G
      {0x42, 0x42, 0x42, 0x7E, 0x42, 0x42, 0x42, 0x42}, // H
      {0x3C, 0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x3C}, // I
      {0x1E, 0x04, 0x04, 0x04, 0x04, 0x44, 0x44, 0x38}, // J
      {0x42, 0x44, 0x48, 0x70, 0x48, 0x44, 0x42, 0x42}, // K
      {0x40, 0x40, 0x40, 0x40, 0x40, 0x40, 0x40, 0x7E}, // L
      {0x42, 0x66, 0x5A, 0x5A, 0x42, 0x42, 0x42, 0x42}, // M
      {0x42, 0x62, 0x52, 0x4A, 0x46, 0x42, 0x42, 0x42}, // N
      {0x3C, 0x42, 0x42, 0x42, 0x42, 0x42, 0x42, 0x3C}, // O
      {0x7C, 0x42, 0x42, 0x7C, 0x40, 0x40, 0x40, 0x40}, // P
      {0x3C, 0x42, 0x42, 0x42, 0x42, 0x4A, 0x44, 0x3A}, // Q
      {0x7C, 0x42, 0x42, 0x7C, 0x48, 0x44, 0x42, 0x42}, // R
      {0x3C, 0x42, 0x40, 0x3C, 0x02, 0x02, 0x42, 0x3C}, // S
      {0x7E, 0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x10}, // T
      {0x42, 0x42, 0x42, 0x42, 0x42, 0x42, 0x42, 0x3C}, // U
      {0x42, 0x42, 0x42, 0x42, 0x42, 0x24, 0x24, 0x18}, // V
      {0x42, 0x42, 0x42, 0x42, 0x5A, 0x5A, 0x66, 0x42}, // W
      {0x42, 0x42, 0x24, 0x18, 0x18, 0x24, 0x42, 0x42}, // X
      {0x42, 0x42, 0x24, 0x18, 0x10, 0x10, 0x10, 0x10}, // Y
      {0x7E, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x7E}, // Z
  };

  if (c == ' ')
    return kSpace;
  if (c == '.')
    return kDot;
  if (c == '-')
    return kDash;
  if (c == '_')
    return kUnd;
  if (c >= '0' && c <= '9')
    return kDigits[c - '0'];
  if (c >= 'A' && c <= 'Z')
    return kUpper[c - 'A'];
  if (c >= 'a' && c <= 'z')
    return kUpper[c - 'a'];
  return kQmark;
}

DisplayService::DisplayService() {
  initialized_ = false;
  is_listening_ = false;
  listening_animation_frame_ = 0;
  last_animation_update_ = 0;
  camera_preview_active_ = false;
  render_mutex_ = xSemaphoreCreateRecursiveMutex();
}

DisplayService::~DisplayService() {
  DeinitPanel();
  if (render_mutex_) {
    vSemaphoreDelete(render_mutex_);
    render_mutex_ = nullptr;
  }
}

bool DisplayService::Initialize() {
  if (initialized_) {
    return true;
  }

  if (!render_mutex_) {
    render_mutex_ = xSemaphoreCreateRecursiveMutex();
  }

  if (!InitPanel()) {
    ESP_LOGE(TAG, "Display panel init failed");
    initialized_ = false;
    return false;
  }

  {
    DisplayLock lock(render_mutex_);
    FillScreen(Rgb565(0, 0, 0));
  }

  ESP_LOGI(TAG, "Display service initialized");
  initialized_ = true;
  return true;
}

void DisplayService::ShowText(const std::string &text, int duration_ms) {
  if (!initialized_) {
    return;
  }

  DisplayLock lock(render_mutex_);
  current_text_ = text;
  ESP_LOGI(TAG, "Display: %s", text.c_str());

  // 앱에서 show_emoji는 emoji_id("heart","smile")를 ShowText로 넘김.
  if (text == "heart" || text == "smile" || text == "thumbs_up" ||
      text == "warning" || text == "fire" || text == "star") {
    DisableCameraPreviewLocked();
    DrawEmoji(text);
    return;
  }

  if (!IsAsciiRenderable(text)) {
    ESP_LOGW(TAG,
             "Non-ASCII text requested (length=%zu). UTF-8 rendering is not "
             "enabled yet.",
             text.size());
    RenderUnicodeNotice(text);
    return;
  }

  DisableCameraPreviewLocked();
  FillScreen(Rgb565(0, 0, 0));
  auto lines = WrapText(text, 18);
  if (lines.empty()) {
    lines.push_back(text.substr(0, 18));
  }
  DrawCenteredLines(lines, Rgb565(255, 255, 255), Rgb565(0, 0, 0));

  (void)duration_ms;
}

void DisplayService::ShowListening(bool is_listening) {
  if (!initialized_) {
    return;
  }

  DisplayLock lock(render_mutex_);
  is_listening_ = is_listening;
  listening_animation_frame_ = 0;
  last_animation_update_ = 0;

  if (is_listening) {
    ESP_LOGI(TAG, "Display: 🎤 음성인식 중...");
    DisableCameraPreviewLocked();
    DrawListeningScreen(listening_animation_frame_);
  } else {
    ESP_LOGI(TAG, "Display: 음성인식 종료");
    FillScreen(Rgb565(0, 0, 0));
  }
}

void DisplayService::UpdateListeningAnimation() {
  if (!initialized_ || !is_listening_) {
    return;
  }

  int64_t now = esp_timer_get_time() / 1000; // milliseconds
  if (now - last_animation_update_ < LISTENING_ANIMATION_INTERVAL_MS) {
    return;
  }

  last_animation_update_ = now;
  listening_animation_frame_ = (listening_animation_frame_ + 1) % 4;
  DisplayLock lock(render_mutex_);
  DrawListeningScreen(listening_animation_frame_);
}

void DisplayService::Clear() {
  if (!initialized_) {
    return;
  }

  DisplayLock lock(render_mutex_);
  current_text_.clear();
  is_listening_ = false;
  camera_preview_active_ = false;
  ESP_LOGI(TAG, "Display: Cleared");

  FillScreen(Rgb565(0, 0, 0));
}

void DisplayService::ShowStatus(const std::string &status,
                                const std::string &color) {
  if (!initialized_) {
    return;
  }

  DisplayLock lock(render_mutex_);
  ESP_LOGI(TAG, "Display Status: %s (color: %s)", status.c_str(),
           color.c_str());
  if (!IsAsciiRenderable(status)) {
    RenderUnicodeNotice(status);
    return;
  }

  uint16_t fg = Rgb565(255, 255, 0);
  std::string lower = color;
  std::transform(lower.begin(), lower.end(), lower.begin(),
                 [](unsigned char ch) { return static_cast<char>(std::tolower(ch)); });
  if (lower == "red") {
    fg = Rgb565(255, 0, 0);
  } else if (lower == "green") {
    fg = Rgb565(0, 255, 0);
  } else if (lower == "blue") {
    fg = Rgb565(0, 128, 255);
  } else if (lower == "white") {
    fg = Rgb565(255, 255, 255);
  } else if (lower == "yellow") {
    fg = Rgb565(255, 255, 0);
  }

  const int bar_height = 24;
  FillRect(0, 0, kLcdHRes, bar_height, Rgb565(0, 0, 0));
  DrawAsciiText(8, 4, status, fg, Rgb565(0, 0, 0), 2);
}

uint16_t DisplayService::Rgb565(uint8_t r, uint8_t g, uint8_t b) {
  return (uint16_t)(((r & 0xF8) << 8) | ((g & 0xFC) << 3) | ((b & 0xF8) >> 3));
}

bool DisplayService::InitPanel() {
  if (panel_ && io_) {
    return true;
  }

  // SPI bus init (safe to call twice: ESP_ERR_INVALID_STATE means already
  // inited)
  spi_bus_config_t buscfg = {};
  buscfg.sclk_io_num = (gpio_num_t)kPinSclk;
  buscfg.mosi_io_num = (gpio_num_t)kPinMosi;
  buscfg.miso_io_num = (gpio_num_t)kPinMiso;
  buscfg.quadwp_io_num = GPIO_NUM_NC;
  buscfg.quadhd_io_num = GPIO_NUM_NC;
  buscfg.max_transfer_sz = kLcdHRes * 40 * sizeof(uint16_t);

  esp_err_t ret = spi_bus_initialize(kLcdSpiHost, &buscfg, SPI_DMA_CH_AUTO);
  if (ret != ESP_OK && ret != ESP_ERR_INVALID_STATE) {
    ESP_LOGE(TAG, "spi_bus_initialize failed: %s", esp_err_to_name(ret));
    return false;
  }

  // Panel IO
  esp_lcd_panel_io_spi_config_t io_config = {};
  io_config.dc_gpio_num = (gpio_num_t)kPinDc;
  io_config.cs_gpio_num = (gpio_num_t)kPinCs;
  io_config.pclk_hz = kPixelClockHz;
  io_config.lcd_cmd_bits = 8;
  io_config.lcd_param_bits = 8;
  io_config.spi_mode = 0;
  io_config.trans_queue_depth = 10;

  ret = esp_lcd_new_panel_io_spi((esp_lcd_spi_bus_handle_t)kLcdSpiHost,
                                 &io_config, &io_);
  if (ret != ESP_OK) {
    ESP_LOGE(TAG, "esp_lcd_new_panel_io_spi failed: %s", esp_err_to_name(ret));
    return false;
  }

  // Panel driver
  esp_lcd_panel_dev_config_t panel_config = {};
  panel_config.reset_gpio_num = (gpio_num_t)kPinRst;
  panel_config.rgb_ele_order = LCD_RGB_ELEMENT_ORDER_BGR;
  panel_config.bits_per_pixel = 16;

  ret = esp_lcd_new_panel_ili9341(io_, &panel_config, &panel_);
  if (ret != ESP_OK) {
    ESP_LOGE(TAG, "esp_lcd_new_panel_ili9341 failed: %s", esp_err_to_name(ret));
    return false;
  }

  esp_lcd_panel_reset(panel_);
  esp_lcd_panel_init(panel_);
  // Match BSP behavior (CoreS3 panel usually needs invert)
  esp_lcd_panel_invert_color(panel_, true);
  esp_lcd_panel_disp_on_off(panel_, true);

  ESP_LOGI(TAG, "Direct LCD init ready (panel=%p, io=%p)", panel_, io_);
  return true;
}

void DisplayService::DeinitPanel() {
  if (panel_) {
    esp_lcd_panel_del(panel_);
    panel_ = nullptr;
  }
  if (io_) {
    esp_lcd_panel_io_del(io_);
    io_ = nullptr;
  }
  // NOTE: Do not free SPI bus here because SD/camera may share.
}

void DisplayService::FillScreen(uint16_t color_rgb565) {
  if (!panel_) {
    return;
  }

  constexpr int chunk_h = 40;
  const uint16_t c = kSwapRgb565Bytes ? Swap16(color_rgb565) : color_rgb565;
  std::vector<uint16_t> line(kLcdHRes * chunk_h, c);

  for (int y = 0; y < kLcdVRes; y += chunk_h) {
    int y2 = std::min(y + chunk_h, kLcdVRes);
    esp_err_t ret =
        esp_lcd_panel_draw_bitmap(panel_, 0, y, kLcdHRes, y2, line.data());
    if (ret != ESP_OK) {
      ESP_LOGW(TAG, "draw_bitmap(FillScreen) failed: %s (y=%d)",
               esp_err_to_name(ret), y);
      return;
    }
  }
}

void DisplayService::DrawAsciiText(int x, int y, const std::string &text,
                                   uint16_t fg, uint16_t bg, int scale) {
  if (!panel_) {
    return;
  }

  const uint16_t fg2 = kSwapRgb565Bytes ? Swap16(fg) : fg;
  const uint16_t bg2 = kSwapRgb565Bytes ? Swap16(bg) : bg;

  const int glyph_w = 8 * scale;
  const int glyph_h = 8 * scale;

  int cursor_x = x;
  int cursor_y = y;

  for (unsigned char uc : text) {
    if (uc == '\n') {
      cursor_x = x;
      cursor_y += glyph_h + scale;
      continue;
    }

    // non-ascii -> '?'
    char c = (uc >= 32 && uc <= 126) ? (char)uc : '?';
    const uint8_t *g = GetGlyph(c);

    std::vector<uint16_t> buf(glyph_w * glyph_h, bg2);
    for (int gy = 0; gy < 8; gy++) {
      uint8_t row = g[gy];
      for (int gx = 0; gx < 8; gx++) {
        bool on = (row & (1 << (7 - gx))) != 0;
        if (!on)
          continue;
        for (int sy = 0; sy < scale; sy++) {
          for (int sx = 0; sx < scale; sx++) {
            buf[(gy * scale + sy) * glyph_w + (gx * scale + sx)] = fg2;
          }
        }
      }
    }

    int x2 = std::min(cursor_x + glyph_w, kLcdHRes);
    int y2 = std::min(cursor_y + glyph_h, kLcdVRes);
    if (cursor_x < kLcdHRes && cursor_y < kLcdVRes) {
      esp_err_t ret = esp_lcd_panel_draw_bitmap(panel_, cursor_x, cursor_y, x2,
                                                y2, buf.data());
      if (ret != ESP_OK) {
        ESP_LOGW(TAG, "draw_bitmap(Text) failed: %s", esp_err_to_name(ret));
        return;
      }
    }
    cursor_x += glyph_w + scale;
    if (cursor_x + glyph_w >= kLcdHRes) {
      cursor_x = x;
      cursor_y += glyph_h + scale;
    }
    if (cursor_y >= kLcdVRes) {
      break;
    }
  }
}

void DisplayService::DrawEmoji(const std::string &emoji_id) {
  camera_preview_active_ = false;
  FillScreen(Rgb565(0, 0, 0));

  const int size = 80;
  const int x0 = (kLcdHRes - size) / 2;
  const int y0 = (kLcdVRes - size) / 2;

  const uint16_t bg_black =
      kSwapRgb565Bytes ? Swap16(Rgb565(0, 0, 0)) : Rgb565(0, 0, 0);
  std::vector<uint16_t> buf(size * size, bg_black);

  auto set_px = [&](int x, int y, uint16_t c) {
    if (x < 0 || y < 0 || x >= size || y >= size)
      return;
    buf[y * size + x] = c;
  };

  if (emoji_id == "heart") {
    // Simple heart: two circles + triangle-ish bottom
    const float cx1 = size * 0.35f;
    const float cx2 = size * 0.65f;
    const float cy = size * 0.35f;
    const float r = size * 0.22f;
    const uint16_t red =
        kSwapRgb565Bytes ? Swap16(Rgb565(255, 40, 40)) : Rgb565(255, 40, 40);
    for (int y = 0; y < size; y++) {
      for (int x = 0; x < size; x++) {
        float fx = (float)x;
        float fy = (float)y;
        float d1 = (fx - cx1) * (fx - cx1) + (fy - cy) * (fy - cy);
        float d2 = (fx - cx2) * (fx - cx2) + (fy - cy) * (fy - cy);
        bool top = (d1 <= r * r) || (d2 <= r * r);
        bool bottom = (fy > cy) && (fy < size * 0.9f) &&
                      (std::abs(fx - size * 0.5f) < (fy - cy) * 0.9f);
        if (top || bottom)
          set_px(x, y, red);
      }
    }
    DrawAsciiText(10, 10, "HEART", Rgb565(255, 255, 255), Rgb565(0, 0, 0), 2);
  } else if (emoji_id == "smile") {
    const uint16_t yellow =
        kSwapRgb565Bytes ? Swap16(Rgb565(255, 220, 0)) : Rgb565(255, 220, 0);
    const uint16_t black =
        kSwapRgb565Bytes ? Swap16(Rgb565(0, 0, 0)) : Rgb565(0, 0, 0);
    const float cx = size * 0.5f;
    const float cy = size * 0.5f;
    const float r = size * 0.45f;
    for (int y = 0; y < size; y++) {
      for (int x = 0; x < size; x++) {
        float fx = (float)x;
        float fy = (float)y;
        float d = (fx - cx) * (fx - cx) + (fy - cy) * (fy - cy);
        if (d <= r * r)
          set_px(x, y, yellow);
      }
    }
    // eyes
    for (int y = 0; y < size; y++) {
      for (int x = 0; x < size; x++) {
        float fx = (float)x;
        float fy = (float)y;
        float d1 = (fx - size * 0.35f) * (fx - size * 0.35f) +
                   (fy - size * 0.40f) * (fy - size * 0.40f);
        float d2 = (fx - size * 0.65f) * (fx - size * 0.65f) +
                   (fy - size * 0.40f) * (fy - size * 0.40f);
        if (d1 <= 10.0f || d2 <= 10.0f)
          set_px(x, y, black);
      }
    }
    // smile arc
    for (int x = 0; x < size; x++) {
      float fx = (float)x;
      float t = (fx - cx) / r;
      float y_smile = cy + (t * t) * (size * 0.18f);
      for (int dy = 0; dy < 3; dy++) {
        int yy = (int)y_smile + dy;
        if (yy >= 0 && yy < size && x >= 0 && x < size)
          set_px(x, yy, black);
      }
    }
    DrawAsciiText(10, 10, "SMILE", Rgb565(255, 255, 255), Rgb565(0, 0, 0), 2);
  } else if (emoji_id == "thumbs_up") {
    const uint16_t skin = kSwapRgb565Bytes ? Swap16(Rgb565(255, 224, 189))
                                           : Rgb565(255, 224, 189);
    const uint16_t cuff =
        kSwapRgb565Bytes ? Swap16(Rgb565(70, 130, 180)) : Rgb565(70, 130, 180);
    // palm
    for (int y = size / 3; y < size; ++y) {
      for (int x = size / 3; x < size - size / 6; ++x) {
        set_px(x, y, skin);
      }
    }
    // thumb
    for (int y = size / 4; y < size / 2; ++y) {
      for (int x = size / 6; x < size / 2; ++x) {
        set_px(x, y, skin);
      }
    }
    // cuff
    for (int y = size - size / 6; y < size; ++y) {
      for (int x = size / 3; x < size - size / 6; ++x) {
        set_px(x, y, cuff);
      }
    }
    DrawAsciiText(10, 10, "OK", Rgb565(255, 255, 255), Rgb565(0, 0, 0), 2);
  } else if (emoji_id == "warning") {
    const uint16_t yellow =
        kSwapRgb565Bytes ? Swap16(Rgb565(255, 215, 0)) : Rgb565(255, 215, 0);
    const uint16_t black =
        kSwapRgb565Bytes ? Swap16(Rgb565(0, 0, 0)) : Rgb565(0, 0, 0);
    for (int y = 0; y < size; ++y) {
      for (int x = 0; x <= y; ++x) {
        if (x >= size / 2 - y / 2 && x <= size / 2 + y / 2) {
          set_px(x, size - 1 - y, yellow);
        }
      }
    }
    // exclamation mark
    for (int y = size / 3; y < size - size / 6; ++y) {
      set_px(size / 2, y, black);
    }
    for (int y = size - size / 6; y < size - size / 12; ++y) {
      for (int x = size / 2 - 2; x <= size / 2 + 2; ++x) {
        set_px(x, y, black);
      }
    }
    DrawAsciiText(10, 10, "WARN", Rgb565(0, 0, 0), Rgb565(255, 255, 0), 2);
  } else if (emoji_id == "fire") {
    const uint16_t orange =
        kSwapRgb565Bytes ? Swap16(Rgb565(255, 140, 0)) : Rgb565(255, 140, 0);
    const uint16_t red =
        kSwapRgb565Bytes ? Swap16(Rgb565(255, 69, 0)) : Rgb565(255, 69, 0);
    for (int y = 0; y < size; ++y) {
      for (int x = 0; x < size; ++x) {
        float fx = (x - size / 2.0f) / (size / 2.0f);
        float fy = (float)y / size;
        if (fx * fx + fy < 1.0f) {
          set_px(x, size - 1 - y, orange);
        }
      }
    }
    for (int y = size / 4; y < size; ++y) {
      for (int x = size / 3; x < size - size / 3; ++x) {
        set_px(x, size - 1 - y, red);
      }
    }
    DrawAsciiText(10, 10, "FIRE", Rgb565(255, 255, 255), Rgb565(0, 0, 0), 2);
  } else if (emoji_id == "star") {
    const uint16_t yellow =
        kSwapRgb565Bytes ? Swap16(Rgb565(255, 215, 0)) : Rgb565(255, 215, 0);
    for (int y = 0; y < size; ++y) {
      for (int x = 0; x < size; ++x) {
        int cx = x - size / 2;
        int cy = y - size / 2;
        if (std::abs(cx * cy) < size) {
          set_px(x, y, yellow);
        }
      }
    }
    DrawAsciiText(10, 10, "STAR", Rgb565(0, 0, 64), Rgb565(255, 215, 0), 2);
  } else {
    DrawAsciiText(10, 100, "UNKNOWN EMOJI", Rgb565(255, 0, 0), Rgb565(0, 0, 0),
                  2);
  }

  if (panel_) {
    esp_err_t ret = esp_lcd_panel_draw_bitmap(panel_, x0, y0, x0 + size,
                                              y0 + size, buf.data());
    if (ret != ESP_OK) {
      ESP_LOGW(TAG, "draw_bitmap(Emoji) failed: %s", esp_err_to_name(ret));
    }
  }
}

bool DisplayService::IsAsciiRenderable(const std::string &text) const {
  for (unsigned char ch : text) {
    if (ch < 0x20 || ch > 0x7E) {
      return false;
    }
  }
  return true;
}

void DisplayService::RenderUnicodeNotice(const std::string &text) {
  DisableCameraPreviewLocked();
  FillScreen(Rgb565(0, 0, 0));
  DrawAsciiText(20, 80, "UTF-8 TEXT", Rgb565(255, 165, 0), Rgb565(0, 0, 0), 2);
  DrawAsciiText(20, 110, "NOT SUPPORTED", Rgb565(255, 165, 0), Rgb565(0, 0, 0),
                2);
  (void)text;
}

std::vector<std::string>
DisplayService::WrapText(const std::string &text, size_t max_chars) const {
  std::vector<std::string> lines;
  std::istringstream iss(text);
  std::string word;
  std::string current;

  while (iss >> word) {
    if (current.empty()) {
      current = word;
    } else if (current.size() + 1 + word.size() <= max_chars) {
      current += " " + word;
    } else {
      lines.push_back(current);
      current = word;
    }
  }
  if (!current.empty()) {
    lines.push_back(current);
  }
  return lines;
}

void DisplayService::DrawCenteredLines(const std::vector<std::string> &lines,
                                       uint16_t fg, uint16_t bg) {
  if (lines.empty()) {
    return;
  }

  const int line_height = 20;
  int total_height = static_cast<int>(lines.size()) * line_height;
  int start_y = (kLcdVRes - total_height) / 2;
  if (start_y < 0) {
    start_y = 0;
  }

  for (size_t i = 0; i < lines.size(); ++i) {
    const auto &line = lines[i];
    int line_width = static_cast<int>(line.size()) * 12;
    int start_x = std::max(0, (kLcdHRes - line_width) / 2);
    DrawAsciiText(start_x, start_y + static_cast<int>(i) * line_height, line, fg,
                  bg, 2);
  }
}

void DisplayService::DrawListeningScreen(int level) {
  FillScreen(Rgb565(0, 0, 0));
  const int center_x = kLcdHRes / 2;
  const int center_y = kLcdVRes / 2 - 10;
  DrawMicShape(center_x, center_y, 32, Rgb565(220, 220, 220));

  const uint16_t bar_color = Rgb565(0, 200, 255);
  const int base_y = center_y + 60;
  const int bar_width = 10;
  const int spacing = 14;
  for (int i = -2; i <= 2; ++i) {
    int amplitude = 20 + ((level + i + 4) % 4) * 10;
    int x = center_x + i * spacing;
    FillRect(x - bar_width / 2, base_y - amplitude, x + bar_width / 2, base_y,
             bar_color);
  }

  DrawAsciiText(center_x - 70, base_y + 20, "Listening...",
                Rgb565(0, 200, 255), Rgb565(0, 0, 0), 2);
}

void DisplayService::DrawMicShape(int center_x, int center_y, int radius,
                                  uint16_t color) {
  // Mic capsule
  FillRect(center_x - radius / 2, center_y - radius, center_x + radius / 2,
           center_y + radius, color);
  // Rounded top
  for (int y = 0; y < radius; ++y) {
    int width = static_cast<int>(std::sqrt(radius * radius - y * y));
    FillRect(center_x - width / 2, center_y - radius - y,
             center_x + width / 2, center_y - radius - y + 1, color);
  }
  // Rounded bottom
  for (int y = 0; y < radius / 2; ++y) {
    int width =
        static_cast<int>(std::sqrt((radius / 2) * (radius / 2) - y * y));
    FillRect(center_x - width / 2, center_y + radius + y,
             center_x + width / 2, center_y + radius + y + 1, color);
  }
  // Base
  FillRect(center_x - radius, center_y + radius + radius / 2,
           center_x + radius, center_y + radius + radius / 2 + 6, color);
  FillRect(center_x - 6, center_y + radius + radius / 2,
           center_x + 6, center_y + radius + radius + 20, color);
}

void DisplayService::ShowCameraFrameRGB565(const uint8_t *frame, int width,
                                           int height) {
  if (!initialized_ || !frame || width <= 0 || height <= 0) {
    return;
  }

  DisplayLock lock(render_mutex_);
  camera_preview_active_ = true;
  is_listening_ = false;

  const size_t target_pixels = kLcdHRes * kLcdVRes;
  camera_buffer_.resize(target_pixels);
  const uint16_t *src = reinterpret_cast<const uint16_t *>(frame);

  if (width == kLcdHRes && height == kLcdVRes) {
    for (size_t i = 0; i < target_pixels; ++i) {
      uint16_t px = src[i];
      camera_buffer_[i] = kSwapRgb565Bytes ? Swap16(px) : px;
    }
  } else {
    for (int y = 0; y < kLcdVRes; ++y) {
      int src_y = y * height / kLcdVRes;
      const uint16_t *src_row = src + src_y * width;
      uint16_t *dst_row = camera_buffer_.data() + y * kLcdHRes;
      for (int x = 0; x < kLcdHRes; ++x) {
        uint16_t px = src_row[x * width / kLcdHRes];
        dst_row[x] = kSwapRgb565Bytes ? Swap16(px) : px;
      }
    }
  }

  const int chunk_h = 40;
  for (int y = 0; y < kLcdVRes; y += chunk_h) {
    int y2 = std::min(y + chunk_h, kLcdVRes);
    esp_lcd_panel_draw_bitmap(panel_, 0, y, kLcdHRes, y2,
                              camera_buffer_.data() + y * kLcdHRes);
  }
}

void DisplayService::DisableCameraPreview() {
  if (!initialized_) {
    return;
  }
  DisplayLock lock(render_mutex_);
  if (!camera_preview_active_) {
    return;
  }
  camera_preview_active_ = false;
  FillScreen(Rgb565(0, 0, 0));
}

void DisplayService::DisableCameraPreviewLocked() {
  if (camera_preview_active_) {
    camera_preview_active_ = false;
  }
}

void DisplayService::FillRect(int x1, int y1, int x2, int y2, uint16_t color) {
  if (!panel_) {
    return;
  }
  x1 = std::max(0, x1);
  y1 = std::max(0, y1);
  x2 = std::min(kLcdHRes, x2);
  y2 = std::min(kLcdVRes, y2);
  if (x2 <= x1 || y2 <= y1) {
    return;
  }
  const int width = x2 - x1;
  const int height = y2 - y1;
  std::vector<uint16_t> buf(width * height, color);
  esp_lcd_panel_draw_bitmap(panel_, x1, y1, x2, y2, buf.data());
}
