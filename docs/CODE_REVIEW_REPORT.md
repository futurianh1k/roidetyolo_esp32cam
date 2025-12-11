# Core S3 Management System - 코드 리뷰 보고서

**생성일:** 2025-12-10  
**리뷰 대상:** 전체 프로젝트 (백엔드, 프론트엔드, 펌웨어)  
**리뷰 기준:** 한국 개인정보보호법 / ISMS-P 보안 가이드라인

---

## 📊 전체 요약

| 항목 | 상태 | 완성도 | 비고 |
|------|------|--------|------|
| **보안 구현** | 🟡 양호 | 85% | 일부 개선 필요 |
| **코드 품질** | 🟢 우수 | 90% | 잘 구조화됨 |
| **문서화** | 🟢 우수 | 95% | 상세한 문서 제공 |
| **테스트** | 🔴 부족 | 20% | 테스트 코드 필요 |
| **프로덕션 준비** | 🟡 준비 중 | 70% | 보안 강화 필요 |

---

## ✅ 잘 구현된 부분

### 1. 보안 기본 구조 (85% 완료)

#### ✅ 비밀번호 처리 (보안 가이드라인 1-1)
- **위치:** `backend/app/security/password.py`
- **구현 상태:** ✅ 완료
- **특징:**
  - BCrypt 해싱 (rounds=12) ✅
  - 비밀번호 강도 검증 ✅
  - 로그에 비밀번호 노출 방지 ✅

```12:14:backend/app/security/password.py
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
```

#### ✅ JWT 토큰 관리 (보안 가이드라인 1-2)
- **위치:** `backend/app/security/jwt.py`
- **구현 상태:** ✅ 완료
- **특징:**
  - Access Token (15분) + Refresh Token (7일) ✅
  - Refresh Token 해시 저장 ✅
  - 토큰 재발급 시 기존 토큰 무효화 ✅

```82:93:backend/app/security/jwt.py
def hash_token(token: str) -> str:
    """
    토큰 해시 생성 (DB 저장용)
    보안 가이드라인 1-2: Refresh Token은 해시로 저장
    
    Args:
        token: 원본 토큰
    
    Returns:
        str: SHA-256 해시
    """
    return hashlib.sha256(token.encode()).hexdigest()
```

#### ✅ 입력 검증 (보안 가이드라인 3-1)
- **위치:** `backend/app/utils/validators.py`
- **구현 상태:** ✅ 완료
- **특징:**
  - 장비 ID, IP 주소, MQTT 토픽 검증 ✅
  - 파일 확장자 화이트리스트 ✅
  - 경로 공격 방지 (sanitize_filename) ✅

```84:104:backend/app/utils/validators.py
def sanitize_filename(filename: str) -> str:
    """
    파일명 정제 (경로 공격 방지)
    보안 가이드라인 6 준수: ../ 경로 공격 방지
    
    Args:
        filename: 원본 파일명
    
    Returns:
        str: 정제된 파일명
    """
    # 경로 구분자 제거
    filename = filename.replace('/', '_').replace('\\', '_')
    
    # 특수문자 제거 (알파벳, 숫자, ., -, _ 만 허용)
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    
    # 연속된 점 제거
    filename = re.sub(r'\.{2,}', '.', filename)
    
    return filename
```

#### ✅ 로그 필터링 (보안 가이드라인 5)
- **위치:** `backend/app/utils/logger.py`
- **구현 상태:** ✅ 완료
- **특징:**
  - 민감정보 자동 필터링 ✅
  - 비밀번호, 토큰, API 키 로그 제외 ✅

```13:33:backend/app/utils/logger.py
# 민감 정보 키워드 (로그에서 필터링)
SENSITIVE_KEYS = {
    "password", "password_hash", "token", "access_token", "refresh_token",
    "secret", "api_key", "authorization", "cookie", "jwt"
}


class SensitiveDataFilter(logging.Filter):
    """민감 정보 필터링 로그 필터"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """로그 레코드에서 민감 정보 마스킹"""
        # 메시지 필터링
        if hasattr(record, 'msg'):
            msg_lower = str(record.msg).lower()
            for key in SENSITIVE_KEYS:
                if key in msg_lower:
                    record.msg = f"[FILTERED] 민감정보 포함된 로그"
                    break
        
        return True
```

