# API 테스트 결과 보고서

**생성 일시**: 2025-12-08  
**테스트 범위**: 전체 백엔드 API 엔드포인트  
**테스트 도구**: `backend/test_all_apis.py`

---

## 테스트 요약

| 항목                     | 값                                |
| ------------------------ | --------------------------------- |
| 총 API 엔드포인트        | 35개                              |
| 테스트 가능한 엔드포인트 | 35개                              |
| 테스트 스크립트          | `backend/test_all_apis.py`        |
| 테스트 실행 방법         | `python backend/test_all_apis.py` |

**참고**: 실제 테스트 실행을 위해서는 백엔드 서버가 `http://localhost:8000`에서 실행 중이어야 합니다.

---

## API 그룹별 엔드포인트 목록

### 1. 시스템 API

| API 이름  | 메서드 | 엔드포인트 | 설명              | 인증 필요 |
| --------- | ------ | ---------- | ----------------- | --------- |
| 루트      | GET    | `/`        | 애플리케이션 정보 | ❌        |
| 헬스 체크 | GET    | `/health`  | 서버 상태 확인    | ❌        |

### 2. 인증 API (`/auth`)

| API 이름         | 메서드 | 엔드포인트       | 설명                                 | 인증 필요 |
| ---------------- | ------ | ---------------- | ------------------------------------ | --------- |
| 사용자 등록      | POST   | `/auth/register` | 새 사용자 등록                       | ❌        |
| 로그인           | POST   | `/auth/login`    | 사용자 로그인                        | ❌        |
| 토큰 갱신        | POST   | `/auth/refresh`  | Refresh 토큰으로 새 Access 토큰 발급 | ❌        |
| 로그아웃         | POST   | `/auth/logout`   | 사용자 로그아웃                      | ✅        |
| 현재 사용자 조회 | GET    | `/auth/me`       | 현재 로그인한 사용자 정보            | ✅        |

### 3. 사용자 관리 API (`/users`)

| API 이름         | 메서드 | 엔드포인트           | 설명                       | 인증 필요 | 권한  |
| ---------------- | ------ | -------------------- | -------------------------- | --------- | ----- |
| 사용자 목록 조회 | GET    | `/users/`            | 사용자 목록 (페이지네이션) | ✅        | ADMIN |
| 사용자 상세 조회 | GET    | `/users/{user_id}`   | 특정 사용자 정보           | ✅        | ADMIN |
| 사용자 생성      | POST   | `/users/`            | 새 사용자 생성             | ✅        | ADMIN |
| 사용자 정보 수정 | PUT    | `/users/{user_id}`   | 사용자 정보 수정           | ✅        | ADMIN |
| 사용자 삭제      | DELETE | `/users/{user_id}`   | 사용자 삭제                | ✅        | ADMIN |
| 비밀번호 변경    | PUT    | `/users/me/password` | 본인 비밀번호 변경         | ✅        | 본인  |

### 4. 장비 관리 API (`/devices`)

| API 이름            | 메서드 | 엔드포인트                           | 설명                                  | 인증 필요 | 권한                     |
| ------------------- | ------ | ------------------------------------ | ------------------------------------- | --------- | ------------------------ |
| 장비 목록 조회      | GET    | `/devices/`                          | 장비 목록 (페이지네이션, 필터링)      | ⚠️        | VIEWER (현재 비활성화)   |
| 장비 상세 조회      | GET    | `/devices/{device_id}`               | 특정 장비 정보                        | ⚠️        | VIEWER (현재 비활성화)   |
| 장비 등록           | POST   | `/devices/`                          | 새 장비 등록                          | ⚠️        | OPERATOR (현재 비활성화) |
| 장비 정보 수정      | PUT    | `/devices/{device_id}`               | 장비 정보 수정                        | ⚠️        | OPERATOR (현재 비활성화) |
| 장비 삭제           | DELETE | `/devices/{device_id}`               | 장비 삭제                             | ✅        | ADMIN                    |
| 장비 상태 기록      | POST   | `/devices/{device_id}/status`        | 장비 상태 데이터 기록 (장비에서 호출) | ⚠️        | VIEWER (현재 비활성화)   |
| 장비 상태 이력 조회 | GET    | `/devices/{device_id}/status`        | 장비 상태 이력 조회                   | ✅        | VIEWER                   |
| 장비 최신 상태 조회 | GET    | `/devices/{device_id}/status/latest` | 장비 최신 상태 조회                   | ⚠️        | VIEWER (현재 비활성화)   |

