# 개발 현황 및 향후 개발 계획

**작성일**: 2025-12-10  
**프로젝트**: M5Stack Core S3 장비 원격 관리 시스템  
**상태**: 펌웨어 빌드 에러로 인한 revert 후 재계획

---

## 📊 현재 개발 상태

### ✅ 완료된 기능

#### 1. 프론트엔드 (Phase 4 완료)

**구현된 기능**:

- ✅ 장비 목록 조회 및 표시
- ✅ 장비 상세 페이지
- ✅ 장비 등록/수정/삭제
- ✅ 장비 상태 실시간 모니터링 (5초 간격)
- ✅ 카메라 제어 (시작/일시정지/정지)
- ✅ 마이크 제어 (시작/일시정지/정지)
- ✅ 스피커 제어 (재생/정지)
- ✅ 디스플레이 제어 (텍스트 표시/이모티콘/지우기)
- ✅ 시스템 제어 (재시작)
- ✅ IP 주소 편집 기능
- ✅ **음성인식 패널** (`VoiceRecognitionPanel.tsx`)
- ✅ **인식 결과 채팅 창** (`RecognitionChatWindow.tsx`)
- ✅ **WebSocket Hook** (`useASRWebSocket.ts`)
- ✅ 영상 sink 설정 UI (카메라 제어 시)

**주요 파일**:

- `frontend/src/app/dashboard/page.tsx` - 대시보드
- `frontend/src/app/devices/[id]/page.tsx` - 장비 상세 페이지
- `frontend/src/components/DeviceControl.tsx` - 장비 제어 컴포넌트
- `frontend/src/components/DeviceStatus.tsx` - 장비 상태 컴포넌트
- `frontend/src/components/VoiceRecognitionPanel.tsx` - 음성인식 패널
- `frontend/src/components/RecognitionChatWindow.tsx` - 인식 결과 창
- `frontend/src/hooks/useASRWebSocket.ts` - WebSocket Hook
- `frontend/src/lib/api.ts` - API 클라이언트

#### 2. 백엔드 (Phase 2, Phase 5 완료)

**구현된 기능**:

- ✅ 장비 관리 API (등록/조회/수정/삭제)
- ✅ 장비 상태 관리 (MQTT 수신, DB 저장)
- ✅ 장비 제어 API (카메라/마이크/스피커/디스플레이/시스템)
- ✅ MQTT 서비스 (명령 전송, 상태 수신)
- ✅ **ASR 세션 관리 API** (`/asr/devices/{id}/session/start|stop|status`)
- ✅ **ASR 결과 수신 API** (`POST /asr/result`)
- ✅ WebSocket 브로드캐스트 (인식 결과 전파)
- ✅ 영상 sink 설정 지원 (카메라 제어 시)
- ✅ 오디오 업로드/재생 API
- ✅ 인증 시스템 (현재 비활성화, TODO)
- ✅ 감사 로그 (AuditLog)

**주요 파일**:

- `backend/app/api/devices.py` - 장비 관리 API
- `backend/app/api/control.py` - 장비 제어 API
- `backend/app/api/asr.py` - ASR API (세션 관리, 결과 수신)
- `backend/app/api/audio.py` - 오디오 API
- `backend/app/services/mqtt_service.py` - MQTT 서비스
- `backend/app/services/asr_service.py` - ASR 서비스 클라이언트
- `backend/app/schemas/asr.py` - ASR 스키마

**API 엔드포인트**:

```
GET    /devices                    - 장비 목록
GET    /devices/{id}               - 장비 상세
POST   /devices                    - 장비 등록
PUT    /devices/{id}               - 장비 수정
DELETE /devices/{id}               - 장비 삭제
GET    /devices/{id}/status        - 장비 상태 조회

POST   /control/devices/{id}/camera      - 카메라 제어
POST   /control/devices/{id}/microphone  - 마이크 제어
POST   /control/devices/{id}/speaker     - 스피커 제어
POST   /control/devices/{id}/display     - 디스플레이 제어
POST   /control/devices/{id}/system      - 시스템 제어

POST   /asr/devices/{id}/session/start   - ASR 세션 시작
POST   /asr/devices/{id}/session/stop    - ASR 세션 종료
GET    /asr/devices/{id}/session/status  - ASR 세션 상태
GET    /asr/sessions                     - 모든 세션 목록
POST   /asr/result                        - ASR 결과 수신 (ASR 서버 → 백엔드)
GET    /asr/health                        - ASR 서버 헬스 체크

POST   /audio/upload                      - 오디오 업로드
GET    /audio/{id}                        - 오디오 다운로드
```

