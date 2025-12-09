# Phase 4 완료 보고서 - 프론트엔드 구현

**완료일**: 2025-12-08  
**소요 시간**: 약 1.5시간  
**상태**: ✅ 완료

---

## 📋 작업 요약

Phase 4에서는 프론트엔드에 음성인식 기능을 통합했습니다. 사용자가 웹 UI에서 음성인식 세션을 시작/종료하고, 실시간 인식 결과를 채팅 형식으로 확인할 수 있습니다.

---

## 📦 생성된 파일 (3개)

### 1. frontend/src/hooks/useASRWebSocket.ts (200 라인)

**목적**: ASR WebSocket 통신을 관리하는 커스텀 Hook

**주요 기능**:

- ✅ WebSocket 연결/해제 관리
- ✅ 인식 결과 수신 및 상태 관리
- ✅ 자동 재연결 (최대 5회)
- ✅ 에러 처리 및 콜백 지원

**주요 함수**:

#### `useASRWebSocket(options)`

**파라미터**:

- `wsUrl`: WebSocket URL (null이면 연결 안 함)
- `enabled`: 연결 활성화 여부
- `onResult`: 인식 결과 콜백
- `onError`: 에러 콜백
- `onConnect`: 연결 성공 콜백
- `onDisconnect`: 연결 해제 콜백

**반환값**:

```typescript
{
  isConnected: boolean;      // 연결 상태
  isConnecting: boolean;     // 연결 중 여부
  error: Error | null;       // 에러 정보
  results: RecognitionResult[]; // 인식 결과 목록
  connect: () => void;        // 수동 연결
  disconnect: () => void;     // 연결 해제
  clearResults: () => void;   // 결과 초기화
}
```

**메시지 처리**:

- `recognition_result`: 인식 결과 → `onResult` 콜백 호출
- `processing`: 처리 중 메시지 → 콘솔 로그
- `connected`: 연결 확인 → 콘솔 로그
- `error`: 에러 메시지 → `onError` 콜백 호출

**재연결 로직**:

- 정상 종료 (code 1000)가 아니면 자동 재연결
- 최대 5회 시도, 3초 간격
- 재연결 실패 시 에러 반환

---

### 2. frontend/src/components/VoiceRecognitionPanel.tsx (250 라인)

**목적**: 음성인식 세션을 시작/종료하는 패널 컴포넌트

**주요 기능**:

- ✅ 세션 시작/종료 버튼
- ✅ 세션 상태 표시 (활성 세션 정보)
- ✅ WebSocket 연결 상태 표시
- ✅ 언어 선택 (auto, ko, en, zh, ja)
- ✅ VAD 활성화 옵션
- ✅ 장비 오프라인 경고

**Props**:

```typescript
interface VoiceRecognitionPanelProps {
  device: Device;
  onResult?: (result: RecognitionResult) => void;
}
```

**상태 관리**:

- `language`: 선택된 언어 (기본값: 'ko')
- `vadEnabled`: VAD 활성화 여부 (기본값: true)
- `wsUrl`: WebSocket URL (세션 시작 시 저장)

**API 통신**:

- `asrAPI.getSessionStatus()`: 세션 상태 조회 (5초/30초 간격)
- `asrAPI.startSession()`: 세션 시작
- `asrAPI.stopSession()`: 세션 종료

**UI 구성**:

1. **헤더**: 제목 + WebSocket 연결 상태
2. **오프라인 경고**: 장비 오프라인 시 경고 메시지
3. **세션 상태**: 활성 세션 정보 (세션 ID, 세그먼트 수, 마지막 결과)
4. **설정**: 언어 선택, VAD 옵션 (세션이 없을 때만)
5. **버튼**: 시작/종료 버튼
6. **에러 표시**: WebSocket 에러 메시지

---

### 3. frontend/src/components/RecognitionChatWindow.tsx (150 라인)

**목적**: 음성인식 결과를 채팅 형식으로 표시하는 창

**주요 기능**:

- ✅ 인식 결과 히스토리 표시
- ✅ 타임스탬프 표시
- ✅ 응급 상황 강조 표시
- ✅ 자동 스크롤 (새 결과 추가 시)
- ✅ 결과 초기화 버튼

**Props**:

```typescript
interface RecognitionChatWindowProps {
  results: RecognitionResult[];
  onClear?: () => void;
}
```

**UI 구성**:

1. **헤더**: 제목 + 초기화 버튼
2. **메시지 영역**: 스크롤 가능한 결과 목록
3. **결과 카드**:
   - 헤더: 장비 이름 + 타임스탬프
   - 본문: 인식 텍스트
   - 메타: 길이, 응급 키워드
   - 응급 상황: 빨간색 배경 강조
4. **통계**: 총 결과 수, 응급 상황 건수

**스타일링**:

- 일반 결과: 회색 배경
- 응급 상황: 빨간색 배경 + 경고 아이콘
- 최대 높이: 500px (스크롤)

---

## 🔧 수정된 파일 (2개)

### 1. frontend/src/lib/api.ts

**추가된 타입** (7개):

- `ASRSessionStartRequest`
- `ASRSessionStartResponse`
- `ASRSessionStopRequest`
- `ASRSessionStopResponse`
- `ASRSessionStatus`
- `ASRSessionStatusResponse`
- `RecognitionResult`

**추가된 API 함수**:

```typescript
export const asrAPI = {
  startSession: (deviceId, request) => ...,
  stopSession: (deviceId, request) => ...,
  getSessionStatus: (deviceId) => ...,
  listAllSessions: () => ...,
  healthCheck: () => ...,
};
```

**수정된 함수**:

- `controlAPI.microphone`: `start_asr`, `stop_asr` 액션 추가

---

### 2. frontend/src/app/devices/[id]/page.tsx

**추가된 import**:

```typescript
import VoiceRecognitionPanel from "@/components/VoiceRecognitionPanel";
import RecognitionChatWindow from "@/components/RecognitionChatWindow";
import { RecognitionResult } from "@/lib/api";
```

**추가된 상태**:

```typescript
const [recognitionResults, setRecognitionResults] = useState<
  RecognitionResult[]
>([]);
```

**추가된 UI 섹션**:

```tsx
{
  /* Voice Recognition Section */
}
<div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
  <VoiceRecognitionPanel
    device={device}
    onResult={(result) => {
      setRecognitionResults((prev) => [...prev, result]);
    }}
  />
  <RecognitionChatWindow
    results={recognitionResults}
    onClear={() => setRecognitionResults([])}
  />
</div>;
```

---

## 🔄 전체 데이터 플로우

### 사용자 액션 → 인식 결과 표시

```
[사용자] "음성인식 시작" 버튼 클릭
    │
    ├─ VoiceRecognitionPanel.handleStart()
    │     │
    │     └─ asrAPI.startSession(deviceId, {language, vad_enabled})
    │           │
    │           ▼
    [백엔드] POST /asr/devices/{id}/session/start
    │           │
    │           ├─ ASR 서버에 세션 생성
    │           │     → {session_id, ws_url}
    │           │
    │           └─ MQTT로 CoreS3에 start_asr 명령 전송
    │                 │
    │                 ▼
    [CoreS3] WebSocket 연결 + 오디오 스트리밍 시작
    │           │
    │           ▼
    [ASR 서버] 음성인식 처리
    │           │
    │           ▼
    [ASR 서버] WebSocket으로 인식 결과 전송
    │           {
    │             type: "recognition_result",
    │             text: "안녕하세요",
    │             ...
    │           }
    │           │
    │           ▼
    [프론트엔드] useASRWebSocket Hook
    │           │
    │           ├─ WebSocket 메시지 수신
    │           ├─ JSON 파싱
    │           ├─ onResult 콜백 호출
    │           │     │
    │           │     ▼
    [VoiceRecognitionPanel] onResult(result)
    │           │
    │           └─ setRecognitionResults([...prev, result])
    │                 │
    │                 ▼
    [RecognitionChatWindow] results prop 업데이트
    │           │
    │           └─ 새 결과 카드 표시
    │                 - 텍스트: "안녕하세요"
    │                 - 타임스탬프: "10:30:45"
    │                 - 응급 상황: 빨간색 강조 (필요 시)
```

---

## 🎨 UI/UX 특징

### 1. VoiceRecognitionPanel

**상태별 UI**:

- **세션 없음**: 언어 선택 + VAD 옵션 + "음성인식 시작" 버튼
- **세션 활성**: 세션 정보 + WebSocket 상태 + "음성인식 종료" 버튼
- **오프라인**: 경고 메시지 + 비활성화된 버튼

**WebSocket 상태 표시**:

- 🟢 연결됨: 초록색 아이콘 + "연결됨"
- 🟡 연결 중: 노란색 스피너 + "연결 중..."
- 🔴 연결 끊김: 빨간색 아이콘 + "연결 끊김"

---

### 2. RecognitionChatWindow

**결과 카드 스타일**:

- **일반 결과**: 회색 배경 (`bg-gray-50`)
- **응급 상황**: 빨간색 배경 (`bg-red-50`) + 경고 아이콘

**자동 스크롤**:

- 새 결과 추가 시 자동으로 맨 아래로 스크롤
- `useEffect` + `scrollRef` 사용

**통계 정보**:

- 총 결과 수
- 응급 상황 건수 (있는 경우)

---

## 🧪 테스트 방법

### 1. 개발 서버 실행

```bash
cd frontend
npm run dev
```

### 2. 브라우저에서 확인

1. **장비 상세 페이지 접속**

   - `http://localhost:3000/devices/1`

2. **음성인식 패널 확인**

   - 언어 선택 드롭다운
   - VAD 체크박스
   - "음성인식 시작" 버튼

3. **세션 시작**

   - "음성인식 시작" 클릭
   - WebSocket 연결 상태 확인
   - 세션 정보 표시 확인

4. **인식 결과 확인**

   - CoreS3에서 음성 입력
   - RecognitionChatWindow에 결과 표시 확인
   - 타임스탬프, 길이 정보 확인

5. **세션 종료**
   - "음성인식 종료" 클릭
   - WebSocket 연결 해제 확인
   - 세션 정보 제거 확인

---

## ⚠️ 주의사항

### WebSocket URL 관리

**현재 구현**:

- 세션 시작 시 `ws_url`을 `useState`로 저장
- 세션 종료 시 `ws_url` 제거

**개선 가능**:

- 세션 상태 조회 API에서 `ws_url` 반환 (현재는 없음)
- 또는 세션 시작 응답을 전역 상태로 관리

---

### 재연결 로직

**현재 구현**:

- 자동 재연결 (최대 5회, 3초 간격)
- 정상 종료 (code 1000)는 재연결 안 함

**개선 가능**:

- 사용자에게 재연결 상태 알림
- 재연결 실패 시 수동 재연결 버튼

---

### 에러 처리

**현재 구현**:

- Toast 알림으로 에러 표시
- WebSocket 에러는 패널 하단에 표시

**개선 가능**:

- 더 상세한 에러 메시지
- 에러 복구 가이드

---

## ✅ 달성한 목표

### 프론트엔드 통합

- ✅ ASR API 타입 및 함수 추가
- ✅ WebSocket Hook 구현
- ✅ 음성인식 패널 컴포넌트
- ✅ 인식 결과 채팅 창
- ✅ 장비 상세 페이지 통합

### 사용자 경험

- ✅ 직관적인 UI/UX
- ✅ 실시간 상태 표시
- ✅ 에러 처리 및 알림
- ✅ 자동 스크롤

---

## 🚀 다음 단계 (선택적)

### 개선 사항

1. **세션 상태 관리 개선**

   - 전역 상태 관리 (Zustand)
   - 세션 상태 조회 API에 `ws_url` 추가

2. **에러 처리 강화**

   - 더 상세한 에러 메시지
   - 재연결 가이드

3. **성능 최적화**

   - 결과 목록 가상화 (많은 결과 처리)
   - WebSocket 메시지 배치 처리

4. **접근성 개선**
   - 키보드 네비게이션
   - 스크린 리더 지원

---

## 📝 변경 사항 요약

| 구분 | 파일 수 | 라인 수 |
| ---- | ------- | ------- |
| 생성 | 3       | 600     |
| 수정 | 2       | ~50     |
| 합계 | 5       | 650     |

---

## 🎉 Phase 4 완료!

프론트엔드에 음성인식 기능이 완전히 통합되었습니다.

**완료된 기능**:

- ✅ 음성인식 세션 시작/종료
- ✅ 실시간 인식 결과 표시
- ✅ WebSocket 연결 관리
- ✅ 응급 상황 강조

**전체 시스템 준비 완료**:

- ✅ Phase 1: ASR 서버
- ✅ Phase 2: 백엔드
- ✅ Phase 3: 펌웨어
- ✅ Phase 4: 프론트엔드

**음성인식 시스템 통합 완료!** 🎊

---

**작성일**: 2025-12-08  
**상태**: ✅ 완료  
**다음**: 테스트 및 배포