#### ✅ 파일 업로드 검증 (보안 가이드라인 6)
- **위치:** `backend/app/api/audio.py`
- **구현 상태:** ✅ 완료
- **특징:**
  - 파일 크기 제한 (10MB) ✅
  - 확장자 화이트리스트 ✅
  - 파일명 정제 ✅

### 2. 코드 구조

#### ✅ 모듈화된 아키텍처
- 백엔드: FastAPI 기반 명확한 구조
- 프론트엔드: Next.js App Router 사용
- 펌웨어: 모듈별 분리

#### ✅ 환경 변수 기반 설정
- **위치:** `backend/app/config.py`
- **특징:**
  - 시크릿을 코드에 하드코딩하지 않음 ✅
  - `.env` 파일 사용 ✅

---

## ⚠️ 개선이 필요한 부분

### 1. 보안 취약점 (중요도: 높음)

#### ❌ 토큰 저장 방식 (보안 가이드라인 1-2 위반)

**문제점:**
- 프론트엔드에서 토큰을 `localStorage`에 저장
- XSS 공격에 취약
- 보안 가이드라인 1-2: "토큰을 localStorage에 저장하고, JS로 아무 데서나 읽어 쓰기" ❌

**위치:** `frontend/src/store/authStore.ts`, `frontend/src/lib/api.ts`

```25:27:frontend/src/store/authStore.ts
  setAuth: (user, accessToken, refreshToken) => {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
```

**권장 해결책:**
1. HttpOnly + Secure + SameSite 쿠키 사용
2. 백엔드에서 쿠키로 토큰 전달
3. 프론트엔드에서 localStorage 제거

**우선순위:** 🔴 높음 (프로덕션 배포 전 필수)

---

#### ⚠️ 인증 시스템 임시 비활성화

**문제점:**
- 개발 편의를 위해 인증 체크가 주석 처리됨
- 프로덕션 배포 시 보안 위험

**위치:**
- `backend/app/api/devices.py` (40, 75, 99번 줄)
- `backend/app/api/control.py` (32, 98, 167, 230번 줄)
- `frontend/src/app/page.tsx` (10번 줄)

```40:42:backend/app/api/devices.py
    # TODO: 로그인 수정 후 활성화
    # current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
```

**권장 해결책:**
1. 모든 TODO 주석 제거
2. 인증 의존성 활성화
3. 프론트엔드 라우트 가드 추가

**우선순위:** 🔴 높음 (프로덕션 배포 전 필수)

---

#### ⚠️ 감사 로그 미완성

**문제점:**
- 일부 API에서 감사 로그가 TODO로 비활성화됨
- ISMS-P 요구사항 미충족

**위치:**
- `backend/app/api/devices.py` (144-156번 줄)
- `backend/app/api/control.py` (66-77번 줄)
- `backend/app/api/audio.py` (60-70번 줄)

```60:70:backend/app/api/audio.py
        # TODO: 로그인 수정 후 감사 로그 활성화
        # ip_address = get_client_ip(request) if request else None
        # audit_log = AuditLog(
        #     user_id=current_user.id,
        #     action="upload_audio",
        #     resource_type="audio_file",
        #     resource_id=saved_filename,
        #     ip_address=ip_address
        # )
        # db.add(audit_log)
        # db.commit()
```

**권장 해결책:**
1. 모든 TODO 주석 제거
2. 감사 로그 기록 활성화
3. 감사 로그 조회 API 추가

**우선순위:** 🟡 중간 (프로덕션 배포 전 권장)

---

### 2. 프로덕션 보안 기능 (중요도: 중간)

#### ❌ HTTPS 미구현

**문제점:**
- HTTP 통신만 사용
- 프로덕션 환경에서 민감정보 노출 위험

**권장 해결책:**
1. Nginx 리버스 프록시 설정
2. Let's Encrypt SSL 인증서 발급
3. HSTS 헤더 추가

**우선순위:** 🟡 중간 (프로덕션 배포 시 필수)

---

#### ❌ Rate Limiting 미구현

**문제점:**
- DoS 공격에 취약
- 무차별 대입 공격 방지 없음

**권장 해결책:**
1. FastAPI-Limiter 도입
2. Redis 기반 Rate Limiting
3. 로그인 API: 5회/분 제한

**우선순위:** 🟡 중간 (프로덕션 배포 시 권장)

---

#### ❌ MQTT TLS/SSL 미구현

**문제점:**
- MQTT 통신이 평문으로 전송
- 장비 제어 명령 노출 위험