#### 3. ASR 서버 (Phase 1 완료)

**구현된 기능**:

- ✅ WebSocket 기반 오디오 스트리밍 수신
- ✅ VAD (Voice Activity Detection) 통합
- ✅ Sherpa-ONNX 음성인식 엔진
- ✅ 다중 세션 관리
- ✅ 응급 상황 자동 감지
- ✅ **HTTP POST로 백엔드에 결과 전송** (Phase 5)
- ✅ 바이너리 PCM 스트리밍 지원 (Base64 대신)

**주요 파일**:

- `backend/rk3588asr/asr_api_server.py` - ASR API 서버
- `backend/rk3588asr/demo_vad_final.py` - VAD 프로세서

**API 엔드포인트**:

```
POST   /asr/session/start          - 세션 생성
GET    /asr/session/{id}/status    - 세션 상태
POST   /asr/session/{id}/stop      - 세션 종료
GET    /asr/sessions               - 세션 목록
WS     /ws/audio/{session_id}      - 바이너리 PCM 스트리밍
GET    /health                     - 헬스 체크
```

#### 4. 펌웨어 (Revert 상태)

**현재 상태**: 빌드 에러로 인해 기능 구현 이전 상태로 revert됨

**기본 기능만 구현됨**:

- ✅ WiFi 연결
- ✅ MQTT 연결 및 기본 통신
- ✅ 카메라 초기화 (기본 기능)
- ✅ 오디오 초기화 (기본 기능)
- ✅ 디스플레이 초기화 (기본 기능)
- ✅ 상태 보고 (기본 정보)

**미구현 기능** (revert 전에 구현되었던 것들):

- ❌ ASR WebSocket 연결 및 오디오 스트리밍
- ❌ 영상 sink 전송 (MJPEG/WebSocket/RTSP)
- ❌ 한글/일본어 텍스트 표시 (UTF-8 폰트)
- ❌ 이모티콘 그래픽 표시
- ❌ MP3 재생 (FreeRTOS Task 기반)
- ❌ 고급 상태 정보 (배터리, 온도 등)

**주요 파일**:

- `firmware/src/main.cpp` - 메인 루프
- `firmware/src/mqtt_module.cpp` - MQTT 통신
- `firmware/src/camera_module.cpp` - 카메라 제어
- `firmware/src/audio_module.cpp` - 오디오 제어
- `firmware/src/display_module.cpp` - 디스플레이 제어
- `firmware/src/status_module.cpp` - 상태 보고
- `firmware/src/websocket_module.cpp` - WebSocket (미구현)

**TODO 항목** (코드 내):

- `camera_module.cpp`: RTSP 서버, WebSocket 스트리밍
- `audio_module.cpp`: 오디오 데이터 처리
- `status_module.cpp`: 배터리 레벨, 온도 센서, SD 카드 사용량

---

## 🔄 그동안 개발한 내역

### Phase 1: ASR 서버 구현 (완료)

- ASR WebSocket API 서버 구현
- VAD 통합
- 다중 세션 관리
- 응급 상황 감지
- 문서화 (5개 문서, ~100 페이지)

### Phase 2: 백엔드 프록시 API (완료)

- ASR 세션 관리 API
- ASR 서비스 클라이언트
- MQTT 명령 확장 (`start_asr`, `stop_asr`)
- 데이터 스키마 정의

### Phase 3: 펌웨어 구현 (부분 완료 후 revert)

- WebSocket 모듈 구현 시도
- 오디오 스트리밍 구현 시도
- 빌드 에러 발생 (ESP-IDF v5.x 호환성 문제)
- **Revert됨**

### Phase 4: 프론트엔드 구현 (완료)

- 음성인식 패널 컴포넌트
- 인식 결과 채팅 창
- WebSocket Hook
- 장비 상세 페이지 통합

