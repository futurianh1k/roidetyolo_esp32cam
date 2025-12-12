# 코드 비교 분석: xiaozhi-esp32 vs firmware

**작성일:** 2025-12-10  
**분석 대상:**
- `xiaozhi-esp32/`: ESP-IDF 기반 완전한 AI 챗봇 프로젝트
- `firmware/`: PlatformIO/Arduino 기반 Core S3 관리 시스템

---

## 1. 아키텍처 비교

### 1.1 프레임워크 및 빌드 시스템

| 항목 | xiaozhi-esp32 | firmware |
|------|---------------|----------|
| **프레임워크** | ESP-IDF (네이티브) | PlatformIO + Arduino |
| **빌드 시스템** | CMake (ESP-IDF) | PlatformIO |
| **언어** | C++ (ESP-IDF 스타일) | C++ (Arduino 스타일) |
| **메모리 관리** | FreeRTOS 태스크 기반 | Arduino 스타일 (loop) |
| **코드베이스 크기** | 대규모 (1000+ 파일) | 소규모 (7개 모듈) |

### 1.2 주요 차이점

**xiaozhi-esp32:**
- ESP-IDF 네이티브 API 사용 (`esp_log.h`, `freertos/FreeRTOS.h`)
- 멀티태스크 아키텍처 (별도 태스크로 오디오/네트워크 처리)
- 상태 머신 기반 디바이스 제어
- MCP (Model Context Protocol) 서버 통합

**firmware:**
- Arduino 라이브러리 기반 (M5Unified, PubSubClient)
- 단일 루프 기반 (`setup()` + `loop()`)
- 모듈화된 구조 (audio_module, camera_module 등)
- MQTT + WebSocket 하이브리드 통신

---

## 2. 오디오 처리 비교

### 2.1 현재 Firmware 상태

**구현된 기능:**
- ✅ I2S PCM 입력/출력 (16kHz, 16bit, 모노)
- ✅ WebSocket을 통한 PCM 스트리밍
- ✅ HTTP를 통한 오디오 파일 재생
- ❌ OPUS 코덱 없음 (PCM만 전송)
- ❌ 웨이크 워드 감지 없음
- ❌ 오디오 전처리 없음

**코드 위치:**
```cpp
// firmware/src/audio_module.cpp
// - I2S 설정 및 PCM 데이터 읽기/쓰기
// - WebSocket으로 PCM 스트리밍
// - HTTP GET으로 오디오 파일 재생
```

### 2.2 Xiaozhi-esp32 오디오 기능

**구현된 기능:**
- ✅ OPUS 코덱 (인코딩/디코딩 완전 구현)
- ✅ ESP-SR 기반 웨이크 워드 감지
- ✅ 오디오 전처리 (노이즈 제거, AGC 등)
- ✅ 멀티태스크 오디오 파이프라인
- ✅ OPUS 스트리밍 (대역폭 절약)

**주요 파일:**
```
xiaozhi-esp32/main/audio/
├── audio_codec.h/cc          # I2S 코덱 추상화
├── audio_service.h/cc        # 오디오 서비스 (OPUS 인코딩/디코딩)
├── codecs/                   # 다양한 오디오 코덱 (ES8311, ES8388 등)
│   ├── opus_encoder.h/cc    # OPUS 인코더
│   ├── opus_decoder.h/cc    # OPUS 디코더
│   └── opus_resampler.h/cc  # 리샘플링
├── wake_words/               # 웨이크 워드 감지
│   ├── esp_wake_word.h/cc   # ESP-SR 웨이크 워드
│   ├── afe_wake_word.h/cc   # AFE 웨이크 워드
│   └── custom_wake_word.h/cc # 사용자 정의 웨이크 워드
└── processors/               # 오디오 전처리
    ├── afe_audio_processor.h/cc
    └── ...
```

**OPUS 코덱 구현:**
```cpp
// xiaozhi-esp32/main/audio/audio_service.h
#define OPUS_FRAME_DURATION_MS 60
std::unique_ptr<OpusEncoderWrapper> opus_encoder_;
std::unique_ptr<OpusDecoderWrapper> opus_decoder_;

// 인코딩: PCM -> OPUS (60ms 프레임)
// 디코딩: OPUS -> PCM
```

**웨이크 워드 감지:**
```cpp
// xiaozhi-esp32/main/audio/wake_word.h
class WakeWord {
    virtual bool Initialize(AudioCodec* codec, srmodel_list_t* models_list) = 0;
    virtual void Feed(const std::vector<int16_t>& data) = 0;
    virtual void OnWakeWordDetected(std::function<void(const std::string&)> callback) = 0;
};
```

