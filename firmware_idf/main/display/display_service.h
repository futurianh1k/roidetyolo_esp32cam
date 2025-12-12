#ifndef DISPLAY_SERVICE_H
#define DISPLAY_SERVICE_H

#include <string>

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

  /**
   * 마이크 애니메이션 업데이트 (주기적으로 호출)
   */
  void UpdateListeningAnimation();

private:
  bool initialized_ = false;
  std::string current_text_;
  bool is_listening_ = false;
  int listening_animation_frame_ = 0;
  int64_t last_animation_update_ = 0;
};

#endif // DISPLAY_SERVICE_H