### Phase 5: 백엔드 결과 수신 (완료)

- ASR 서버 → 백엔드 HTTP POST 통신
- WebSocket 브로드캐스트
- 응급 상황 전파

### 추가 작업

- 영상 sink 설정 기능 (프론트엔드, 백엔드, 펌웨어 설계)
- API 테스트 자동화 코드 작성
- 빌드 에러 수정 시도 (ESP-IDF v5.x 호환성)

---

## 🚨 현재 문제점

### 1. 펌웨어 빌드 에러

**문제**:

- ESP-IDF v5.x와 Arduino Core 간 호환성 문제
- M5GFX 라이브러리와 ESP-IDF 로그 시스템 충돌
- WiFi 라이브러리 IPv6 관련 에러
- `ESP_LOG_LEVEL` 매크로 미정의 에러
- `bool` 타입 재정의 에러 (C/C++ 혼합)

**시도한 해결책**:

- `esp_log_fix.h` 헤더 파일 생성
- `platformio.ini` 빌드 플래그 조정
- M5GFX 라이브러리 버전 업데이트 (0.1.17)
- `sdkconfig.h` WiFi 설정 추가
- `pre_build.py` 패치 스크립트 추가

**결과**: 부분적으로 해결되었으나 여전히 빌드 에러 발생

### 2. 펌웨어 기능 미구현

**미구현 기능**:

- ASR WebSocket 연결 및 오디오 스트리밍
- 영상 sink 전송
- 한글/일본어 텍스트 표시
- 이모티콘 그래픽 표시
- MP3 재생 (FreeRTOS Task 기반)

---

## 📋 향후 개발 계획

### ✅ Phase 1: 펌웨어 빌드 환경 안정화 (완료)

**목표**: 빌드 에러 완전 해결 및 안정적인 빌드 환경 구축

**작업 내용**:

1. **PlatformIO 환경 재설정**

   - ESP-IDF 버전 호환성 확인
   - Arduino Core 버전 확인
   - M5Stack 라이브러리 버전 확인
   - 최적의 버전 조합 찾기

2. **빌드 에러 해결**

   - ESP-IDF v5.x 호환성 문제 해결
   - M5GFX 라이브러리 충돌 해결
   - WiFi 라이브러리 에러 해결
   - C/C++ 혼합 컴파일 문제 해결

3. **빌드 스크립트 개선**
   - `pre_build.py` 패치 로직 개선
   - 자동 패치 검증
   - 빌드 실패 시 자동 롤백

**예상 시간**: 2-3시간

**성공 기준**:

- ✅ `pio run` 성공적으로 완료 ✅ **달성**
- ✅ 펌웨어 업로드 성공 (다음 단계)
- ✅ 기본 기능 동작 확인 (다음 단계)

**완료 상태**: ✅ **빌드 성공 확인됨** (2025-12-10)

---

### Phase 2: 펌웨어 기본 기능 복구 (우선순위: 높음)

**목표**: revert 전 상태로 기본 기능 복구

**작업 내용**:

1. **디스플레이 기능**

   - 텍스트 표시
   - 이모티콘 그래픽 표시 (9종)
   - 한글/일본어 UTF-8 폰트 지원

2. **오디오 기능**

   - MP3 재생 (FreeRTOS Task 기반)
   - 마이크 캡처
   - 스피커 출력

3. **카메라 기능**

   - 카메라 시작/정지
   - 기본 스트리밍

4. **상태 보고**
   - CPU 사용률
   - 메모리 사용량
   - 기본 상태 정보

**예상 시간**: 3-4시간

**성공 기준**:

- ✅ 모든 기본 제어 기능 동작
- ✅ 웹 UI에서 장비 제어 가능
- ✅ 상태 정보 정상 표시

---

### Phase 3: ASR WebSocket 통신 구현 (우선순위: 높음)

**목표**: CoreS3 → ASR 서버 WebSocket 오디오 스트리밍

**작업 내용**:

1. **WebSocket 모듈 구현**

   - `websocket_module.h` / `websocket_module.cpp`
   - WebSocket 클라이언트 연결/해제
   - 재연결 로직
   - 에러 처리

