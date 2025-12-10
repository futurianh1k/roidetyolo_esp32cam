# -*- coding: utf-8 -*-
"""
ASR WebSocket API 서버
Sherpa-ONNX 기반 실시간 음성인식 WebSocket API

🎯 기능:
1. WebSocket 기반 실시간 오디오 스트리밍 수신
2. VAD (Voice Activity Detection) 기반 음성 구간 감지
3. 실시간 음성인식 결과 전송
4. 다중 세션 관리
5. 응급 상황 감지 및 알림

📡 API 엔드포인트:
- POST /asr/session/start - 음성인식 세션 시작
- POST /asr/session/{session_id}/stop - 세션 종료
- GET /asr/session/{session_id}/status - 세션 상태 조회
- WS /ws/asr/{session_id} - WebSocket 음성 스트리밍

참고: Sherpa-ONNX RK3588 NPU 최적화
"""

import os
import sys
import logging
import asyncio
import json
import base64
import uuid
from datetime import datetime
from typing import Dict, Optional, List
from collections import deque
import numpy as np

# FastAPI 관련
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# 기존 demo_vad_final.py의 모듈 import
try:
    from demo_vad_final import (
        VADStreamingProcessor,
        load_model,
        matcher,
        recognizer,
        logger as demo_logger,
        EMERGENCY_API_CONFIG,
        send_emergency_alert,
    )

    # 모델 즉시 로드 (서버 시작 전에 초기화)
    if recognizer is None:
        logger.info("📦 음성인식 모델 초기 로딩 중...")
        try:
            load_model()
            logger.info("✅ 모델 초기 로드 완료")
        except Exception as e:
            logger.error(f"❌ 모델 초기 로딩 실패: {e}", exc_info=True)
            logger.warning("⚠️ 서버는 시작되지만 세션 생성이 실패할 수 있습니다.")

except ImportError as e:
    print(f"❌ demo_vad_final.py 모듈 import 실패: {e}")
    print("💡 asr_api_server.py와 demo_vad_final.py가 같은 디렉토리에 있어야 합니다.")
    sys.exit(1)