**참고**: ⚠️ 표시는 현재 인증이 비활성화되어 있지만, 향후 활성화 예정인 엔드포인트입니다.

### 5. 장비 제어 API (`/control`)

| API 이름        | 메서드 | 엔드포인트                                | 설명                                     | 인증 필요 | 권한                     |
| --------------- | ------ | ----------------------------------------- | ---------------------------------------- | --------- | ------------------------ |
| 카메라 제어     | POST   | `/control/devices/{device_id}/camera`     | 카메라 시작/일시정지/중지                | ⚠️        | OPERATOR (현재 비활성화) |
| 마이크 제어     | POST   | `/control/devices/{device_id}/microphone` | 마이크 시작/일시정지/중지, ASR 시작/중지 | ⚠️        | OPERATOR (현재 비활성화) |
| 스피커 제어     | POST   | `/control/devices/{device_id}/speaker`    | 오디오 재생/중지                         | ⚠️        | OPERATOR (현재 비활성화) |
| 디스플레이 제어 | POST   | `/control/devices/{device_id}/display`    | 텍스트/이모지 표시, 화면 지우기          | ⚠️        | OPERATOR (현재 비활성화) |
| 시스템 제어     | POST   | `/control/devices/{device_id}/system`     | 장비 재시작                              | ⚠️        | OPERATOR (현재 비활성화) |

### 6. 오디오 파일 관리 API (`/audio`)

| API 이름             | 메서드 | 엔드포인트          | 설명                             | 인증 필요 | 권한                     |
| -------------------- | ------ | ------------------- | -------------------------------- | --------- | ------------------------ |
| 오디오 파일 업로드   | POST   | `/audio/upload`     | MP3 파일 업로드 (파일 검증 포함) | ⚠️        | OPERATOR (현재 비활성화) |
| 오디오 파일 목록     | GET    | `/audio/list`       | 업로드된 오디오 파일 목록        | ⚠️        | OPERATOR (현재 비활성화) |
| 오디오 파일 다운로드 | GET    | `/audio/{filename}` | 오디오 파일 다운로드             | ⚠️        | OPERATOR (현재 비활성화) |
| 오디오 파일 삭제     | DELETE | `/audio/{filename}` | 오디오 파일 삭제                 | ✅        | OPERATOR                 |

### 7. ASR (음성인식) API (`/asr`)

| API 이름           | 메서드 | 엔드포인트                                | 설명                                         | 인증 필요 | 권한                     |
| ------------------ | ------ | ----------------------------------------- | -------------------------------------------- | --------- | ------------------------ |
| ASR 세션 시작      | POST   | `/asr/devices/{device_id}/session/start`  | 장비의 음성인식 세션 시작                    | ⚠️        | OPERATOR (현재 비활성화) |
| ASR 세션 종료      | POST   | `/asr/devices/{device_id}/session/stop`   | 장비의 음성인식 세션 종료                    | ⚠️        | OPERATOR (현재 비활성화) |
| ASR 세션 상태 조회 | GET    | `/asr/devices/{device_id}/session/status` | 장비의 ASR 세션 상태 조회                    | ⚠️        | OPERATOR (현재 비활성화) |
| 모든 ASR 세션 조회 | GET    | `/asr/sessions`                           | 시스템의 모든 활성 ASR 세션 목록             | ⚠️        | ADMIN (현재 비활성화)    |
| ASR 서버 헬스 체크 | GET    | `/asr/health`                             | ASR 서버 상태 확인                           | ❌        | -                        |
| ASR 결과 수신      | POST   | `/asr/result`                             | ASR 서버로부터 음성인식 결과 수신 (내부 API) | ❌        | -                        |

