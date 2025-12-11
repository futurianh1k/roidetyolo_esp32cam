# Core S3 Management System - 후속 개발 계획

**작성일:** 2025-12-10  
**기준 문서:** 코드 리뷰 보고서 (CODE_REVIEW_REPORT.md)  
**현재 완성도:** 92%  
**목표 완성도:** 100% (프로덕션 준비 완료)

---

## 📊 개발 계획 개요

### 전체 일정

| 단계 | 기간 | 우선순위 | 상태 |
|------|------|----------|------|
| **Phase 1: 보안 강화** | 1주 | 🔴 높음 | 🔄 진행 예정 |
| **Phase 2: 기능 완성** | 1주 | 🟡 중간 | ✅ 완료 |
| **Phase 3: 테스트 및 품질** | 1주 | 🟡 중간 | 🔄 진행 예정 |
| **Phase 4: 프로덕션 준비** | 1주 | 🔴 높음 | 🔄 진행 예정 |
| **총 예상 기간** | **4주** | - | - |

---

## 🔴 Phase 1: 보안 강화 (1주)

**목표:** 프로덕션 배포 전 필수 보안 기능 구현  
**예상 작업 시간:** 20-25시간

### 1-1. 토큰 저장 방식 변경 (4-6시간)

**문제점:**
- 현재: localStorage에 토큰 저장 (XSS 취약)
- 보안 가이드라인 1-2 위반

**해결 방법:**
1. 백엔드에서 HttpOnly + Secure + SameSite 쿠키로 토큰 전달
2. 프론트엔드에서 localStorage 제거
3. API 클라이언트에서 쿠키 자동 사용

**작업 내용:**

#### 백엔드 수정
- **파일:** `backend/app/api/auth.py`
- **변경 사항:**
  ```python
  # 로그인 응답을 쿠키로 전달
  from fastapi import Response
  
  @router.post("/login")
  async def login(..., response: Response):
      # ... 토큰 생성 ...
      
      # 쿠키 설정
      response.set_cookie(
          key="access_token",
          value=access_token,
          httponly=True,
          secure=True,  # HTTPS만
          samesite="lax",
          max_age=900  # 15분
      )
      response.set_cookie(
          key="refresh_token",
          value=refresh_token,
          httponly=True,
          secure=True,
          samesite="lax",
          max_age=604800  # 7일
      )
      
      return {"message": "로그인 성공"}
  ```

#### 프론트엔드 수정
- **파일:** `frontend/src/store/authStore.ts`
- **변경 사항:**
  ```typescript
  // localStorage 제거, 쿠키는 자동으로 전송됨
  setAuth: (user, accessToken, refreshToken) => {
    // localStorage 제거
    set({
      user,
      isAuthenticated: true,
    });
  }
  ```

- **파일:** `frontend/src/lib/api.ts`
- **변경 사항:**
  ```typescript
  // 쿠키는 자동으로 전송되므로 Authorization 헤더 제거
  api.interceptors.request.use((config) => {
    // 쿠키는 자동으로 전송됨
    config.withCredentials = true;
    return config;
  });
  ```

**참고 자료:**
- FastAPI Cookie 설정: https://fastapi.tiangolo.com/advanced/response-cookies/
- 보안 가이드라인 1-2: JWT/세션 토큰은 HttpOnly + Secure + SameSite 쿠키로 전달

**체크리스트:**
- [ ] 백엔드 로그인 API 쿠키 설정
- [ ] 백엔드 로그아웃 API 쿠키 삭제
- [ ] 프론트엔드 localStorage 제거
- [ ] API 클라이언트 쿠키 설정
- [ ] 브라우저 개발자 도구에서 쿠키 확인
- [ ] XSS 공격 테스트

---

### 1-2. 인증 시스템 재활성화 (2-3시간)

**문제점:**
- 개발 편의를 위해 인증 체크가 주석 처리됨

**작업 내용:**