---

## 3. 카메라 처리 비교

### 3.1 현재 Firmware 상태

**구현된 기능:**
- ✅ OV2640 카메라 초기화
- ✅ JPEG 캡처 (단일 프레임)
- ✅ HTTP POST로 JPEG 전송 (MJPEG 스틸컷)
- ❌ WebSocket 스트리밍 없음
- ❌ 멀티스레드 인코딩 없음
- ❌ 실시간 스트리밍 없음

**코드 위치:**
```cpp
// firmware/src/camera_module.cpp
// - cameraInit(): 카메라 초기화
// - cameraCaptureFrame(): JPEG 캡처
// - cameraSendToSink(): HTTP POST로 전송
```

### 3.2 Xiaozhi-esp32 카메라 기능

**구현된 기능:**
- ✅ 멀티스레드 JPEG 인코딩
- ✅ HTTP multipart/form-data 전송
- ✅ WebSocket 스트리밍 (추정, 코드 확인 필요)
- ✅ 실시간 영상 전송

**참고 코드:**
```cpp
// xiaozhi-esp32/main/mcp_server.cc
// multipart/form-data 형식으로 JPEG 전송
http->SetHeader("Content-Type", "multipart/form-data; boundary=" + boundary);
```

---

## 4. 상태 관리 비교

### 4.1 현재 Firmware 상태

**구현된 기능:**
- ✅ 간단한 상태 플래그 (`cameraActive`, `microphoneActive`, `asrMode`)
- ❌ 상태 머신 없음
- ❌ 상태 전환 검증 없음

### 4.2 Xiaozhi-esp32 상태 관리

**구현된 기능:**
- ✅ 완전한 상태 머신 (`DeviceStateMachine`)
- ✅ 상태 전환 검증
- ✅ 상태 변경 콜백

**코드:**
```cpp
// xiaozhi-esp32/main/device_state_machine.h
class DeviceStateMachine {
    DeviceState GetState() const;
    bool TransitionTo(DeviceState new_state);
    bool CanTransitionTo(DeviceState target) const;
    int AddStateChangeListener(StateCallback callback);
};
```

**상태 정의:**
```cpp
// xiaozhi-esp32/main/device_state.h
enum DeviceState {
    kDeviceStateUnknown,
    kDeviceStateIdle,
    kDeviceStateListening,
    kDeviceStateProcessing,
    kDeviceStateSpeaking,
    // ...
};
```

---

## 5. 통신 프로토콜 비교

### 5.1 현재 Firmware

**구현된 프로토콜:**
- ✅ MQTT (PubSubClient)
- ✅ WebSocket (ArduinoWebsockets) - ASR용
- ✅ HTTP (HTTPClient) - 오디오 재생, 카메라 전송

**제한사항:**
- WebSocket은 ASR 전용 (PCM 스트리밍만)
- 프로토콜 추상화 없음

### 5.2 Xiaozhi-esp32

**구현된 프로토콜:**
- ✅ WebSocket 프로토콜 (완전한 구현)
- ✅ MQTT + UDP 하이브리드 프로토콜
- ✅ MCP (Model Context Protocol) 서버
- ✅ 프로토콜 추상화 (`protocol.h`)

**코드 구조:**
```
xiaozhi-esp32/main/protocols/
├── protocol.h/cc              # 프로토콜 추상화
├── websocket_protocol.h/cc    # WebSocket 구현
└── mqtt_protocol.h/cc         # MQTT 구현
```

---

## 6. 기능 비교 요약표

| 기능 | firmware | xiaozhi-esp32 | 통합 우선순위 |
|------|----------|---------------|--------------|
| **오디오** |
| I2S PCM | ✅ | ✅ | - |
| OPUS 코덱 | ❌ | ✅ | **높음** |
| 웨이크 워드 | ❌ | ✅ (ESP-SR) | **높음** |
| 오디오 전처리 | ❌ | ✅ | 중간 |
| **카메라** |
| JPEG 캡처 | ✅ | ✅ | - |
| HTTP 전송 | ✅ | ✅ | - |
| WebSocket 스트리밍 | ❌ | ✅ | **높음** |
| 멀티스레드 인코딩 | ❌ | ✅ | 중간 |
| **상태 관리** |
| 상태 머신 | ❌ | ✅ | 중간 |
| 상태 전환 검증 | ❌ | ✅ | 중간 |
| **통신** |
| MQTT | ✅ | ✅ | - |
| WebSocket | ✅ (ASR만) | ✅ (완전) | - |
| MCP 서버 | ❌ | ✅ | 낮음 |
| **기타** |
| TTS 재생 | ❌ | ✅ | 중간 |
| 성문 인식 | ❌ | ✅ (서버 측) | 낮음 |
| 다국어 지원 | ❌ | ✅ | 낮음 |