### 8. WebSocket API

| API 이름       | 타입 | 엔드포인트 | 설명                                 | 인증 필요 |
| -------------- | ---- | ---------- | ------------------------------------ | --------- |
| WebSocket 연결 | WS   | `/ws`      | 실시간 통신 (장비 상태, ASR 결과 등) | ⚠️        |

---

## 테스트 실행 방법

### 1. 사전 요구사항

```bash
# 백엔드 의존성 설치
cd backend
pip install httpx fastapi uvicorn

# 백엔드 서버 실행 (별도 터미널)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. 테스트 실행

```bash
# 테스트 스크립트 실행
cd backend
python test_all_apis.py
```

### 3. 테스트 결과 확인

테스트 결과는 다음 위치에 저장됩니다:

- JSON 형식: `backend/test_results/api_test_results_YYYYMMDD_HHMMSS.json`
- 콘솔 출력: 실시간 테스트 진행 상황 및 결과 요약

### 4. 마크다운 보고서 생성 (선택사항)

```bash
# JSON 결과를 마크다운으로 변환
python backend/generate_test_report.py backend/test_results/api_test_results_YYYYMMDD_HHMMSS.json docs/API_TEST_RESULT.md
```

---

## 예상 테스트 결과

### 성공 케이스

다음 API들은 정상적으로 동작해야 합니다:

1. **시스템 API**

   - `GET /` → 200 OK
   - `GET /health` → 200 OK

2. **인증 API**

   - `POST /auth/register` → 201 Created (새 사용자) 또는 400 Bad Request (중복)
   - `POST /auth/login` → 200 OK (유효한 자격증명)
   - `GET /auth/me` → 200 OK (유효한 토큰)
   - `POST /auth/refresh` → 200 OK (유효한 Refresh 토큰)

3. **장비 관리 API**

   - `GET /devices/` → 200 OK
   - `GET /devices/{device_id}` → 200 OK (존재하는 장비) 또는 404 Not Found (없는 장비)
   - `POST /devices/` → 201 Created (새 장비) 또는 400 Bad Request (중복)
   - `PUT /devices/{device_id}` → 200 OK (존재하는 장비)
   - `GET /devices/{device_id}/status/latest` → 200 OK (상태 있음) 또는 404 Not Found (상태 없음)

4. **장비 제어 API**

   - `POST /control/devices/{device_id}/camera` → 200 OK (온라인 장비) 또는 400 Bad Request (오프라인 장비)
   - `POST /control/devices/{device_id}/microphone` → 200 OK (온라인 장비)
   - `POST /control/devices/{device_id}/display` → 200 OK (온라인 장비)

5. **오디오 파일 관리 API**

   - `GET /audio/list` → 200 OK
   - `POST /audio/upload` → 201 Created (유효한 파일) 또는 400 Bad Request (유효하지 않은 파일)

6. **ASR API**
   - `GET /asr/health` → 200 OK (ASR 서버 연결됨) 또는 500 Internal Server Error (ASR 서버 미연결)
   - `GET /asr/devices/{device_id}/session/status` → 200 OK

### 실패 케이스 (정상 동작)

다음은 의도된 실패 케이스입니다:

1. **인증 실패**

   - `POST /auth/login` → 401 Unauthorized (잘못된 자격증명)
   - `GET /auth/me` → 401 Unauthorized (유효하지 않은 토큰)

2. **리소스 없음**

   - `GET /devices/99999` → 404 Not Found (존재하지 않는 장비)
   - `GET /devices/{device_id}/status/latest` → 404 Not Found (상태 정보 없음)

3. **권한 부족**

   - `DELETE /devices/{device_id}` → 403 Forbidden (ADMIN 권한 필요)
   - `GET /users/` → 403 Forbidden (ADMIN 권한 필요)

4. **장비 오프라인**

   - `POST /control/devices/{device_id}/camera` → 400 Bad Request (장비가 오프라인)

5. **파일 검증 실패**
   - `POST /audio/upload` → 400 Bad Request (유효하지 않은 파일 형식 또는 크기 초과)

---

## 테스트 커버리지

| API 그룹             | 총 엔드포인트 | 테스트 커버리지 | 비고                                           |
| -------------------- | ------------- | --------------- | ---------------------------------------------- |
| 시스템 API           | 2             | 100% (2/2)      | -                                              |
| 인증 API             | 5             | 100% (5/5)      | -                                              |
| 사용자 관리 API      | 6             | 0% (0/6)        | ADMIN 권한 필요, 현재 테스트 스크립트에서 제외 |
| 장비 관리 API        | 8             | 87.5% (7/8)     | DELETE는 ADMIN 권한 필요                       |
| 장비 제어 API        | 5             | 100% (5/5)      | 시스템 재시작은 스킵                           |
| 오디오 파일 관리 API | 4             | 50% (2/4)       | 업로드/목록만 테스트, 다운로드/삭제는 제외     |
| ASR API              | 6             | 33% (2/6)       | 헬스 체크 및 세션 상태만 테스트                |
| WebSocket API        | 1             | 0% (0/1)        | WebSocket 테스트는 별도 도구 필요              |
| **전체**             | **37**        | **62% (23/37)** | -                                              |

---

## 테스트 시 주의사항

1. **백엔드 서버 실행 필요**

   - 테스트 실행 전에 백엔드 서버가 `http://localhost:8000`에서 실행 중이어야 합니다.