#### 백엔드 수정
- **파일:** `backend/app/api/devices.py`
- **변경 사항:**
  ```python
  # TODO 주석 제거
  @router.get("/")
  async def list_devices(
      current_user: User = Depends(get_current_active_user),  # 활성화
      db: Session = Depends(get_db),
  ):
  ```

- **파일:** `backend/app/api/control.py`
- **변경 사항:**
  ```python
  # TODO 주석 제거
  @router.post("/devices/{device_id}/camera")
  async def control_camera(
      current_user: User = Depends(require_operator),  # 활성화
      ...
  ):
  ```

- **파일:** `backend/app/api/audio.py`
- **변경 사항:**
  ```python
  # TODO 주석 제거
  @router.post("/upload")
  async def upload_audio_file(
      current_user: User = Depends(require_operator),  # 활성화
      ...
  ):
  ```

#### 프론트엔드 수정
- **파일:** `frontend/src/app/page.tsx`
- **변경 사항:**
  ```typescript
  useEffect(() => {
    const token = getCookie('access_token');  // 쿠키에서 확인
    if (token) {
      router.push('/dashboard');
    } else {
      router.push('/login');
    }
  }, [router]);
  ```

- **새 파일:** `frontend/src/middleware.ts`
- **내용:**
  ```typescript
  import { NextResponse } from 'next/server';
  import type { NextRequest } from 'next/server';

  export function middleware(request: NextRequest) {
    const token = request.cookies.get('access_token');
    
    // 보호된 라우트
    if (!token && !request.nextUrl.pathname.startsWith('/login')) {
      return NextResponse.redirect(new URL('/login', request.url));
    }
    
    return NextResponse.next();
  }

  export const config = {
    matcher: ['/dashboard/:path*', '/devices/:path*'],
  };
  ```

**체크리스트:**
- [ ] 백엔드 모든 TODO 주석 제거
- [ ] 프론트엔드 로그인 우회 제거
- [ ] 라우트 가드 미들웨어 추가
- [ ] 인증 실패 시 로그인 페이지 리다이렉트
- [ ] 토큰 만료 시 자동 갱신 테스트
- [ ] 권한별 접근 제어 테스트

---

### 1-3. HTTPS 설정 (2-3시간)

**작업 내용:**

#### Nginx 설정
- **파일:** `nginx.conf` (새로 생성)
- **내용:**
  ```nginx
  server {
      listen 80;
      server_name yourdomain.com;
      
      # HTTP → HTTPS 리다이렉트
      return 301 https://$server_name$request_uri;
  }

  server {
      listen 443 ssl http2;
      server_name yourdomain.com;

      ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
      ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
      
      # SSL 보안 설정
      ssl_protocols TLSv1.2 TLSv1.3;
      ssl_ciphers HIGH:!aNULL:!MD5;
      ssl_prefer_server_ciphers on;
      
      # HSTS
      add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

      # 백엔드 프록시
      location /api {
          proxy_pass http://localhost:8000;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
      }

      # 프론트엔드
      location / {
          proxy_pass http://localhost:3000;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
      }
  }
  ```

#### Let's Encrypt 인증서 발급
```bash
# Ubuntu
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com

# 자동 갱신 설정
sudo certbot renew --dry-run
```

**체크리스트:**
- [ ] 도메인 설정
- [ ] Let's Encrypt 인증서 발급
- [ ] Nginx 설정 파일 작성
- [ ] HTTPS 연결 테스트
- [ ] HSTS 헤더 확인
- [ ] SSL Labs 테스트 (A+ 등급 목표)

**참고 자료:**
- Let's Encrypt: https://letsencrypt.org/
- Nginx SSL 설정: https://nginx.org/en/docs/http/configuring_https_servers.html

---

### 1-4. 감사 로그 완성 (2시간)

**작업 내용:**

