# BACKEND_HOST 설정 가이드

## 문제

ESP32 장비에서 오디오 파일 재생 시 `localhost:8000`에 연결을 시도하여 실패합니다.

## 해결 방법

### 1. 백엔드 서버의 IP 주소 확인

**Windows PowerShell:**
```powershell
ipconfig | findstr /i "IPv4"
```

**결과 예시:**
```
IPv4 주소 . . . . . . . . . : 10.10.11.18
```

### 2. .env 파일 수정

`backend/.env` 파일을 열고 다음 줄을 추가/수정:

```env
# Backend Server (장비가 접근할 수 있는 백엔드 주소)
BACKEND_HOST=10.10.11.18  # 실제 백엔드 서버 IP로 변경
BACKEND_PORT=8000
```

**중요:** 
- ESP32 장비 IP: `10.10.11.18`
- 백엔드 서버 IP: `10.10.11.18` (같은 머신)
- 같은 IP인 경우, 백엔드 서버가 실행 중인 머신의 IP를 사용

### 3. 백엔드 서버 재시작

```bash
cd backend
# 서버 중지 후 재시작
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 테스트

1. MP3 파일 업로드
2. 재생 버튼 클릭
3. 로그에서 생성된 URL 확인:
   ```
   오디오 파일 URL 생성: http://10.10.11.18:8000/audio/xxx.mp3
   ```

## 자동 감지 기능

코드가 자동으로 다음을 시도합니다:
1. Request의 Host 헤더에서 IP 추출
2. 장비 IP와 같은 서브넷의 백엔드 IP 추론
3. 네트워크 인터페이스에서 실제 IP 찾기

하지만 **명시적으로 .env 파일에 설정하는 것이 가장 안정적**입니다.