2. **데이터베이스 초기화**

   - 테스트는 실제 데이터베이스를 사용하므로, 테스트 환경에서는 별도 데이터베이스를 사용하는 것을 권장합니다.

3. **MQTT 브로커**

   - 장비 제어 API 테스트는 MQTT 브로커가 실행 중이어야 정상 동작합니다.
   - MQTT 브로커가 없어도 API는 응답하지만, 실제 명령 전송은 실패할 수 있습니다.

4. **ASR 서버**

   - ASR API 테스트는 ASR 서버(`http://10.10.11.17:8001`)가 실행 중이어야 합니다.
   - ASR 서버가 없어도 헬스 체크는 실패하지만, 다른 API는 정상 동작합니다.

5. **인증 토큰**

   - 일부 테스트는 인증 토큰이 필요합니다.
   - 테스트 스크립트는 자동으로 로그인하여 토큰을 획득합니다.

6. **장비 상태**
   - 장비 제어 API 테스트는 실제 온라인 장비가 있어야 완전한 테스트가 가능합니다.
   - 오프라인 장비에 대한 테스트는 400 Bad Request 응답을 받는 것이 정상입니다.

---

## 향후 개선 사항

1. **테스트 커버리지 향상**

   - 사용자 관리 API 테스트 추가 (ADMIN 권한 계정 필요)
   - WebSocket API 테스트 추가
   - ASR 세션 시작/종료 테스트 추가

2. **통합 테스트**

   - pytest 기반 테스트 프레임워크 도입
   - 테스트 데이터베이스 분리
   - CI/CD 파이프라인 통합

3. **성능 테스트**

   - 부하 테스트 추가
   - 응답 시간 모니터링
   - 동시성 테스트

4. **보안 테스트**
   - 인증/인가 테스트 강화
   - 입력 검증 테스트
   - SQL Injection, XSS 등 보안 취약점 테스트

---

## 참고 자료

- **FastAPI 공식 문서**: https://fastapi.tiangolo.com/
- **httpx 문서**: https://www.python-httpx.org/
- **테스트 스크립트**: `backend/test_all_apis.py`
- **보고서 생성 스크립트**: `backend/generate_test_report.py`
- **API 명세서**: `docs/asr_integration/02_api_specification.md`

---

**문서 작성일**: 2025-12-08  
**최종 업데이트**: 2025-12-08