#### 백엔드 수정
- **파일:** `backend/app/api/devices.py`, `control.py`, `audio.py`
- **변경 사항:**
  ```python
  # TODO 주석 제거 및 감사 로그 활성화
  ip_address = get_client_ip(request) if request else None
  audit_log = AuditLog(
      user_id=current_user.id,
      action="device_create",  # 또는 적절한 액션
      resource_type="device",
      resource_id=str(device.id),
      ip_address=ip_address
  )
  db.add(audit_log)
  db.commit()
  ```

#### 감사 로그 조회 API 추가
- **새 파일:** `backend/app/api/audit.py`
- **내용:**
  ```python
  @router.get("/audit-logs/")
  async def list_audit_logs(
      page: int = Query(1, ge=1),
      page_size: int = Query(50, ge=1, le=100),
      user_id: Optional[int] = None,
      device_id: Optional[int] = None,
      action: Optional[str] = None,
      current_user: User = Depends(require_admin),
      db: Session = Depends(get_db)
  ):
      # 감사 로그 조회 로직
      pass
  ```

**체크리스트:**
- [ ] 모든 TODO 주석 제거
- [ ] 모든 관리자 액션에 로그 기록
- [ ] 감사 로그 조회 API 추가
- [ ] IP 주소 추적 확인
- [ ] 로그 보존 기간 설정 (90일)

---

### 1-5. Rate Limiting 구현 (2-3시간)

**작업 내용:**

#### Redis 설치 및 설정
```bash
# Ubuntu
sudo apt install redis-server
sudo systemctl start redis

# Windows
# Redis for Windows 다운로드 및 설치
```

#### 백엔드 수정
- **의존성 추가:**
  ```bash
  pip install fastapi-limiter redis
  ```

- **파일:** `backend/app/main.py`
- **변경 사항:**
  ```python
  from fastapi_limiter import FastAPILimiter
  from fastapi_limiter.depends import RateLimiter
  import redis.asyncio as redis

  @asynccontextmanager
  async def lifespan(app: FastAPI):
      # 시작
      redis_connection = await redis.from_url("redis://localhost")
      await FastAPILimiter.init(redis_connection)
      yield
      # 종료
      await FastAPILimiter.close()
  ```

- **파일:** `backend/app/api/auth.py`
- **변경 사항:**
  ```python
  from fastapi_limiter.depends import RateLimiter

  @router.post("/login")
  @limiter.limit("5/minute")
  async def login(...):
      # 로그인 로직
  ```

**체크리스트:**
- [ ] Redis 설치 및 설정
- [ ] FastAPI-Limiter 통합
- [ ] 로그인 API Rate Limiting (5회/분)
- [ ] 장비 제어 API Rate Limiting (10회/분)
- [ ] Rate Limit 초과 시 에러 메시지
- [ ] Redis 모니터링

**참고 자료:**
- FastAPI-Limiter: https://github.com/long2ice/fastapi-limiter
- Redis: https://redis.io/

---

## 🟡 Phase 2: 기능 완성 (1주) ✅ 완료

**목표:** 미완성 기능 구현  
**예상 작업 시간:** 15-20시간  
**실제 작업 시간:** 약 2시간 (대부분 이미 완료되어 있었음)  
**완료일:** 2025-12-10

**상세 보고서:** [PHASE2_COMPLETE.md](PHASE2_COMPLETE.md)

### 2-1. 스피커 제어 UI 구현 (2-3시간)

**작업 내용:**

- **파일:** `frontend/src/components/DeviceControl.tsx`
- **추가 내용:**
  ```typescript
  // 스피커 제어 섹션
  const [audioFiles, setAudioFiles] = useState<AudioFile[]>([]);
  const [selectedFile, setSelectedFile] = useState<string>('');
  const [volume, setVolume] = useState<number>(70);

  useEffect(() => {
    // 오디오 파일 목록 조회
    audioAPI.list().then(res => setAudioFiles(res.data.files));
  }, []);

  const handleSpeakerControl = async (action: 'play' | 'pause' | 'stop') => {
    await controlAPI.speaker(deviceId, action, selectedFile, volume);
  };
  ```