---

## 7. 다른 AI 분석 결과 리뷰

### 7.1 분석 결과 검증

**✅ 정확한 분석:**
1. **카메라**: firmware는 기본 JPEG 캡처만, 스트리밍 미구현 → **정확**
2. **오디오**: I2S PCM만, OPUS 코덱 없음 → **정확**
3. **웨이크 워드**: 없음 (서버 ASR만 사용) → **정확**
4. **Xiaozhi OPUS 코덱**: 완전 구현 확인 → **정확**
5. **Xiaozhi 웨이크 워드**: ESP-SR 기반 확인 → **정확**

**⚠️ 보완 필요:**
1. **카메라 WebSocket 스트리밍**: xiaozhi에서도 명시적인 WebSocket 스트리밍 코드는 확인되지 않음. multipart/form-data HTTP 전송만 확인됨.
2. **멀티스레드 JPEG 인코딩**: xiaozhi 코드에서 명시적인 멀티스레드 인코딩 구현은 확인되지 않음. ESP-IDF의 멀티태스크 환경을 활용할 수 있음.

### 7.2 우선순위 평가

**✅ 동의하는 우선순위:**
- **높음**: OPUS 코덱 통합, 오프라인 웨이크 워드, 카메라 스트리밍
- **중간**: TTS 재생, 상태 머신
- **낮음**: 성문 인식 (서버 측 처리로 충분)

**💡 추가 제안:**
- **중간**: 오디오 전처리 (노이즈 제거, AGC) - OPUS 통합 후 고려
- **낮음**: MCP 서버 통합 - 현재 프로젝트와 직접 관련 없음

---

## 8. 통합 전략

### 8.1 단계별 통합 계획

#### Phase 1: OPUS 코덱 통합 (최우선)

**목표:**
- PCM 대신 OPUS로 오디오 스트리밍
- 대역폭 절약 (약 10:1 압축)
- 지연 시간 감소

**작업:**
1. OPUS 라이브러리 추가 (ESP-IDF opus 컴포넌트 또는 Arduino 라이브러리)
2. `audio_module.cpp`에 OPUS 인코더/디코더 추가
3. WebSocket 프로토콜 수정 (PCM → OPUS)
4. 백엔드 ASR 서버 OPUS 지원 확인/수정

**참고 코드:**
- `xiaozhi-esp32/main/audio/codecs/opus_encoder.h`
- `xiaozhi-esp32/main/audio/codecs/opus_decoder.h`

**예상 작업량:** 2-3일

#### Phase 2: 오프라인 웨이크 워드 (ESP-SR)

**목표:**
- 서버 의존성 감소
- 즉시 반응 (로컬 처리)

**작업:**
1. ESP-SR 라이브러리 추가
2. 웨이크 워드 모델 통합
3. `audio_module.cpp`에 웨이크 워드 감지 로직 추가
4. 상태 머신 연동 (웨이크 워드 감지 → ASR 모드 전환)

**참고 코드:**
- `xiaozhi-esp32/main/audio/wake_words/esp_wake_word.h`
- `xiaozhi-esp32/main/audio/wake_words/afe_wake_word.h`

**예상 작업량:** 3-5일

#### Phase 3: 카메라 WebSocket 스트리밍

**목표:**
- 실시간 영상 전송
- HTTP 대신 WebSocket 사용 (지연 감소)

**작업:**
1. WebSocket 스트리밍 프로토콜 설계
2. `camera_module.cpp`에 WebSocket 스트리밍 추가
3. 멀티태스크 환경 고려 (별도 태스크로 JPEG 인코딩)
4. 백엔드 WebSocket 수신 처리

**참고 코드:**
- `xiaozhi-esp32/main/mcp_server.cc` (multipart 전송 참고)
- `firmware/src/websocket_module.cpp` (기존 WebSocket 구현 참고)

**예상 작업량:** 2-3일

#### Phase 4: 상태 머신 통합

