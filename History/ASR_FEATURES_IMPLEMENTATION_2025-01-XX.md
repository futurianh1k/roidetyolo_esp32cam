# 음성인식 기능 구현 완료 보고서

## 구현 일자

2025-01-XX

## 구현 내용 요약

### 1. WebSocket 클라이언트 구현 ✅

- **파일**: `firmware_idf/main/network/websocket_client.h`, `.cc`
- **기능**:
  - ASR 서버와 WebSocket 통신
  - 오디오 스트림 전송 (Base64 인코딩된 JSON 형식)
  - 인식 결과 수신 및 파싱
  - 자동 재연결 지원
- **참고**: ESP-IDF `esp_websocket_client` 사용

### 2. ASR 서비스 구현 ✅

- **파일**: `firmware_idf/main/asr/asr_service.h`, `.cc`
- **기능**:
  - ASR 서버 세션 생성 (HTTP API)
  - WebSocket 연결 및 오디오 스트림 전송
  - 인식 결과 수신 및 처리
  - 백엔드로 결과 전송 (HTTP POST)
- **특징**:
  - MQTT로 받은 `ws_url` 사용 가능
  - 자동 오디오 스트리밍 (20ms 프레임)

### 3. 디스플레이 서비스 구현 ✅

- **파일**: `firmware_idf/main/display/display_service.h`, `.cc`
- **기능**:
  - 텍스트 표시
  - 음성인식 중 마이크 아이콘 표시
  - 상태 표시
- **참고**: 현재는 로그만 출력, 실제 하드웨어 연동은 추후 구현

### 4. WebSocket 자동 연결 ✅

- **구현 위치**: `firmware_idf/main/application.cc`
- **동작**:
  - WiFi 연결 후 MQTT 연결
  - MQTT로 `start_asr` 명령 수신 시 WebSocket 자동 연결
  - 재연결은 WebSocketClient에서 자동 처리

### 5. MQTT 토픽 구독 추가 ✅

- **추가된 토픽**: `devices/{device_id}/command`
- **처리 내용**:
  - `devices/{device_id}/control/microphone`: 마이크 제어 (start_asr, stop_asr)
  - `devices/{device_id}/control/display`: 디스플레이 제어 (show_text, clear)
  - `devices/{device_id}/command`: 통합 명령 토픽

### 6. 음성인식 결과 표시 기능 ✅

#### 6.1 장비 스크린 표시

- **구현 위치**: `firmware_idf/main/asr/asr_service.cc`
- **동작**:
  - 인식 결과를 디스플레이 서비스로 전달
  - 응급 상황인 경우 "🚨" 표시 추가
  - 5초간 표시 후 자동 클리어

#### 6.2 프론트엔드 채팅 윈도우 표시

- **구현 위치**: `frontend/src/app/devices/[id]/page.tsx`
- **동작**:
  - 백엔드 WebSocket으로 ESP32에서 전송한 결과 수신
  - `RecognitionChatWindow` 컴포넌트에 표시
  - 기존 ASR 서버 WebSocket 결과와 통합

### 7. 음성인식 중 UI 표시 ✅

- **구현 위치**: `firmware_idf/main/display/display_service.cc`
- **기능**:
  - `ShowListening(true)`: 마이크 아이콘 및 "🎤 음성인식 중..." 표시
  - `ShowListening(false)`: 마이크 아이콘 숨김
- **트리거**:
  - `kDeviceStateListening` 상태 전이 시 자동 표시
  - MQTT `start_asr` 명령 수신 시 표시

## 수정된 파일 목록

### 펌웨어 (ESP-IDF)

1. `firmware_idf/main/network/websocket_client.h` (신규)
2. `firmware_idf/main/network/websocket_client.cc` (신규)
3. `firmware_idf/main/asr/asr_service.h` (신규)
4. `firmware_idf/main/asr/asr_service.cc` (신규)
5. `firmware_idf/main/display/display_service.h` (신규)
6. `firmware_idf/main/display/display_service.cc` (신규)
7. `firmware_idf/main/application.cc` (수정)
8. `firmware_idf/main/config.h` (수정)
9. `firmware_idf/main/CMakeLists.txt` (수정)

### 백엔드

1. `backend/app/schemas/asr.py` (수정 - device_id_string 추가)
2. `backend/app/api/asr.py` (수정 - device_id_string 처리)

### 프론트엔드

1. `frontend/src/app/devices/[id]/page.tsx` (수정 - 백엔드 WebSocket 연결 추가)

## 동작 흐름

### 음성인식 시작

1. 프론트엔드에서 "음성인식 시작" 버튼 클릭
2. 백엔드 API 호출: `POST /api/asr/devices/{device_id}/session/start`
3. 백엔드가 ASR 서버에 세션 생성 요청
4. 백엔드가 MQTT로 ESP32에 `start_asr` 명령 전송
   - 토픽: `devices/{device_id}/control/microphone`
   - Payload: `{"command": "microphone", "action": "start_asr", "ws_url": "...", "language": "ko"}`
5. ESP32가 MQTT 명령 수신
6. ESP32가 WebSocket 연결 (ws_url 사용 또는 ASR 서버에서 세션 생성)
7. ESP32가 마이크 시작 및 오디오 스트림 전송
8. 디스플레이에 "🎤 음성인식 중..." 표시

### 음성인식 결과 수신

1. ASR 서버가 음성 인식 완료
2. ASR 서버가 WebSocket으로 결과 전송
3. ESP32가 결과 수신
4. ESP32가 디스플레이에 결과 표시
5. ESP32가 백엔드로 결과 전송 (HTTP POST `/api/asr/result`)
6. 백엔드가 결과를 DB에 저장
7. 백엔드가 WebSocket으로 구독 중인 클라이언트에게 브로드캐스트
8. 프론트엔드가 결과 수신 및 채팅 윈도우에 표시

## 테스트 필요 사항

1. **WebSocket 연결 테스트**

   - ASR 서버 연결 성공 여부
   - 재연결 동작 확인

2. **오디오 스트림 테스트**

   - PCM 데이터 전송 확인
   - Base64 인코딩 정확성

3. **인식 결과 처리 테스트**

   - 디스플레이 표시 확인
   - 백엔드 전송 확인
   - 프론트엔드 수신 확인

4. **MQTT 명령 처리 테스트**
   - start_asr 명령 처리
   - stop_asr 명령 처리
   - display 명령 처리

## 알려진 제한사항

1. **디스플레이 하드웨어**

   - 현재는 로그만 출력
   - 실제 ILI9341 디스플레이 연동 필요
   - LVGL 또는 비트맵 폰트 통합 필요

2. **Base64 인코딩**

   - 현재 간단한 구현 사용
   - 최적화 가능 (라이브러리 사용)

3. **시간 처리**
   - 타임스탬프 생성 간단 구현
   - NTP 동기화 고려 필요

## 다음 단계

1. 디스플레이 하드웨어 연동
2. 폰트 렌더링 구현
3. 마이크 아이콘 애니메이션
4. 에러 처리 개선
5. 통합 테스트