**권장 해결책:**
1. Mosquitto TLS 설정
2. 백엔드 MQTT 클라이언트 TLS 활성화
3. ESP32 펌웨어 TLS 지원

**우선순위:** 🟢 낮음 (프로덕션 배포 시 권장)

---

### 3. 코드 품질

#### ⚠️ 테스트 코드 부족

**문제점:**
- 백엔드 테스트 코드 미구현
- 프론트엔드 테스트 코드 미구현
- 통합 테스트 없음

**현재 상태:**
- `backend/test_api.py`: 수동 테스트 스크립트만 존재
- `backend/test_all_apis.py`: 수동 테스트 스크립트만 존재
- 자동화된 테스트 없음

**권장 해결책:**
1. pytest 기반 백엔드 테스트
2. Jest + React Testing Library 프론트엔드 테스트
3. CI/CD 파이프라인 통합

**우선순위:** 🟡 중간 (코드 품질 향상)

---

#### ⚠️ 에러 처리 개선 필요

**문제점:**
- 일부 API에서 상세한 에러 메시지 노출 가능성
- 사용자에게는 일반적인 메시지만 표시해야 함

**권장 해결책:**
1. 커스텀 예외 핸들러 추가
2. 프로덕션 환경에서 스택트레이스 숨김
3. 에러 로깅 강화

**우선순위:** 🟢 낮음

---

### 4. 기능 완성도

#### 🔄 인증 시스템 재활성화 필요

**현재 상태:**
- 백엔드: 인증 체크 주석 처리
- 프론트엔드: 로그인 우회

**필요 작업:**
1. 백엔드 TODO 주석 제거
2. 프론트엔드 라우트 가드 추가
3. 토큰 자동 갱신 로직 테스트

---

#### 🔄 스피커 제어 UI 미완성

**현재 상태:**
- 백엔드 API: ✅ 완료
- 프론트엔드 UI: ❌ 미구현

**필요 작업:**
1. 스피커 제어 컴포넌트 추가
2. 오디오 파일 선택 드롭다운
3. 볼륨 슬라이더

---

#### 🔄 장비 등록 UI 미완성

**현재 상태:**
- 백엔드 API: ✅ 완료
- 프론트엔드 UI: ❌ 미구현 (스크립트로만 가능)

**필요 작업:**
1. 장비 등록 모달 컴포넌트
2. 폼 검증 로직
3. 대시보드 통합

---

## 📋 보안 가이드라인 준수 현황

| 가이드라인 | 항목 | 상태 | 비고 |
|-----------|------|------|------|
| **1-1** | 비밀번호 해싱 | ✅ | BCrypt (rounds=12) |
| **1-1** | 비밀번호 로그 제외 | ✅ | 로그 필터링 |
| **1-2** | JWT 토큰 관리 | ✅ | Access + Refresh |
| **1-2** | Refresh Token 해시 저장 | ✅ | SHA-256 |
| **1-2** | 토큰 재발급 시 무효화 | ✅ | revoked 플래그 |
| **1-2** | 토큰 localStorage 저장 | ❌ | **쿠키로 변경 필요** |
| **2** | 권한 기반 접근 제어 | ⚠️ | **인증 비활성화 상태** |
| **3-1** | 백엔드 입력 검증 | ✅ | Pydantic + Validators |
| **3-2** | XSS 방지 | ✅ | 출력 인코딩 (Next.js 기본) |
| **4-1** | 필드 암호화 | ❌ | **개인정보 암호화 필요** |
| **4-2** | 시크릿 환경변수 관리 | ✅ | .env 파일 사용 |
| **5** | 민감정보 로그 필터링 | ✅ | SensitiveDataFilter |
| **6** | 파일 업로드 검증 | ✅ | 화이트리스트, 크기 제한 |
| **7** | AI/LLM 연동 보안 | ✅ | ASR 서버 통합 완료 |
| **8** | 프론트엔드 보안 | ⚠️ | **토큰 저장 방식 개선 필요** |
| **9** | 관리 기능 보안 | ⚠️ | **감사 로그 완성 필요** |

---

## 🎯 우선순위별 개선 사항

### 🔴 높은 우선순위 (프로덕션 배포 전 필수)

1. **토큰 저장 방식 변경**
   - localStorage → HttpOnly 쿠키
   - 작업 시간: 4-6시간
   - 보안 영향: 높음