**목표:**
- 안정적인 상태 전환
- 상태 기반 제어

**작업:**
1. `device_state_machine.h/cc` 생성
2. 상태 정의 (`device_state.h`)
3. 기존 모듈을 상태 머신에 연동
4. 상태 전환 검증 로직 추가

**참고 코드:**
- `xiaozhi-esp32/main/device_state_machine.h`
- `xiaozhi-esp32/main/device_state.h`

**예상 작업량:** 2일

#### Phase 5: TTS 재생 파이프라인

**목표:**
- 서버에서 받은 TTS 오디오 재생
- OPUS 디코딩 후 스피커 출력

**작업:**
1. TTS 오디오 수신 (WebSocket 또는 HTTP)
2. OPUS 디코딩
3. 스피커 출력

**예상 작업량:** 1-2일

---

## 9. 기술적 고려사항

### 9.1 프레임워크 차이

**문제:**
- xiaozhi는 ESP-IDF 기반, firmware는 Arduino 기반
- 직접 코드 포팅 불가능

**해결책:**
1. **라이브러리 활용**: Arduino용 OPUS 라이브러리 사용
2. **하이브리드 접근**: 필요한 부분만 ESP-IDF API 사용
3. **점진적 마이그레이션**: ESP-IDF로 전환 고려 (장기)

### 9.2 메모리 제약

**문제:**
- ESP32-S3 메모리 제한
- OPUS + 웨이크 워드 + 카메라 동시 실행 시 메모리 부족 가능

**해결책:**
1. **동적 로딩**: 필요 시에만 모듈 로드
2. **메모리 풀 관리**: PSRAM 활용
3. **우선순위 기반**: 웨이크 워드 우선, 카메라는 선택적

### 9.3 성능 최적화

**문제:**
- 단일 루프 기반 아키텍처의 성능 제한

**해결책:**
1. **FreeRTOS 태스크 도입**: 오디오/카메라를 별도 태스크로
2. **우선순위 설정**: 오디오 > 카메라 > 네트워크
3. **버퍼 최적화**: DMA 버퍼 크기 조정

---

## 10. 결론 및 권장사항

### 10.1 즉시 시작 가능한 작업

1. **OPUS 코덱 통합** (최우선)
   - 대역폭 절약 효과 즉시 확인 가능
   - 기존 WebSocket 프로토콜 수정만 필요

2. **오프라인 웨이크 워드** (ESP-SR)
   - 서버 의존성 감소
   - 사용자 경험 개선

3. **카메라 WebSocket 스트리밍**
   - 실시간 영상 전송
   - HTTP 대비 지연 감소

### 10.2 중장기 계획

1. **상태 머신 통합**: 안정성 향상
2. **TTS 재생 파이프라인**: 완전한 음성 상호작용
3. **ESP-IDF 마이그레이션 고려**: 장기적 확장성

### 10.3 리스크 관리

- **메모리 부족**: 단계별 통합, 각 단계에서 메모리 사용량 측정
- **성능 저하**: FreeRTOS 태스크 도입 고려
- **호환성 문제**: 백엔드 서버도 OPUS 지원 필요

---

## 11. 참고 자료

### 11.1 Xiaozhi-esp32 주요 파일

- `xiaozhi-esp32/main/audio/audio_service.cc` - 오디오 서비스 메인
- `xiaozhi-esp32/main/audio/codecs/opus_encoder.h` - OPUS 인코더
- `xiaozhi-esp32/main/audio/wake_words/esp_wake_word.h` - ESP-SR 웨이크 워드
- `xiaozhi-esp32/main/device_state_machine.h` - 상태 머신
- `xiaozhi-esp32/main/protocols/websocket_protocol.h` - WebSocket 프로토콜

### 11.2 외부 라이브러리

- **ESP-SR**: https://github.com/espressif/esp-sr
- **OPUS 코덱**: ESP-IDF 컴포넌트 또는 Arduino 라이브러리
- **ESP32-Camera**: 이미 사용 중

### 11.3 문서

- `xiaozhi-esp32/README_kr.md` - 한국어 문서
- `xiaozhi-esp32/docs/websocket.md` - WebSocket 프로토콜 문서
- `xiaozhi-esp32/docs/mcp-protocol.md` - MCP 프로토콜 문서

---

**작성자:** AI Assistant  
**검토 필요:** 프로젝트 리더  
**다음 단계:** Phase 1 (OPUS 코덱 통합) 시작

