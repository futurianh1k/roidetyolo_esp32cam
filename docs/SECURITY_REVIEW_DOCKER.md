# 🔒 Docker 배포 보안 검토 보고서

## 검토 일시

2024-12-14

## 수정 완료 내역

### ✅ 수정됨

| 파일                                     | 변경 내용                                                      |
| ---------------------------------------- | -------------------------------------------------------------- |
| `backend/app/config.py`                  | ASR_SERVER_URL → `http://localhost:8001` (환경변수 오버라이드) |
| `backend/rk3588asr/config.py`            | 모든 IP → `localhost` (환경변수 오버라이드)                    |
| `backend/yolodetect/streamlit_app.py`    | 하드코딩 IP 제거, 환경변수 사용                                |
| `backend/yolodetect/streamlit_app_v2.py` | 예시 IP → `camera-ip` 플레이스홀더                             |
| `backend/yolodetect/roi_*.py`            | API 엔드포인트 → 환경변수 참조                                 |
| `backend/init_db.py`                     | 초기 비밀번호 → 환경변수 `INIT_ADMIN_PASSWORD`                 |
| `backend/register_device.py`             | IP/URL → 환경변수 사용                                         |
| `backend/app/api/stream.py`              | 문서 예시 IP 일반화                                            |
| `backend/app/api/control.py`             | 문서 예시 IP 일반화                                            |

### ✅ Watch ID 수정

| 파일                  | 변경 내용                                            |
| --------------------- | ---------------------------------------------------- |
| `streamlit_app.py`    | 환경변수 `EMERGENCY_WATCH_ID` 사용, 기본값 빈 문자열 |
| `rk3588asr/config.py` | 환경변수 `EMERGENCY_WATCH_ID` 사용, 기본값 빈 문자열 |

### ✅ RTSP 예시 URL 수정

```python
# Before
"rtsp://admin:password@192.168.1.100:554/stream1"

# After
"rtsp://user:pass@camera-ip:554/stream"  # 플레이스홀더 사용
```

### 🟢 정상 (환경변수 사용)

- `SECRET_KEY`: 환경변수 필수 (`.env`)
- `DB_PASSWORD`: 환경변수 필수
- `MQTT_PASSWORD`: 환경변수 (선택)
- `INIT_ADMIN_PASSWORD`: 환경변수 (선택, 기본값 있음)

---

## 수정 가이드

### 1. config.py 수정

```python
# Before
ASR_SERVER_URL: str = "http://10.10.11.17:8001"

# After
ASR_SERVER_URL: str = "http://localhost:8001"  # 환경변수로 오버라이드
```

### 2. 하드코딩된 기본값을 환경변수 참조로 변경

```python
# Before
api_endpoint = config.get('api_endpoint', 'http://10.10.11.23:10008/api/emergency')

# After
import os
api_endpoint = config.get('api_endpoint', os.getenv('API_ENDPOINT', 'http://localhost:8080/api/emergency'))
```

### 3. RTSP 예시에서 비밀번호 제거

```python
# Before
"rtsp://admin:password@192.168.1.100:554/stream1"

# After
"rtsp://user:****@example.com:554/stream"  # 예시 형식만 표시
```

### 4. 초기 비밀번호 환경변수화

```python
# init_db.py
import os
initial_password = os.getenv("INIT_ADMIN_PASSWORD", "ChangeMe123!")
```

---

## 권장 사항

1. **모든 IP 주소를 `localhost` 또는 환경변수로 대체**
2. **Watch ID 등 식별자는 환경변수 또는 설정 파일에서 로드**
3. **예시 URL에는 실제 비밀번호 대신 플레이스홀더 사용**
4. **초기 비밀번호는 첫 로그인 시 강제 변경 요구**
5. **`.env.example` 파일에 모든 필수 환경변수 문서화**

---

## 참고: Docker 배포 시 체크리스트

- [ ] `.env` 파일이 `.gitignore`에 포함되어 있는가?
- [ ] 하드코딩된 IP 주소가 없는가?
- [ ] 비밀번호/토큰이 코드에 없는가?
- [ ] 개발용 기본값이 프로덕션에 안전한가?
- [ ] 로그에 민감정보가 출력되지 않는가?