2. **오디오 스트리밍**

   - I2S 마이크 → int16 PCM 캡처
   - 바이너리 PCM 데이터 전송 (Base64 없이)
   - 16kHz, 16-bit, 모노
   - 청크 단위 전송

3. **MQTT 명령 처리**

   - `start_asr` 액션 처리
   - `stop_asr` 액션 처리
   - 세션 ID 및 WebSocket URL 수신

4. **인식 결과 수신**
   - WebSocket 메시지 수신
   - JSON 파싱
   - 디스플레이에 텍스트 표시

**예상 시간**: 4-5시간

**성공 기준**:

- ✅ ASR 서버와 WebSocket 연결 성공
- ✅ 오디오 스트리밍 정상 동작
- ✅ 인식 결과 수신 및 표시
- ✅ 프론트엔드에서 실시간 인식 결과 확인 가능

---

### Phase 4: 영상 Sink 전송 구현 (우선순위: 중간)

**목표**: 카메라 영상을 외부 서버로 전송

**작업 내용**:

1. **MJPEG 스틸컷 모드**

   - 주기적 JPEG 프레임 전송
   - HTTP POST로 전송
   - 프레임 간격 설정 가능

2. **WebSocket 스트림 모드** (선택적)

   - 실시간 WebSocket 스트리밍
   - 바이너리 JPEG 데이터 전송

3. **RTSP 스트림 모드** (선택적)
   - RTSP 서버 구현
   - 실시간 RTSP 스트리밍

**예상 시간**: 3-4시간 (MJPEG만), 6-8시간 (전체)

**성공 기준**:

- ✅ MJPEG 스틸컷 정상 동작
- ✅ 프론트엔드에서 sink URL 설정 가능
- ✅ 외부 서버로 영상 전송 확인

---

### Phase 5: 고급 기능 구현 (우선순위: 낮음)

**목표**: 추가 기능 및 최적화

**작업 내용**:

1. **상태 정보 고도화**

   - 배터리 레벨 (AXP2101)
   - 온도 센서
   - SD 카드 사용량

2. **성능 최적화**

   - 메모리 사용량 최적화
   - CPU 사용률 최적화
   - 네트워크 대역폭 최적화

3. **에러 처리 강화**
   - 자동 재연결 로직
   - 에러 복구 메커니즘
   - 상세한 로깅

**예상 시간**: 4-6시간

---

## 🎯 단계별 우선순위

### 즉시 진행 (1주일 내)

1. **Phase 1: 빌드 환경 안정화** (2-3시간)

   - 빌드 에러 완전 해결
   - 안정적인 빌드 환경 구축

2. **Phase 2: 기본 기능 복구** (3-4시간)
   - revert 전 상태로 복구
   - 기본 제어 기능 동작 확인

### 단기 목표 (2주일 내)

3. **Phase 3: ASR WebSocket 통신** (4-5시간)
   - 음성인식 기능 완전 구현
   - 전체 시스템 통합 완료

### 중기 목표 (1개월 내)

4. **Phase 4: 영상 Sink 전송** (3-4시간)

   - MJPEG 스틸컷 구현
   - 영상 전송 기능 완성

5. **Phase 5: 고급 기능** (4-6시간)
   - 상태 정보 고도화
   - 성능 최적화

---

## 📝 개발 체크리스트

### Phase 1: 빌드 환경 안정화

- [ ] PlatformIO 버전 확인 및 업데이트
- [ ] ESP-IDF 버전 호환성 확인
- [ ] Arduino Core 버전 확인
- [ ] M5Stack 라이브러리 버전 확인
- [ ] 빌드 에러 완전 해결
- [ ] 펌웨어 업로드 성공
- [ ] 기본 동작 확인

### Phase 2: 기본 기능 복구

- [ ] 디스플레이 텍스트 표시
- [ ] 이모티콘 그래픽 표시
- [ ] 한글/일본어 폰트 지원
- [ ] MP3 재생 기능
- [ ] 마이크/스피커 기본 기능
- [ ] 카메라 기본 기능
- [ ] 상태 보고 기능

### Phase 3: ASR WebSocket 통신

- [ ] WebSocket 모듈 구현
- [ ] 오디오 스트리밍 구현
- [ ] MQTT 명령 처리
- [ ] 인식 결과 수신 및 표시
- [ ] 통합 테스트