**체크리스트:**
- [ ] 스피커 제어 UI 추가
- [ ] 오디오 파일 선택 드롭다운
- [ ] 볼륨 슬라이더 (0-100)
- [ ] 재생/일시정지/정지 버튼
- [ ] 현재 재생 상태 표시
- [ ] API 연동 및 에러 처리

---

### 2-2. 장비 등록 UI 구현 (3-4시간)

**작업 내용:**

- **새 파일:** `frontend/src/components/RegisterDeviceModal.tsx`
- **내용:**
  ```typescript
  interface RegisterDeviceModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
  }

  export default function RegisterDeviceModal({ ... }: RegisterDeviceModalProps) {
    // 폼 상태 관리
    // 입력 검증
    // API 연동
  }
  ```

- **파일:** `frontend/src/app/dashboard/page.tsx`
- **변경 사항:**
  ```typescript
  // 장비 등록 버튼 추가
  <button onClick={() => setShowRegisterModal(true)}>
    장비 등록
  </button>
  ```

**체크리스트:**
- [ ] 등록 모달 컴포넌트 생성
- [ ] 폼 입력 필드 (device_id, device_name, ip_address 등)
- [ ] 입력 검증 (IP 형식, device_id 형식)
- [ ] API 연동
- [ ] 성공/실패 처리
- [ ] 등록 후 목록 자동 갱신

---

### 2-3. RTSP 스트리밍 완성 (4-6시간)

**작업 내용:**

#### 펌웨어 수정
- **파일:** `firmware/src/camera_module.cpp`
- **변경 사항:**
  - MJPEG HTTP 스트리밍 서버 구현
  - URL: `http://{device_ip}:81/stream`

#### 프론트엔드 수정
- **새 파일:** `frontend/src/components/VideoPlayer.tsx`
- **내용:**
  ```typescript
  export default function VideoPlayer({ streamUrl }: { streamUrl: string }) {
    return (
      <img 
        src={streamUrl} 
        alt="Camera Stream"
        className="w-full h-auto"
      />
    );
  }
  ```