# ====================
# 로깅 설정
# ====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ====================
# FastAPI 앱 생성
# ====================
app = FastAPI(
    title="ASR WebSocket API Server",
    description="Sherpa-ONNX 기반 실시간 음성인식 WebSocket API",
    version="1.0.0",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====================
# 데이터 모델
# ====================


class SessionStartRequest(BaseModel):
    """세션 시작 요청"""

    device_id: str = Field(..., description="장비 ID (예: cores3_01)")
    language: str = Field(
        default="auto", description="언어 코드 (auto, ko, en, zh, ja, yue)"
    )
    sample_rate: int = Field(default=16000, description="샘플레이트 (Hz)")
    vad_enabled: bool = Field(default=True, description="VAD 활성화 여부")


class SessionStartResponse(BaseModel):
    """세션 시작 응답"""

    session_id: str = Field(..., description="세션 ID")
    ws_url: str = Field(..., description="WebSocket 연결 URL")
    status: str = Field(..., description="세션 상태")
    message: str = Field(..., description="상태 메시지")


class SessionStatusResponse(BaseModel):
    """세션 상태 응답"""

    session_id: str
    device_id: str
    is_active: bool
    is_processing: bool
    segments_count: int
    last_result: Optional[str]
    created_at: str
    language: str


class SessionStopResponse(BaseModel):
    """세션 종료 응답"""

    session_id: str
    status: str
    message: str
    segments_count: int


# ====================
# 세션 관리자
# ====================


class ASRSession:
    """음성인식 세션"""

    def __init__(
        self,
        session_id: str,
        device_id: str,
        language: str = "auto",
        sample_rate: int = 16000,
        vad_enabled: bool = True,
    ):
        self.session_id = session_id
        self.device_id = device_id
        self.language = language
        self.sample_rate = sample_rate
        self.created_at = datetime.now()

        # VAD Processor 생성
        global recognizer
        if recognizer is None:
            raise RuntimeError(
                "❌ Recognizer가 초기화되지 않았습니다. load_model()을 먼저 실행하세요."
            )

        self.processor = VADStreamingProcessor(
            recognizer=recognizer, sample_rate=sample_rate, vad_enabled=vad_enabled
        )

        # WebSocket 연결
        self.websocket: Optional[WebSocket] = None

        # 결과 저장
        self.recognition_results = deque(maxlen=100)

        logger.info(f"✅ ASR 세션 생성: {session_id} (device: {device_id})")

    def start(self):
        """세션 시작"""
        self.processor.start_session()
        logger.info(f"🎤 세션 시작: {self.session_id}")

    def stop(self):
        """세션 종료"""
        self.processor.stop_session()
        logger.info(f"🛑 세션 종료: {self.session_id}")

    async def process_audio_chunk(self, audio_data: np.ndarray) -> Optional[Dict]:
        """
        오디오 청크 처리

        Args:
            audio_data: float32 PCM 오디오 데이터 (16kHz)

        Returns:
            인식 결과 딕셔너리 또는 None
        """
        result = self.processor.process_audio_chunk(audio_data)

        if result:
            # 응급 상황 감지
            text = result.get("text", "")
            if text:
                match_result = matcher.find_best_match(text)

                result["is_emergency"] = match_result.get("is_emergency", False)
                result["emergency_keywords"] = match_result.get(
                    "emergency_keywords", []
                )

                # 응급 상황 감지 시 API 호출
                if result["is_emergency"]:
                    logger.warning(f"🚨 응급 상황 감지! {result['emergency_keywords']}")
                    try:
                        send_emergency_alert(text, result["emergency_keywords"])
                    except Exception as e:
                        logger.error(f"❌ 응급 알림 전송 실패: {e}")

                # 결과 저장
                self.recognition_results.append(result)

        return result

    def get_status(self) -> Dict:
        """세션 상태 반환"""
        processor_status = self.processor.get_session_status()

        return {
            "session_id": self.session_id,
            "device_id": self.device_id,
            "is_active": processor_status["is_active"],
            "is_processing": processor_status["is_processing"],
            "segments_count": processor_status["segments_count"],
            "last_result": processor_status["last_result"],
            "created_at": self.created_at.isoformat(),
            "language": self.language,
        }


class SessionManager:
    """세션 관리자 (싱글톤)"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.sessions: Dict[str, ASRSession] = {}
        return cls._instance

    def create_session(
        self,
        device_id: str,
        language: str = "auto",
        sample_rate: int = 16000,
        vad_enabled: bool = True,
    ) -> ASRSession:
        """새 세션 생성"""
        session_id = str(uuid.uuid4())

        session = ASRSession(
            session_id=session_id,
            device_id=device_id,
            language=language,
            sample_rate=sample_rate,
            vad_enabled=vad_enabled,
        )

        self.sessions[session_id] = session
        logger.info(f"📝 세션 등록: {session_id} (총 {len(self.sessions)}개)")

        return session

    def get_session(self, session_id: str) -> Optional[ASRSession]:
        """세션 조회"""
        return self.sessions.get(session_id)

    def remove_session(self, session_id: str):
        """세션 제거"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.stop()
            del self.sessions[session_id]
            logger.info(
                f"🗑️ 세션 제거: {session_id} (남은 세션: {len(self.sessions)}개)"
            )

    def get_all_sessions(self) -> List[Dict]:
        """모든 세션 목록"""
        return [session.get_status() for session in self.sessions.values()]


# 전역 세션 관리자
session_manager = SessionManager()

# ====================
# API 엔드포인트
# ====================


@app.get("/")
async def root():
    """서버 정보"""
    return {
        "service": "ASR WebSocket API Server",
        "version": "1.0.0",
        "status": "running",
        "active_sessions": len(session_manager.sessions),
        "endpoints": {
            "session_start": "POST /asr/session/start",
            "session_stop": "POST /asr/session/{session_id}/stop",
            "session_status": "GET /asr/session/{session_id}/status",
            "websocket": "WS /ws/asr/{session_id}",
        },
    }


@app.get("/health")
async def health_check():
    """헬스 체크"""
    global recognizer
    return {
        "status": "healthy",
        "recognizer_loaded": recognizer is not None,
        "active_sessions": len(session_manager.sessions),
    }


@app.post("/asr/session/start", response_model=SessionStartResponse)
async def start_session(request: SessionStartRequest):
    """
    음성인식 세션 시작

    새로운 음성인식 세션을 생성하고 WebSocket URL을 반환합니다.
    """
    try:
        # Recognizer 초기화 확인
        global recognizer
        if recognizer is None:
            logger.warning("⚠️ Recognizer가 초기화되지 않았습니다. 모델을 로드합니다...")
            try:
                load_model()
                logger.info("✅ 모델 로드 완료")
            except Exception as e:
                logger.error(f"❌ 모델 로딩 실패: {e}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"음성인식 모델을 로드할 수 없습니다: {str(e)}",
                )

        # 세션 생성
        session = session_manager.create_session(
            device_id=request.device_id,
            language=request.language,
            sample_rate=request.sample_rate,
            vad_enabled=request.vad_enabled,
        )

        # 세션 시작
        session.start()

        # WebSocket URL 생성
        ws_url = f"ws://localhost:8001/ws/asr/{session.session_id}"

        return SessionStartResponse(
            session_id=session.session_id,
            ws_url=ws_url,
            status="ready",
            message="세션이 생성되었습니다. WebSocket으로 연결하세요.",
        )

    except Exception as e:
        logger.error(f"❌ 세션 생성 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"세션 생성 실패: {str(e)}",
        )


@app.get("/asr/session/{session_id}/status", response_model=SessionStatusResponse)
async def get_session_status(session_id: str):
    """
    세션 상태 조회
    """
    session = session_manager.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"세션을 찾을 수 없습니다: {session_id}",
        )

    return SessionStatusResponse(**session.get_status())