### Phase 4: 영상 Sink 전송

- [ ] MJPEG 스틸컷 구현
- [ ] 프론트엔드 연동
- [ ] 외부 서버 전송 테스트
- [ ] (선택) WebSocket 스트림
- [ ] (선택) RTSP 스트림

### Phase 5: 고급 기능

- [ ] 배터리 레벨 측정
- [ ] 온도 센서 읽기
- [ ] SD 카드 사용량
- [ ] 성능 최적화
- [ ] 에러 처리 강화

---

## 🔧 기술 스택 요약

### 프론트엔드

- **프레임워크**: Next.js 14 (App Router)
- **상태 관리**: React Query, Zustand
- **스타일링**: Tailwind CSS
- **HTTP 클라이언트**: Axios
- **WebSocket**: Native WebSocket API

### 백엔드

- **프레임워크**: FastAPI
- **데이터베이스**: SQLite (개발), PostgreSQL (운영 예정)
- **ORM**: SQLAlchemy
- **MQTT**: paho-mqtt
- **WebSocket**: FastAPI WebSocket
- **HTTP 클라이언트**: httpx

### ASR 서버

- **프레임워크**: FastAPI
- **음성인식**: Sherpa-ONNX
- **VAD**: demo_vad_final.py
- **플랫폼**: RK3588 (NPU 최적화)

### 펌웨어

- **플랫폼**: ESP32-S3 (M5Stack Core S3)
- **프레임워크**: Arduino Core
- **통신**: WiFi, MQTT, WebSocket
- **하드웨어**: M5Unified, M5GFX, ESP32-Camera

---

## 📚 참고 문서

### 완료 보고서

- `docs/PHASE1_COMPLETION_REPORT.md` - ASR 서버 구현
- `docs/asr_integration/PHASE2_COMPLETE.md` - 백엔드 프록시 API
- `docs/asr_integration/PHASE4_COMPLETE.md` - 프론트엔드 구현
- `docs/asr_integration/PHASE5_COMPLETE.md` - 백엔드 결과 수신
- `docs/camera_sink/PHASE2_COMPLETE.md` - 영상 sink 프론트엔드

### 설계 문서

- `docs/asr_integration/01_architecture.md` - 시스템 아키텍처
- `docs/asr_integration/02_api_specification.md` - API 명세서
- `docs/asr_integration/03_functions_detail.md` - 함수 상세
- `docs/asr_integration/04_deployment_guide.md` - 배포 가이드
- `docs/camera_sink/DESIGN.md` - 영상 sink 설계

### 테스트 문서

- `docs/API_TEST_REPORT.md` - API 테스트 보고서
- `docs/API_TEST_RESULTS_TEMPLATE.md` - 테스트 결과 템플릿

---

## 🎯 최종 목표

### 완전한 음성인식 시스템

- ✅ ASR 서버 (완료)
- ✅ 백엔드 프록시 (완료)
- ✅ 프론트엔드 UI (완료)
- ❌ 펌웨어 WebSocket 통신 (미완료)

### 완전한 장비 관리 시스템

- ✅ 장비 등록/관리 (완료)
- ✅ 장비 제어 (완료)
- ✅ 상태 모니터링 (완료)
- ❌ 영상 sink 전송 (부분 완료)

### 안정적인 빌드 환경

- ✅ 빌드 에러 해결 (완료)
- ✅ 안정적인 빌드 프로세스 (완료)

---

**작성일**: 2025-12-10  
**상태**: Phase 1 완료, Phase 2 준비 중  
**다음 단계**: Phase 2 - 기본 기능 복구

---

## ✅ Phase 1 완료 (2025-12-10)

### 빌드 환경 안정화 완료

- ✅ PlatformIO 설정 최적화
- ✅ 빌드 전 스크립트 단순화
- ✅ 불필요한 설정 제거
- ✅ **빌드 성공 확인**

**변경된 파일**:
- `firmware/platformio.ini` - 최소한의 필수 설정만 유지
- `firmware/pre_build.py` - M5GFX 라이브러리 패치만 유지

**상세 내용**: `docs/firmware/PHASE1_BUILD_STABILIZATION_COMPLETE.md` 참조
