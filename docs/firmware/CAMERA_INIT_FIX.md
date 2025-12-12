# 카메라 초기화 오류 해결 가이드

**문제:** ESP32 카메라 초기화 시 I2C/SCCB 오류 발생

---

## 🔍 문제 원인

```
E (4193) i2c: i2c driver install error
E (4194) camera: sccb init err
E (4194) camera: Camera probe failed with error 0xffffffff(ESP_FAIL)
```

**가능한 원인:**
1. I2C 버스 충돌 (M5.begin()이 이미 I2C를 초기화)
2. 카메라 하드웨어 안정화 시간 부족
3. PSRAM 설정 문제
4. 카메라 핀 설정 오류
5. 하드웨어 연결 문제

---

## ✅ 해결 방법

### 1. 코드 개선 (완료)

다음 개선 사항이 적용되었습니다:

- **I2C 버스 정리**: 카메라 초기화 전에 I2C 버스 재시작
- **재시도 로직**: 최대 3회 재시도
- **상세 에러 메시지**: 오류 유형별 메시지 출력
- **하드웨어 안정화 지연**: 초기화 전 충분한 지연 시간

### 2. 하드웨어 확인

**카메라 연결 확인:**
1. FPC 케이블이 올바르게 연결되어 있는지 확인
2. 케이블이 느슨하지 않은지 확인
3. 케이블 손상 여부 확인

**전원 공급 확인:**
- M5Stack Core S3는 USB-C로 충전/전원 공급
- 충전 중이거나 배터리가 부족하면 카메라 초기화 실패 가능
- 안정적인 전원 공급 확인

### 3. 펌웨어 재컴파일 및 업로드

```bash
cd firmware
pio run -t upload
```

### 4. 시리얼 모니터 확인

업로드 후 시리얼 모니터에서 다음 메시지 확인:

```
Initializing camera...
Camera pins: XCLK=2, SIOD=12, SIOC=11
Camera pins: PWDN=-1, RESET=-1
Camera initialized successfully
```

---

## 🔧 추가 문제 해결

### 문제 1: 여전히 I2C 오류 발생

**해결:**
1. M5Stack Core S3 재부팅
2. USB 케이블 교체 (고품질 케이블 사용)
3. 다른 USB 포트 사용

### 문제 2: 카메라가 감지되지 않음

**해결:**
1. FPC 케이블 재연결
2. 카메라 모듈 교체 테스트
3. 핀 설정 확인 (`firmware/include/pins.h`)

### 문제 3: PSRAM 오류

**확인:**
- `platformio.ini`에서 PSRAM 설정 확인:
  ```ini
  board_build.arduino.memory_type = qio_opi
  ```

---

## 📝 변경 사항

### `firmware/src/camera_module.cpp`

1. **I2C 버스 정리 추가:**
   ```cpp
   Wire.end();  // 기존 I2C 연결 종료
   delay(100);
   Wire.begin();  // I2C 버스 재시작
   ```

2. **재시도 로직 추가:**
   - 최대 3회 재시도
   - 각 재시도 간 500ms 지연

3. **상세 에러 메시지:**
   - `ESP_ERR_CAMERA_NOT_DETECTED`: 카메라 미감지
   - `ESP_ERR_CAMERA_INIT_FAIL`: 초기화 실패
   - `ESP_ERR_NO_MEM`: 메모리 부족

4. **프레임 버퍼 설정 변경:**
   - `fb_count`: 2 → 1 (M5Stack Core S3 권장)
   - `grab_mode`: `CAMERA_GRAB_LATEST` → `CAMERA_GRAB_WHEN_EMPTY`

### `firmware/src/main.cpp`

1. **초기화 순서 개선:**
   - WiFi 연결 후 500ms 지연 추가
   - 카메라 실패 시에도 시스템 계속 동작

---

## 🧪 테스트

1. **펌웨어 업로드**
2. **시리얼 모니터 확인**
3. **카메라 제어 테스트:**
   - 프론트엔드에서 카메라 시작 명령 전송
   - MQTT 응답 확인

---

## 📚 참고 자료

- M5Stack Core S3 핀아웃: https://docs.m5stack.com/en/core/CoreS3
- ESP32-Camera 라이브러리: https://github.com/espressif/esp32-camera

---

**작성일:** 2025-12-10  
**상태:** ✅ 수정 완료

