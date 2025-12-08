# Core S3 Management System - Frontend

Next.js 기반 Core S3 장비 관리 시스템 프론트엔드입니다.

## 기술 스택

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Data Fetching**: TanStack Query (React Query)
- **HTTP Client**: Axios
- **Real-time**: Socket.io-client
- **UI Icons**: Lucide React
- **Toast Notifications**: React Hot Toast

## 주요 기능

### ✅ 인증
- 로그인/로그아웃
- JWT 토큰 기반 인증
- 자동 토큰 갱신
- 보호된 라우트

### ✅ 대시보드
- 장비 목록 조회
- 실시간 상태 업데이트
- 온라인/오프라인 상태 표시
- 장비 통계 (전체/온라인/오프라인)

### ✅ 장비 상세
- 실시간 시스템 상태 모니터링
  - 배터리 레벨
  - 메모리 사용량
  - CPU 온도
  - CPU 사용률
- 컴포넌트 상태 표시
  - 카메라 상태
  - 마이크 상태

### ✅ 장비 제어
- 카메라 제어 (시작/일시정지/정지)
- 마이크 제어 (시작/일시정지/정지)
- 디스플레이 제어 (텍스트 표시/화면 지우기)

### ✅ 실시간 통신
- WebSocket을 통한 실시간 상태 업데이트
- 자동 재연결

## 프로젝트 구조

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx          # 루트 레이아웃
│   │   ├── page.tsx            # 홈 (리다이렉트)
│   │   ├── providers.tsx       # React Query Provider
│   │   ├── globals.css         # 전역 스타일
│   │   ├── login/
│   │   │   └── page.tsx       # 로그인 페이지
│   │   ├── dashboard/
│   │   │   └── page.tsx       # 대시보드
│   │   └── devices/
│   │       └── [id]/
│   │           └── page.tsx   # 장비 상세
│   ├── components/
│   │   ├── DeviceCard.tsx      # 장비 카드
│   │   ├── DashboardStats.tsx  # 대시보드 통계
│   │   ├── DeviceStatus.tsx    # 장비 상태 표시
│   │   └── DeviceControl.tsx   # 장비 제어
│   ├── lib/
│   │   ├── api.ts              # API 클라이언트
│   │   └── websocket.ts        # WebSocket 클라이언트
│   └── store/
│       └── authStore.ts        # 인증 상태 관리
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.js
└── README.md
```

## 설치 및 실행

### 1. 의존성 설치

```bash
cd frontend
npm install
```

### 2. 환경 변수 설정

`.env.local` 파일 생성:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### 3. 개발 서버 실행

```bash
npm run dev
```

브라우저에서 http://localhost:3000 접속

### 4. 빌드

```bash
# 프로덕션 빌드
npm run build

# 프로덕션 서버 실행
npm start
```

## 사용 방법

### 1. 로그인

기본 관리자 계정:
- 사용자명: `admin`
- 비밀번호: `Admin123!`

⚠️ 로그인 후 반드시 비밀번호를 변경하세요!

### 2. 대시보드

- 등록된 모든 장비 목록 확인
- 온라인/오프라인 상태 실시간 확인
- 장비 통계 확인
- 장비 카드 클릭하여 상세 페이지 이동

### 3. 장비 상세

- 실시간 시스템 상태 모니터링
- 카메라/마이크 제어
- 디스플레이 제어

## API 연동

### API 클라이언트 사용

```typescript
import { authAPI, devicesAPI, controlAPI } from '@/lib/api';

// 로그인
const { data } = await authAPI.login({ username, password });

// 장비 목록
const { data } = await devicesAPI.getList();

// 카메라 제어
await controlAPI.camera(deviceId, 'start');
```

### React Query 사용

```typescript
import { useQuery } from '@tanstack/react-query';
import { devicesAPI } from '@/lib/api';

const { data, isLoading } = useQuery({
  queryKey: ['devices'],
  queryFn: async () => {
    const { data } = await devicesAPI.getList();
    return data;
  },
  refetchInterval: 10000, // 10초마다 자동 갱신
});
```

## 상태 관리

### Zustand 사용

```typescript
import { useAuthStore } from '@/store/authStore';

function MyComponent() {
  const { user, isAuthenticated, setAuth, clearAuth } = useAuthStore();

  // ...
}
```

## WebSocket 연동

```typescript
import { wsClient } from '@/lib/websocket';

// 연결
wsClient.connect(accessToken);

// 장비 구독
wsClient.subscribeDevice(deviceId);

// 메시지 수신
wsClient.onMessage((message) => {
  console.log('Received:', message);
});

// 연결 해제
wsClient.disconnect();
```

## 스타일링

### Tailwind CSS 사용

```tsx
<div className="bg-white rounded-lg shadow p-6">
  <h2 className="text-lg font-semibold text-gray-900">
    제목
  </h2>
</div>
```

### 커스텀 색상

```typescript
// tailwind.config.ts
colors: {
  primary: {
    50: '#f0f9ff',
    // ...
    600: '#0284c7',
    // ...
  },
}
```

## 알림 (Toast)

```typescript
import toast from 'react-hot-toast';

// 성공
toast.success('성공 메시지');

// 에러
toast.error('에러 메시지');

// 정보
toast('정보 메시지');
```

## 라우팅

### 페이지 이동

```typescript
import { useRouter } from 'next/navigation';

const router = useRouter();

// 이동
router.push('/dashboard');

// 뒤로가기
router.back();
```

### 동적 라우트

```
/devices/[id]/page.tsx → /devices/1, /devices/2, ...
```

```typescript
import { useParams } from 'next/navigation';

const params = useParams();
const deviceId = Number(params.id);
```

## 성능 최적화

### 1. 자동 코드 분할

Next.js App Router는 자동으로 코드 분할을 수행합니다.

### 2. 이미지 최적화

```tsx
import Image from 'next/image';

<Image
  src="/logo.png"
  alt="Logo"
  width={200}
  height={200}
/>
```

### 3. React Query 캐싱

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5000,  // 5초 동안 캐시 유지
      cacheTime: 10000, // 10초 후 캐시 삭제
    },
  },
});
```

## 배포

### Vercel 배포

```bash
# Vercel CLI 설치
npm i -g vercel

# 배포
vercel
```

### Docker 배포

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
CMD ["npm", "start"]
```

```bash
docker build -t cores3-frontend .
docker run -p 3000:3000 cores3-frontend
```

### 환경 변수 설정

배포 환경에서 다음 환경 변수를 설정하세요:

```
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_WS_URL=wss://api.yourdomain.com
```

## 문제 해결

### API 연결 실패

백엔드 서버가 실행 중인지 확인:
```bash
curl http://localhost:8000/health
```

### WebSocket 연결 실패

- 백엔드 WebSocket 엔드포인트 확인
- CORS 설정 확인
- 방화벽 설정 확인

### 토큰 만료

- 자동 토큰 갱신이 실패하면 로그아웃 후 재로그인
- 브라우저 개발자 도구에서 localStorage 확인

## 개발 팁

### 1. Hot Reload

개발 중 파일 저장 시 자동으로 페이지가 새로고침됩니다.

### 2. TypeScript

타입 체크:
```bash
npm run type-check
```

### 3. Linting

```bash
npm run lint
```

### 4. 브라우저 개발자 도구

- Network 탭: API 요청/응답 확인
- Console 탭: 에러 메시지 확인
- Application 탭: localStorage 확인

## 라이선스

MIT License

