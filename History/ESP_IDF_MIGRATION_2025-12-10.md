# ESP-IDF 마이그레이션 및 FreeRTOS 멀티태스크 구조 전환

**작성일:** 2025-12-10  
**브랜치:** `feature/esp-idf-migration`  
**변경 유형:** 중대한 변경 (프레임워크 전환)

---

## 변경 사항 요약

### 이전 상태
- **프레임워크:** PlatformIO + Arduino
- **아키텍처:** 단일 루프 (`setup()` + `loop()`)
- **빌드 시스템:** PlatformIO
- **메모리 관리:** Arduino 스타일

### 변경 후 상태
- **프레임워크:** ESP-IDF (네이티브)
- **아키텍처:** FreeRTOS 멀티태스크
- **빌드 시스템:** CMake (ESP-IDF)
- **메모리 관리:** FreeRTOS 태스크 기반

---

## 마이그레이션 목표

1. **ESP-IDF 네이티브 API 사용**
   - `esp_log.h` (로깅)
   - `freertos/FreeRTOS.h` (태스크 관리)
   - `driver/i2s.h` (I2S 드라이버)
   - `esp_camera.h` (카메라)

2. **FreeRTOS 멀티태스크 구조**
   - 오디오 입력 태스크
   - 오디오 출력 태스크
   - 카메라 태스크
   - 네트워크 태스크
   - 메인 이벤트 루프 태스크

3. **상태 머신 구현**
   - `DeviceStateMachine` 클래스
   - 상태 전환 검증
   - 상태 변경 콜백

4. **Application 싱글톤 패턴**
   - 이벤트 그룹 기반 통신
   - 스레드 안전한 상태 관리

---

## 참고 자료

- **xiaozhi-esp32 프로젝트:** ESP-IDF 기반 완전한 구현 참고
- **ESP-IDF 공식 문서:** https://docs.espressif.com/projects/esp-idf/
- **FreeRTOS 문서:** https://www.freertos.org/

---

## 마이그레이션 단계

### Phase 1: 프로젝트 구조 생성 ✅
- CMakeLists.txt 생성
- main/ 디렉토리 구조 생성
- idf_component.yml 생성

### Phase 2: 메인 애플리케이션 클래스
- Application 싱글톤 구현
- 이벤트 그룹 설정
- 메인 이벤트 루프

### Phase 3: 상태 머신
- DeviceStateMachine 구현
- 상태 정의 및 전환 로직

### Phase 4: 오디오 모듈 변환
- I2S 드라이버 ESP-IDF 변환
- 오디오 입력/출력 태스크
- FreeRTOS 큐 사용

### Phase 5: 카메라 모듈 변환
- esp_camera API 사용
- 카메라 태스크 생성
- JPEG 인코딩 태스크

### Phase 6: 네트워크 모듈 변환
- WiFi ESP-IDF API
- MQTT 클라이언트 (ESP-IDF)
- WebSocket 클라이언트

### Phase 7: 디스플레이 모듈 변환
- M5Stack 디스플레이 ESP-IDF 변환

---

## 예상 작업량

- **Phase 1-3:** 2일
- **Phase 4:** 2일
- **Phase 5:** 1일
- **Phase 6:** 2일
- **Phase 7:** 1일
- **테스트 및 디버깅:** 2일

**총 예상 작업량:** 10일

---

## 리스크 및 고려사항

1. **하드웨어 호환성**
   - M5Stack Core S3 핀 매핑 확인 필요
   - I2S 설정 검증 필요

2. **메모리 사용량**
   - FreeRTOS 태스크 스택 크기 조정
   - PSRAM 활용 최적화

3. **성능**
   - 태스크 우선순위 설정
   - CPU 코어 할당 (ESP32-S3는 듀얼 코어)

4. **호환성**
   - 기존 백엔드 서버와의 통신 프로토콜 유지
   - MQTT/WebSocket 프로토콜 호환성

---

## 테스트 계획

1. **단위 테스트**
   - 각 모듈별 독립 테스트
   - 상태 머신 전환 테스트

2. **통합 테스트**
   - 오디오 + 네트워크 통합
   - 카메라 + 네트워크 통합
   - 전체 시스템 통합

3. **성능 테스트**
   - 메모리 사용량 측정
   - CPU 사용률 측정
   - 지연 시간 측정

---

## 롤백 계획

기존 PlatformIO 버전은 `main` 브랜치에 유지되며, 문제 발생 시 즉시 롤백 가능.

---

**작성자:** AI Assistant  
**검토 필요:** 프로젝트 리더