- **파일:** `frontend/src/app/devices/[id]/page.tsx`
- **변경 사항:**
  ```typescript
  // 카메라 상태 옆에 비디오 플레이어 추가
  <VideoPlayer streamUrl={`http://${device.ip_address}:81/stream`} />
  ```

**체크리스트:**
- [ ] 펌웨어 MJPEG 스트리밍 구현
- [ ] 프론트엔드 비디오 플레이어 컴포넌트
- [ ] 장비 상세 페이지 통합
- [ ] 재생/정지 제어
- [ ] 연결 실패 시 에러 처리
- [ ] 실제 장비에서 테스트

---

## 🟡 Phase 3: 테스트 및 품질 (1주)

**목표:** 테스트 코드 작성 및 코드 품질 향상  
**예상 작업 시간:** 20-25시간

### 3-1. 백엔드 테스트 코드 작성 (10-12시간)

**작업 내용:**

#### 테스트 환경 설정
- **새 파일:** `backend/tests/conftest.py`
- **내용:**
  ```python
  import pytest
  from fastapi.testclient import TestClient
  from app.main import app
  from app.database import get_db

  @pytest.fixture
  def client():
      return TestClient(app)

  @pytest.fixture
  def db_session():
      # 테스트 DB 세션
      pass
  ```

#### 테스트 파일 작성
- **새 파일:** `backend/tests/test_auth.py`
- **내용:**
  ```python
  def test_register_success(client):
      response = client.post("/auth/register", json={
          "username": "testuser",
          "email": "test@example.com",
          "password": "Test123!",
          "role": "viewer"
      })
      assert response.status_code == 201

  def test_login_success(client):
      # 로그인 테스트
      pass

  def test_login_invalid_credentials(client):
      # 잘못된 자격증명 테스트
      pass
  ```

- **새 파일:** `backend/tests/test_devices.py`
- **새 파일:** `backend/tests/test_control.py`
- **새 파일:** `backend/tests/test_security.py`

**체크리스트:**
- [ ] 테스트 환경 설정
- [ ] 인증 테스트 (5개 이상)
- [ ] 장비 관리 테스트 (10개 이상)
- [ ] 제어 API 테스트 (8개 이상)
- [ ] 보안 테스트 (권한 체크, SQL Injection 등)
- [ ] 테스트 커버리지 80% 이상 목표

---

### 3-2. 프론트엔드 테스트 코드 작성 (8-10시간)

**작업 내용:**

#### 테스트 환경 설정
- **파일:** `frontend/package.json`
- **의존성 추가:**
  ```json
  {
    "devDependencies": {
      "jest": "^29.0.0",
      "@testing-library/react": "^14.0.0",
      "@testing-library/jest-dom": "^6.0.0"
    }
  }
  ```

#### 테스트 파일 작성
- **새 파일:** `frontend/src/__tests__/components/DeviceCard.test.tsx`
- **내용:**
  ```typescript
  import { render, screen } from '@testing-library/react';
  import DeviceCard from '@/components/DeviceCard';

  describe('DeviceCard', () => {
    it('renders device information', () => {
      const device = { id: 1, device_name: 'Test Device' };
      render(<DeviceCard device={device} />);
      expect(screen.getByText('Test Device')).toBeInTheDocument();
    });
  });
  ```

**체크리스트:**
- [ ] 테스트 환경 설정
- [ ] 컴포넌트 테스트 (주요 컴포넌트)
- [ ] API 통합 테스트
- [ ] E2E 테스트 (선택사항)
- [ ] 테스트 커버리지 70% 이상 목표

---

### 3-3. CI/CD 파이프라인 구축 (2-3시간)

**작업 내용:**

- **새 파일:** `.github/workflows/ci.yml`
- **내용:**
  ```yaml
  name: CI

  on: [push, pull_request]

  jobs:
    test-backend:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v3
        - uses: actions/setup-python@v4
        - run: pip install -r backend/requirements.txt
        - run: pytest backend/tests/

    test-frontend:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v3
        - uses: actions/setup-node@v3
        - run: npm install
        - run: npm test
  ```

**체크리스트:**
- [ ] GitHub Actions 워크플로우 작성
- [ ] 백엔드 테스트 자동 실행
- [ ] 프론트엔드 테스트 자동 실행
- [ ] 테스트 실패 시 알림

---

## 🔴 Phase 4: 프로덕션 준비 (1주)

**목표:** 프로덕션 배포 준비 완료  
**예상 작업 시간:** 15-20시간

### 4-1. 배포 가이드 작성 (4-6시간)

**작업 내용:**

- **새 파일:** `DEPLOYMENT.md`
- **포함 내용:**
  1. Windows 배포 가이드
  2. Ubuntu 배포 가이드
  3. Docker 배포 가이드
  4. 환경 변수 설정
  5. 보안 체크리스트
  6. 모니터링 설정
  7. 백업/복구 절차

**체크리스트:**
- [ ] Windows 배포 가이드
- [ ] Ubuntu 배포 가이드
- [ ] Docker 배포 가이드
- [ ] 환경 변수 템플릿
- [ ] 보안 체크리스트
- [ ] 트러블슈팅 가이드

---

### 4-2. 모니터링 시스템 구축 (6-8시간)

**작업 내용:**

#### Prometheus + Grafana 설정
- **새 파일:** `docker-compose.monitoring.yml`
- **내용:**
  ```yaml
  version: '3.8'
  services:
    prometheus:
      image: prom/prometheus
      volumes:
        - ./prometheus.yml:/etc/prometheus/prometheus.yml
      
    grafana:
      image: grafana/grafana
      ports:
        - "3001:3000"
  ```

#### 백엔드 메트릭 수집
- **파일:** `backend/app/main.py`
- **변경 사항:**
  ```python
  from prometheus_client import Counter, Histogram

  request_count = Counter('http_requests_total', 'Total HTTP requests')
  request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')
  ```

**체크리스트:**
- [ ] Prometheus 설정
- [ ] Grafana 대시보드 생성
- [ ] 백엔드 메트릭 수집
- [ ] 알림 규칙 설정 (Slack, Email)

---

### 4-3. 자동 백업 시스템 구축 (4-6시간)

**작업 내용:**

- **새 파일:** `scripts/backup.sh`
- **내용:**
  ```bash
  #!/bin/bash
  # MySQL 백업 스크립트
  
  BACKUP_DIR="/backups"
  DATE=$(date +%Y%m%d_%H%M%S)
  
  mysqldump -u $DB_USER -p$DB_PASSWORD $DB_NAME | gzip > $BACKUP_DIR/backup_$DATE.sql.gz
  
  # 오래된 백업 삭제 (30일 이상)
  find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
  ```

- **Cron 설정:**
  ```bash
  # 매일 새벽 2시 백업
  0 2 * * * /path/to/scripts/backup.sh
  ```

**체크리스트:**
- [ ] 백업 스크립트 작성
- [ ] 자동 백업 스케줄 설정
- [ ] 백업 파일 암호화
- [ ] 원격 저장소 업로드 (선택사항)
- [ ] 복구 절차 문서화

---

## 📅 상세 일정표

### Week 1: 보안 강화
- **Day 1-2:** 토큰 저장 방식 변경
- **Day 3:** 인증 시스템 재활성화
- **Day 4:** HTTPS 설정
- **Day 5:** 감사 로그 완성, Rate Limiting

### Week 2: 기능 완성
- **Day 1:** 스피커 제어 UI
- **Day 2-3:** 장비 등록 UI
- **Day 4-5:** RTSP 스트리밍

### Week 3: 테스트 및 품질
- **Day 1-3:** 백엔드 테스트 코드
- **Day 4-5:** 프론트엔드 테스트 코드, CI/CD

### Week 4: 프로덕션 준비
- **Day 1-2:** 배포 가이드 작성
- **Day 3-4:** 모니터링 시스템
- **Day 5:** 자동 백업, 최종 점검

---

## 🎯 마일스톤

| 마일스톤 | 목표 날짜 | 완료 기준 |
|---------|----------|----------|
| **M1: 보안 강화 완료** | Week 1 종료 | 모든 보안 취약점 해결 |
| **M2: 기능 완성** | Week 2 종료 | 모든 미완성 기능 구현 |
| **M3: 테스트 완료** | Week 3 종료 | 테스트 커버리지 80% 이상 |
| **M4: 프로덕션 준비** | Week 4 종료 | 배포 가이드 완성, 모니터링 구축 |

---

## 📊 예상 작업량

| Phase | 작업 시간 | 누적 시간 |
|-------|----------|----------|
| Phase 1 | 20-25시간 | 20-25시간 |
| Phase 2 | 15-20시간 | 35-45시간 |
| Phase 3 | 20-25시간 | 55-70시간 |
| Phase 4 | 15-20시간 | 70-90시간 |
| **총계** | **70-90시간** | - |

---

## ✅ 최종 체크리스트

### 보안
- [ ] 토큰 HttpOnly 쿠키 저장
- [ ] 인증 시스템 재활성화
- [ ] HTTPS 설정 완료
- [ ] Rate Limiting 구현
- [ ] 감사 로그 완성
- [ ] MQTT TLS/SSL (선택사항)

### 기능
- [ ] 스피커 제어 UI
- [ ] 장비 등록 UI
- [ ] RTSP 스트리밍

### 테스트
- [ ] 백엔드 테스트 코드 (커버리지 80%+)
- [ ] 프론트엔드 테스트 코드 (커버리지 70%+)
- [ ] CI/CD 파이프라인

### 프로덕션
- [ ] 배포 가이드 작성
- [ ] 모니터링 시스템 구축
- [ ] 자동 백업 시스템
- [ ] 성능 테스트
- [ ] 보안 스캔

---

**작성 완료일:** 2025-12-10  
**다음 업데이트:** 각 Phase 완료 시