@app.post("/asr/session/{session_id}/stop", response_model=SessionStopResponse)
async def stop_session(session_id: str):
    """
    세션 종료
    """
    session = session_manager.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"세션을 찾을 수 없습니다: {session_id}",
        )

    segments_count = len(session.recognition_results)
    session_manager.remove_session(session_id)

    return SessionStopResponse(
        session_id=session_id,
        status="stopped",
        message="세션이 종료되었습니다.",
        segments_count=segments_count,
    )


@app.get("/asr/sessions")
async def list_sessions():
    """
    모든 활성 세션 목록
    """
    return {
        "total": len(session_manager.sessions),
        "sessions": session_manager.get_all_sessions(),
    }


# ====================
# WebSocket 엔드포인트
# ====================


@app.websocket("/ws/asr/{session_id}")
async def websocket_asr_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket 음성 스트리밍 엔드포인트

    클라이언트는 다음 형식의 JSON 메시지를 전송:
    {
        "type": "audio_chunk",
        "data": "base64_encoded_pcm_audio",
        "timestamp": 1234567890
    }

    서버는 다음 형식의 JSON 응답:
    {
        "type": "recognition_result",
        "session_id": "uuid-xxxx",
        "text": "인식된 텍스트",
        "timestamp": "2025-12-08 10:30:45",
        "duration": 2.3,
        "is_final": true,
        "is_emergency": false,
        "emergency_keywords": []
    }
    """
    # 세션 확인
    session = session_manager.get_session(session_id)

    if not session:
        await websocket.close(
            code=4004, reason=f"세션을 찾을 수 없습니다: {session_id}"
        )
        return

    # WebSocket 연결 수락
    await websocket.accept()
    session.websocket = websocket

    logger.info(f"🔗 WebSocket 연결: {session_id} (device: {session.device_id})")

    # 연결 확인 메시지
    await websocket.send_json(
        {
            "type": "connected",
            "session_id": session_id,
            "message": "WebSocket 연결 성공. 오디오 전송을 시작하세요.",
        }
    )

    try:
        while True:
            # 클라이언트로부터 메시지 수신
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                msg_type = message.get("type")

                if msg_type == "audio_chunk":
                    # Base64 디코딩
                    audio_base64 = message.get("data", "")
                    if not audio_base64:
                        continue

                    # Base64 → bytes
                    audio_bytes = base64.b64decode(audio_base64)

                    # bytes → numpy array (int16 → float32)
                    audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
                    audio_float32 = audio_int16.astype(np.float32) / 32768.0

                    logger.debug(f"🎵 오디오 수신: {len(audio_float32)} samples")

                    # 오디오 처리
                    result = await session.process_audio_chunk(audio_float32)

                    if result:
                        # 인식 결과 전송
                        response = {
                            "type": "recognition_result",
                            "session_id": session_id,
                            "text": result["text"],
                            "timestamp": result["timestamp"],
                            "duration": result["duration"],
                            "is_final": True,
                            "is_emergency": result.get("is_emergency", False),
                            "emergency_keywords": result.get("emergency_keywords", []),
                        }

                        await websocket.send_json(response)
                        logger.info(f"✅ 인식 결과 전송: {result['text']}")
                    else:
                        # 처리 중 상태 전송 (선택적)
                        if session.processor.is_processing:
                            await websocket.send_json(
                                {
                                    "type": "processing",
                                    "session_id": session_id,
                                    "message": "음성 감지 중...",
                                }
                            )

                elif msg_type == "ping":
                    # Ping-Pong (연결 유지)
                    await websocket.send_json(
                        {"type": "pong", "session_id": session_id}
                    )

                else:
                    logger.warning(f"⚠️ 알 수 없는 메시지 타입: {msg_type}")

            except json.JSONDecodeError:
                logger.error("❌ JSON 파싱 실패")
                await websocket.send_json(
                    {
                        "type": "error",
                        "session_id": session_id,
                        "message": "잘못된 JSON 형식입니다.",
                    }
                )

            except Exception as e:
                logger.error(f"❌ 메시지 처리 오류: {e}", exc_info=True)
                await websocket.send_json(
                    {
                        "type": "error",
                        "session_id": session_id,
                        "message": f"처리 오류: {str(e)}",
                    }
                )

    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket 연결 끊김: {session_id}")

    except Exception as e:
        logger.error(f"❌ WebSocket 오류: {e}", exc_info=True)

    finally:
        # 세션 정리
        session.websocket = None
        logger.info(f"🧹 WebSocket 정리 완료: {session_id}")


# ====================
# 서버 시작 함수
# ====================


def start_server(host: str = "0.0.0.0", port: int = 8001):
    """
    ASR API 서버 시작

    Args:
        host: 호스트 주소
        port: 포트 번호
    """
    logger.info("\n" + "=" * 60)
    logger.info("🚀 ASR WebSocket API 서버 시작")
    logger.info("🖥️ Sherpa-ONNX RK3588 NPU 최적화")
    logger.info("=" * 60 + "\n")

    # Recognizer 로드 확인 (이미 모듈 로드 시 초기화됨)
    global recognizer
    if recognizer is None:
        logger.warning(
            "⚠️ Recognizer가 초기화되지 않았습니다. 모델을 다시 로드합니다..."
        )
        try:
            load_model()
            logger.info("✅ 모델 로드 완료")
        except Exception as e:
            logger.error(f"❌ 모델 로딩 실패: {e}", exc_info=True)
            logger.error("❌ 서버를 시작할 수 없습니다. 모델 파일을 확인하세요.")
            sys.exit(1)
    else:
        logger.info("✅ Recognizer가 이미 초기화되어 있습니다.")

    logger.info(f"\n🌐 서버 주소: http://{host}:{port}")
    logger.info(f"📡 WebSocket: ws://{host}:{port}/ws/asr/{{session_id}}")
    logger.info(f"📚 API 문서: http://{host}:{port}/docs")
    logger.info("=" * 60 + "\n")

    # Uvicorn 서버 실행
    uvicorn.run(app, host=host, port=port, log_level="info", access_log=True)


# ====================
# 메인 실행
# ====================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ASR WebSocket API Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="호스트 주소")
    parser.add_argument("--port", type=int, default=8001, help="포트 번호")

    args = parser.parse_args()

    start_server(host=args.host, port=args.port)
