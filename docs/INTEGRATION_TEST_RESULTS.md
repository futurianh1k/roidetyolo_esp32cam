# 통합 테스트 결과

**테스트 일시**: 2025-01-13  
**버전**: 1.0.0  
**테스트 환경**: Windows 10, Python 3.13

---

## 1. 테스트 개요

백엔드, 프론트엔드, 펌웨어 간의 통합 테스트를 수행했습니다.

### 테스트 대상

- **백엔드**: FastAPI (http://localhost:8000)
- **프론트엔드**: Next.js (http://localhost:3000)
- **펌웨어**: ESP32-S3 Core S3 (시뮬레이션)

---

## 2. 테스트 결과 요약

| 테스트 항목                        | 결과    | 비고           |
| ---------------------------------- | ------- | -------------- |
| 백엔드 서버 상태                   | ✅ 성공 |                |
| 장비 목록 조회                     | ✅ 성공 | 1개 장비 확인  |
| 장비 상세 조회                     | ✅ 성공 |                |
| 장비 상태 기록 (펌웨어 시뮬레이션) | ✅ 성공 |                |
| 장비 최신 상태 조회                | ✅ 성공 |                |
| 카메라 제어 명령                   | ✅ 성공 | MQTT 전송 확인 |
| 마이크(ASR) 제어 명령              | ✅ 성공 | MQTT 전송 확인 |
| 디스플레이 제어 명령               | ✅ 성공 | MQTT 전송 확인 |

**총 결과: 8/8 테스트 통과 (100%)**

---

## 3. 테스트 상세

### 3.1 백엔드 서버 상태 확인

```
GET /
응답: {'app': 'CoreS3 Management System', 'version': '1.0.0', 'status': 'running'}
```

### 3.2 장비 목록 조회

```
GET /devices/
응답: 1개 장비 (ID: 4, 이름: core c3 cam mic, 상태: Offline)
```

### 3.3 장비 상세 조회

```
GET /devices/4
응답:
  - ID: 4
  - 이름: core c3 cam mic
  - 타입: CoreS3
  - 온라인: False
  - IP: 10.10.11.83
```

### 3.4 장비 상태 기록 (펌웨어 → 백엔드)

```
POST /devices/4/status
요청:
{
  "battery_level": 85,
  "memory_usage": 150000,
  "storage_usage": null,
  "temperature": 42.5,
  "cpu_usage": 25,
  "camera_status": "active",
  "mic_status": "stopped"
}
응답: 201 Created
```

### 3.5 장비 최신 상태 조회

```
GET /devices/4/status/latest
응답:
  - 배터리: 85%
  - 메모리: 150000 bytes
  - 온도: 42.5°C
  - CPU: 25%
  - 카메라: active
  - 마이크: stopped
```

### 3.6 카메라 제어 명령

```
POST /control/devices/4/camera
요청: {"action": "start"}
응답: {'success': True, 'message': '카메라 start 명령을 전송했습니다'}
```

### 3.7 마이크(ASR) 제어 명령

```
POST /control/devices/4/microphone
요청: {"action": "start_asr", "language": "ko"}
응답: {'success': True, 'message': '마이크 start_asr 명령을 전송했습니다'}
```

### 3.8 디스플레이 제어 명령

```
POST /control/devices/4/display
요청: {"action": "show_text", "content": "통합 테스트 메시지"}
응답: {'success': True, 'message': '디스플레이 show_text 명령을 전송했습니다'}
```

---

## 4. 확인된 사항

### 4.1 API 필드명

| 컴포넌트        | 필드명    | 설명                          |
| --------------- | --------- | ----------------------------- |
| 디스플레이 제어 | `content` | 표시할 텍스트 (`text`가 아님) |

### 4.2 장비 온라인 상태

- 장비 상태 기록 시 `last_seen_at` 자동 업데이트
- 60초 이상 상태 보고 없으면 자동 오프라인 처리

---

## 5. 테스트 스크립트

```bash
# 통합 테스트 실행
python tests/integration_test.py

# 특정 장비 ID로 테스트
$env:DEVICE_ID="4"; python tests/integration_test.py

# 다른 백엔드 URL 사용
$env:BACKEND_URL="http://10.10.11.18:8000"; python tests/integration_test.py
```

---

## 6. 다음 단계

1. **펌웨어 실제 테스트**

   - 빌드 완료된 펌웨어를 장비에 플래시
   - 실제 장비에서 상태 전송 확인
   - MQTT 명령 수신 및 처리 확인

2. **프론트엔드 E2E 테스트**

   - Selenium 기반 테스트 실행
   - 대시보드 기능 검증

3. **부하 테스트**
   - 다수 장비 동시 상태 전송
   - MQTT 메시지 처리 성능

---

## 참고

- 테스트 스크립트: `tests/integration_test.py`
- 서버 시작 스크립트: `start_servers.ps1`
- 펌웨어 빌드: `firmware_idf/build.ps1`