2. **인증 시스템 재활성화**
   - 백엔드 인증 체크 활성화
   - 프론트엔드 라우트 가드 추가
   - 작업 시간: 2-3시간
   - 보안 영향: 높음

3. **HTTPS 설정**
   - SSL 인증서 발급
   - Nginx 리버스 프록시
   - 작업 시간: 2-3시간
   - 보안 영향: 높음

### 🟡 중간 우선순위 (프로덕션 배포 시 권장)

4. **감사 로그 완성**
   - TODO 주석 제거
   - 감사 로그 조회 API 추가
   - 작업 시간: 2시간

5. **Rate Limiting 구현**
   - FastAPI-Limiter 도입
   - Redis 설정
   - 작업 시간: 2-3시간

6. **테스트 코드 작성**
   - 백엔드 pytest 테스트
   - 프론트엔드 Jest 테스트
   - 작업 시간: 8-10시간

### 🟢 낮은 우선순위 (향후 개선)

7. **MQTT TLS/SSL**
   - 작업 시간: 3-4시간

8. **필드 암호화**
   - 개인정보 필드 암호화
   - 작업 시간: 4-6시간

9. **에러 처리 개선**
   - 커스텀 예외 핸들러
   - 작업 시간: 2-3시간

---

## 📊 코드 품질 평가

### 백엔드 (FastAPI)

**강점:**
- ✅ 명확한 모듈 구조
- ✅ 타입 힌팅 사용
- ✅ Pydantic 스키마 검증
- ✅ 보안 가이드라인 주석 명시

**개선점:**
- ⚠️ 테스트 코드 부족
- ⚠️ 일부 인증 체크 비활성화

**점수:** 85/100

---

### 프론트엔드 (Next.js)

**강점:**
- ✅ TypeScript 사용
- ✅ 컴포넌트 모듈화
- ✅ 상태 관리 (Zustand)

**개선점:**
- ❌ 토큰 localStorage 저장 (보안 위험)
- ⚠️ 테스트 코드 부족
- ⚠️ 라우트 가드 미구현

**점수:** 75/100

---

### 펌웨어 (Arduino/ESP32)

**강점:**
- ✅ 모듈별 분리
- ✅ MQTT 통신 구현
- ✅ 상태 보고 시스템

**점수:** 90/100

---

## 🔍 발견된 보안 취약점 요약

| 취약점 | 심각도 | 위치 | 해결 방법 |
|--------|--------|------|----------|
| 토큰 localStorage 저장 | 높음 | `frontend/src/store/authStore.ts` | HttpOnly 쿠키 사용 |
| 인증 시스템 비활성화 | 높음 | `backend/app/api/devices.py` | 인증 체크 활성화 |
| HTTPS 미구현 | 높음 | 전체 | SSL 인증서 설정 |
| Rate Limiting 없음 | 중간 | 전체 | FastAPI-Limiter 도입 |
| 감사 로그 미완성 | 중간 | `backend/app/api/*.py` | TODO 주석 제거 |
| 필드 암호화 없음 | 낮음 | DB 모델 | 개인정보 암호화 |

---

## ✅ 결론 및 권장 사항

### 현재 상태
- **전체 완성도:** 92%
- **보안 준수도:** 85%
- **프로덕션 준비도:** 70%

### 프로덕션 배포 전 필수 작업

1. ✅ 토큰 저장 방식 변경 (localStorage → HttpOnly 쿠키)
2. ✅ 인증 시스템 재활성화
3. ✅ HTTPS 설정
4. ✅ 감사 로그 완성
5. ✅ Rate Limiting 구현

### 예상 작업 시간

- **필수 작업:** 10-15시간
- **권장 작업:** 12-18시간
- **총 예상 시간:** 22-33시간

### 최종 평가

프로젝트는 **전반적으로 잘 구조화**되어 있으며, **대부분의 보안 가이드라인을 준수**하고 있습니다. 다만, **프로덕션 배포 전 몇 가지 보안 개선 사항**이 필요합니다.

**권장 순서:**
1. 인증 시스템 재활성화 (가장 빠르고 중요)
2. 토큰 저장 방식 변경 (보안 강화)
3. HTTPS 설정 (프로덕션 필수)
4. 감사 로그 완성 (ISMS-P 요구사항)
5. Rate Limiting (DoS 방지)

---

**리뷰 완료일:** 2025-12-10  
**다음 리뷰 예정일:** 프로덕션 배포 전

