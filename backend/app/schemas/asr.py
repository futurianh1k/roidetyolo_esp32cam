"""
ASR (Automatic Speech Recognition) 스키마

음성인식 세션 관리를 위한 데이터 스키마
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ASRSessionStartRequest(BaseModel):
    """
    ASR 세션 시작 요청

    장비의 음성인식 세션을 시작할 때 사용하는 요청 스키마
    """

    language: str = Field(
        default="auto", description="언어 코드 (auto, ko, en, zh, ja, yue)"
    )
    vad_enabled: bool = Field(
        default=True, description="VAD (Voice Activity Detection) 활성화 여부"
    )

    class Config:
        json_schema_extra = {"example": {"language": "ko", "vad_enabled": True}}


class ASRSessionStartResponse(BaseModel):
    """
    ASR 세션 시작 응답

    세션 생성 성공 시 반환되는 정보
    """

    session_id: str = Field(..., description="생성된 세션 ID (UUID)")
    device_id: int = Field(..., description="장비 ID (데이터베이스 PK)")
    device_name: str = Field(..., description="장비 이름")
    ws_url: str = Field(..., description="WebSocket 연결 URL")
    status: str = Field(..., description="세션 상태")
    message: str = Field(..., description="상태 메시지")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "device_id": 1,
                "device_name": "CoreS3-01",
                "ws_url": "ws://192.168.1.100:8001/ws/asr/550e8400-e29b-41d4-a716-446655440000",
                "status": "started",
                "message": "음성인식이 시작되었습니다.",
            }
        }


class ASRSessionStopRequest(BaseModel):
    """
    ASR 세션 종료 요청

    음성인식 세션을 종료할 때 사용
    """

    session_id: str = Field(..., description="종료할 세션 ID")

    class Config:
        json_schema_extra = {
            "example": {"session_id": "550e8400-e29b-41d4-a716-446655440000"}
        }


class ASRSessionStopResponse(BaseModel):
    """
    ASR 세션 종료 응답

    세션 종료 성공 시 반환되는 정보
    """

    session_id: str = Field(..., description="종료된 세션 ID")
    device_id: int = Field(..., description="장비 ID")
    status: str = Field(..., description="세션 상태 (stopped)")
    segments_count: int = Field(..., description="인식된 음성 세그먼트 수")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "device_id": 1,
                "status": "stopped",
                "segments_count": 5,
            }
        }


class ASRSessionStatus(BaseModel):
    """
    ASR 세션 상태

    현재 활성 세션의 상태 정보
    """

    session_id: str = Field(..., description="세션 ID")
    is_active: bool = Field(..., description="세션 활성 여부")
    is_processing: bool = Field(..., description="현재 음성 처리 중 여부")
    segments_count: int = Field(..., description="인식된 세그먼트 수")
    last_result: Optional[str] = Field(None, description="마지막 인식 결과")
    created_at: str = Field(..., description="세션 생성 시각 (ISO 8601)")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "is_active": True,
                "is_processing": False,
                "segments_count": 5,
                "last_result": "안녕하세요",
                "created_at": "2025-12-08T10:30:00.123456",
            }
        }


class ASRSessionStatusResponse(BaseModel):
    """
    ASR 세션 상태 응답

    장비의 음성인식 세션 상태를 조회할 때 반환되는 정보
    """

    device_id: int = Field(..., description="장비 ID")
    device_name: str = Field(..., description="장비 이름")
    has_active_session: bool = Field(..., description="활성 세션 존재 여부")
    session: Optional[ASRSessionStatus] = Field(
        None, description="세션 상태 (활성 세션이 있을 경우)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": 1,
                "device_name": "CoreS3-01",
                "has_active_session": True,
                "session": {
                    "session_id": "550e8400-e29b-41d4-a716-446655440000",
                    "is_active": True,
                    "is_processing": False,
                    "segments_count": 5,
                    "last_result": "안녕하세요",
                    "created_at": "2025-12-08T10:30:00.123456",
                },
            }
        }


class RecognitionResult(BaseModel):
    """
    음성인식 결과

    WebSocket으로 전달되는 실시간 인식 결과
    """

    type: str = Field(default="recognition_result", description="메시지 타입")
    device_id: Optional[int] = Field(None, description="장비 ID (DB PK)")
    device_id_string: Optional[str] = Field(
        None, description="장비 ID 문자열 (device_id가 없을 때 사용)"
    )
    device_name: str = Field(..., description="장비 이름")
    session_id: str = Field(..., description="세션 ID")
    text: str = Field(..., description="인식된 텍스트")
    timestamp: str = Field(..., description="인식 시각")
    duration: float = Field(..., description="음성 길이 (초)")
    is_emergency: bool = Field(default=False, description="응급 상황 여부")
    emergency_keywords: list[str] = Field(
        default_factory=list, description="감지된 응급 키워드"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "type": "recognition_result",
                "device_id": 1,
                "device_name": "CoreS3-01",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "text": "안녕하세요",
                "timestamp": "2025-12-08 10:30:45",
                "duration": 2.3,
                "is_emergency": False,
                "emergency_keywords": [],
            }
        }
