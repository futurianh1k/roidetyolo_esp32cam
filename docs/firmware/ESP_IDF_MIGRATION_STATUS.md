# ESP-IDF 마이그레이션 진행 상황

**작성일:** 2025-12-10  
**브랜치:** `feature/esp-idf-migration`

---

## 완료된 작업 ✅

### Phase 1: 프로젝트 구조 생성
- [x] `firmware_idf/` 디렉토리 생성
- [x] 루트 `CMakeLists.txt` 생성
- [x] `main/CMakeLists.txt` 생성
- [x] `main/idf_component.yml` 생성
- [x] `History/ESP_IDF_MIGRATION_2025-12-10.md` 문서화

### Phase 2: 메인 애플리케이션 클래스
- [x] `Application` 싱글톤 클래스 구현
- [x] 이벤트 그룹 설정
- [x] 메인 이벤트 루프 (`Application::Run()`)
- [x] 스케줄링 시스템 (`Application::Schedule()`)
- [x] `main.cc` 진입점 구현

### Phase 3: 상태 머신
- [x] `DeviceState` 열거형 정의
- [x] `DeviceStateMachine` 클래스 구현
- [x] 상태 전환 검증 로직
- [x] 상태 변경 콜백 시스템

---

## 진행 중인 작업 🚧

### Phase 4: 오디오 모듈 ESP-IDF 변환
- [ ] I2S 드라이버 ESP-IDF 변환
- [ ] 오디오 입력 태스크 생성
- [ ] 오디오 출력 태스크 생성
- [ ] FreeRTOS 큐 구현

---

## 예정된 작업 📋

### Phase 5: 카메라 모듈 ESP-IDF 변환
- [ ] `esp_camera` API 사용
- [ ] 카메라 태스크 생성
- [ ] JPEG 인코딩 태스크

### Phase 6: 네트워크 모듈 ESP-IDF 변환
- [ ] WiFi ESP-IDF API 변환
- [ ] MQTT 클라이언트 (ESP-IDF)
- [ ] WebSocket 클라이언트

### Phase 7: 디스플레이 모듈 ESP-IDF 변환
- [ ] M5Stack 디스플레이 ESP-IDF 변환

---

## 파일 구조

```
firmware_idf/
├── CMakeLists.txt                    ✅
├── main/
│   ├── CMakeLists.txt                ✅
│   ├── idf_component.yml             ✅
│   ├── main.cc                       ✅
│   ├── application.h                 ✅
│   ├── application.cc                ✅
│   ├── device_state.h                ✅
│   ├── device_state_machine.h        ✅
│   ├── device_state_machine.cc       ✅
│   ├── audio/                        ⏳
│   ├── camera/                       ⏳
│   ├── network/                      ⏳
│   ├── display/                      ⏳
│   └── status/                       ⏳
└── README.md                         ✅
```

---

## 다음 단계

1. **오디오 모듈 변환 시작**
   - I2S 드라이버 ESP-IDF 변환
   - 오디오 입력/출력 태스크 생성
   - xiaozhi-esp32의 `audio_service.cc` 참고

2. **네트워크 모듈 변환**
   - WiFi ESP-IDF API 사용
   - MQTT 클라이언트 구현

3. **통합 테스트**
   - 각 모듈별 테스트
   - 전체 시스템 통합 테스트

---

## 참고 자료

- **xiaozhi-esp32:** `xiaozhi-esp32/main/` 디렉토리
- **ESP-IDF 문서:** https://docs.espressif.com/projects/esp-idf/
- **FreeRTOS 문서:** https://www.freertos.org/

---

**작성자:** AI Assistant  
**마지막 업데이트:** 2025-12-10

