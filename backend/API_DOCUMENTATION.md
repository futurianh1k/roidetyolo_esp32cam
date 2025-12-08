# Core S3 Management System - API 문서

## 목차

1. [인증](#인증)
2. [사용자 관리](#사용자-관리)
3. [장비 관리](#장비-관리)
4. [장비 제어](#장비-제어)
5. [오디오 파일](#오디오-파일-관리)
6. [WebSocket](#websocket-실시간-통신)
7. [오류 코드](#오류-코드)

---

## 인증

### 사용자 등록

**POST** `/auth/register`

```json
// Request
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "TestPass123!",
  "role": "viewer"  // admin, operator, viewer
}

// Response (201 Created)
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "role": "viewer",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00",
  "last_login_at": null
}
```

### 로그인

**POST** `/auth/login`

```json
// Request
{
  "username": "admin",
  "password": "Admin123!"
}

// Response (200 OK)
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 토큰 갱신

**POST** `/auth/refresh`

```json
// Request
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}

// Response (200 OK)
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 로그아웃

**POST** `/auth/logout`

**헤더:** `Authorization: Bearer <access_token>`

```json
// Request
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}

// Response (200 OK)
{
  "message": "로그아웃되었습니다"
}
```

### 현재 사용자 정보

**GET** `/auth/me`

**헤더:** `Authorization: Bearer <access_token>`

```json
// Response (200 OK)
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "role": "admin",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00",
  "last_login_at": "2024-01-01T10:30:00"
}
```

---

## 사용자 관리

### 사용자 목록 조회 (ADMIN)

**GET** `/users/?page=1&page_size=10&role=viewer&is_active=true`

**헤더:** `Authorization: Bearer <access_token>`

**권한:** ADMIN

```json
// Response (200 OK)
{
  "users": [
    {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "role": "admin",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00",
      "last_login_at": "2024-01-01T10:30:00"
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 10
}
```

### 사용자 상세 조회 (ADMIN)

**GET** `/users/{user_id}`

**헤더:** `Authorization: Bearer <access_token>`

**권한:** ADMIN

### 사용자 생성 (ADMIN)

**POST** `/users/`

**헤더:** `Authorization: Bearer <access_token>`

**권한:** ADMIN

### 비밀번호 변경

**PUT** `/users/me/password`

**헤더:** `Authorization: Bearer <access_token>`

```json
// Request
{
  "current_password": "OldPass123!",
  "new_password": "NewPass123!"
}

// Response (200 OK)
{
  "message": "비밀번호가 성공적으로 변경되었습니다"
}
```

---

## 장비 관리

### 장비 목록 조회

**GET** `/devices/?page=1&page_size=10&is_online=true&device_type=CoreS3`

**헤더:** `Authorization: Bearer <access_token>`

**권한:** VIEWER 이상

```json
// Response (200 OK)
{
  "devices": [
    {
      "id": 1,
      "device_id": "core_s3_001",
      "device_name": "현관 카메라",
      "device_type": "CoreS3",
      "ip_address": "192.168.1.100",
      "rtsp_url": "rtsp://192.168.1.100:554/stream",
      "mqtt_topic": "devices/core_s3_001",
      "is_online": true,
      "registered_at": "2024-01-01T00:00:00",
      "last_seen_at": "2024-01-01T12:00:00",
      "location": "1층 현관",
      "description": "현관 모니터링용"
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 10
}
```

### 장비 등록 (OPERATOR)

**POST** `/devices/`

**헤더:** `Authorization: Bearer <access_token>`

**권한:** OPERATOR 이상

```json
// Request
{
  "device_id": "core_s3_001",
  "device_name": "현관 카메라",
  "device_type": "CoreS3",
  "ip_address": "192.168.1.100",
  "mqtt_topic": "devices/core_s3_001",
  "location": "1층 현관",
  "description": "현관 모니터링용"
}

// Response (201 Created)
{
  "id": 1,
  "device_id": "core_s3_001",
  "device_name": "현관 카메라",
  // ... 전체 정보
}
```

### 장비 상태 기록

**POST** `/devices/{device_id}/status`

**헤더:** `Authorization: Bearer <access_token>`

```json
// Request
{
  "battery_level": 85,
  "memory_usage": 45000,
  "storage_usage": 1200000,
  "temperature": 38.5,
  "cpu_usage": 45,
  "camera_status": "active",
  "mic_status": "active"
}

// Response (201 Created)
{
  "id": 1,
  "device_id": 1,
  "battery_level": 85,
  // ... 전체 상태
  "recorded_at": "2024-01-01T12:00:00"
}
```

### 장비 최신 상태 조회

**GET** `/devices/{device_id}/status/latest`

**헤더:** `Authorization: Bearer <access_token>`

---

## 장비 제어

### 카메라 제어 (OPERATOR)

**POST** `/control/devices/{device_id}/camera`

**헤더:** `Authorization: Bearer <access_token>`

**권한:** OPERATOR 이상

```json
// Request
{
  "action": "start"  // start, pause, stop
}

// Response (200 OK)
{
  "success": true,
  "message": "카메라 start 명령을 전송했습니다",
  "request_id": "abc123def456"
}
```

### 마이크 제어 (OPERATOR)

**POST** `/control/devices/{device_id}/microphone`

**헤더:** `Authorization: Bearer <access_token>`

**권한:** OPERATOR 이상

```json
// Request
{
  "action": "start"  // start, pause, stop
}

// Response (200 OK)
{
  "success": true,
  "message": "마이크 start 명령을 전송했습니다",
  "request_id": "abc123def456"
}
```

### 스피커 제어 (OPERATOR)

**POST** `/control/devices/{device_id}/speaker`

**헤더:** `Authorization: Bearer <access_token>`

**권한:** OPERATOR 이상

```json
// Request
{
  "action": "play",  // play, stop
  "audio_url": "http://server/api/audio/file.mp3"
}

// Response (200 OK)
{
  "success": true,
  "message": "스피커 play 명령을 전송했습니다",
  "request_id": "abc123def456"
}
```

### 디스플레이 제어 (OPERATOR)

**POST** `/control/devices/{device_id}/display`

**헤더:** `Authorization: Bearer <access_token>`

**권한:** OPERATOR 이상

```json
// Request (텍스트 표시)
{
  "action": "show_text",
  "content": "Hello World"
}

// Request (이모티콘 표시)
{
  "action": "show_emoji",
  "emoji_id": "smile"
}

// Request (화면 지우기)
{
  "action": "clear"
}

// Response (200 OK)
{
  "success": true,
  "message": "디스플레이 show_text 명령을 전송했습니다",
  "request_id": "abc123def456"
}
```

---

## 오디오 파일 관리

### 오디오 파일 업로드 (OPERATOR)

**POST** `/audio/upload`

**헤더:** `Authorization: Bearer <access_token>`

**권한:** OPERATOR 이상

**Content-Type:** `multipart/form-data`

```
// Request (Form Data)
file: <binary_file>  // mp3, wav, ogg (최대 10MB)

// Response (201 Created)
{
  "success": true,
  "message": "파일이 성공적으로 업로드되었습니다",
  "filename": "abc123def456.mp3",
  "original_filename": "announcement.mp3",
  "size": 1024000,
  "url": "/api/audio/abc123def456.mp3"
}
```

### 오디오 파일 목록

**GET** `/audio/list`

**헤더:** `Authorization: Bearer <access_token>`

**권한:** OPERATOR 이상

```json
// Response (200 OK)
[
  {
    "filename": "abc123def456.mp3",
    "size": 1024000,
    "created_at": 1704067200,
    "url": "/api/audio/abc123def456.mp3"
  }
]
```

### 오디오 파일 다운로드

**GET** `/audio/{filename}`

**헤더:** `Authorization: Bearer <access_token>`

**권한:** OPERATOR 이상

### 오디오 파일 삭제

**DELETE** `/audio/{filename}`

**헤더:** `Authorization: Bearer <access_token>`

**권한:** OPERATOR 이상

---

## WebSocket 실시간 통신

### 연결

```
WebSocket: ws://localhost:8000/ws?token=<access_token>
```

### 메시지 형식

#### 클라이언트 → 서버

```json
// 장비 구독
{
  "type": "subscribe_device",
  "device_id": 1
}

// 장비 구독 해제
{
  "type": "unsubscribe_device",
  "device_id": 1
}

// Ping
{
  "type": "ping"
}
```

#### 서버 → 클라이언트

```json
// 연결 성공
{
  "type": "connected",
  "message": "WebSocket 연결 성공",
  "user_id": 1
}

// 구독 확인
{
  "type": "subscribed",
  "device_id": 1
}

// 장비 상태 업데이트
{
  "type": "device_status",
  "device_id": 1,
  "status": {
    "battery_level": 85,
    "temperature": 38.5,
    // ...
  },
  "timestamp": 1704067200
}

// 장비 온라인 상태
{
  "type": "device_online",
  "device_id": 1,
  "is_online": true
}

// 제어 응답
{
  "type": "control_response",
  "response": {
    "request_id": "abc123",
    "success": true,
    "message": "명령 실행 완료"
  }
}

// Pong
{
  "type": "pong"
}
```

---

## 오류 코드

### HTTP 상태 코드

- **200 OK**: 성공
- **201 Created**: 생성 성공
- **204 No Content**: 삭제 성공
- **400 Bad Request**: 잘못된 요청
- **401 Unauthorized**: 인증 실패
- **403 Forbidden**: 권한 없음
- **404 Not Found**: 리소스 없음
- **500 Internal Server Error**: 서버 오류

### 오류 응답 형식

```json
{
  "detail": "오류 메시지"
}
```

### 일반적인 오류

```json
// 인증 실패
{
  "detail": "인증에 실패했습니다"
}

// 권한 없음
{
  "detail": "권한이 없습니다"
}

// 리소스 없음
{
  "detail": "장비를 찾을 수 없습니다"
}

// 유효성 검사 실패
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "비밀번호는 최소 8자 이상이어야 합니다",
      "type": "value_error"
    }
  ]
}
```

---

## 예제 코드

### Python

```python
import requests

# 로그인
response = requests.post("http://localhost:8000/auth/login", json={
    "username": "admin",
    "password": "Admin123!"
})
tokens = response.json()
access_token = tokens["access_token"]

# 장비 목록 조회
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get("http://localhost:8000/devices/", headers=headers)
devices = response.json()

# 카메라 제어
response = requests.post(
    "http://localhost:8000/control/devices/1/camera",
    headers=headers,
    json={"action": "start"}
)
```

### JavaScript

```javascript
// 로그인
const response = await fetch('http://localhost:8000/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'admin',
    password: 'Admin123!'
  })
});
const { access_token } = await response.json();

// 장비 목록 조회
const devicesRes = await fetch('http://localhost:8000/devices/', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
const devices = await devicesRes.json();

// WebSocket 연결
const ws = new WebSocket(`ws://localhost:8000/ws?token=${access_token}`);
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('받은 메시지:', message);
};

// 장비 구독
ws.send(JSON.stringify({
  type: 'subscribe_device',
  device_id: 1
}));
```

---

## 추가 정보

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

