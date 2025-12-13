"""
스키마 패키지
"""

from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserPasswordChange,
    UserResponse,
    UserListResponse,
)
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    TokenPayload,
)
from app.schemas.device import (
    DeviceBase,
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
    DeviceListResponse,
    DeviceStatusCreate,
    DeviceStatusResponse,
    DeviceStatusListResponse,
)
from app.schemas.control import (
    CameraControlRequest,
    MicrophoneControlRequest,
    SpeakerControlRequest,
    DisplayControlRequest,
    ControlResponse,
)
from app.schemas.asr import (
    ASRSessionStartRequest,
    ASRSessionStartResponse,
    ASRSessionStopRequest,
    ASRSessionStopResponse,
    ASRSessionStatus,
    ASRSessionStatusResponse,
    RecognitionResult,
)
from app.schemas.asr_result import (
    ASRResultResponse,
    ASRResultListResponse,
    ASRResultSearchRequest,
    ASRResultStatsResponse,
)
from app.schemas.alarm_history import (
    AlarmHistoryBase,
    AlarmHistoryCreate,
    AlarmHistoryResponse,
    AlarmHistoryListResponse,
    AlarmHistoryFilter,
)

__all__ = [
    # User schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserPasswordChange",
    "UserResponse",
    "UserListResponse",
    # Auth schemas
    "LoginRequest",
    "TokenResponse",
    "RefreshTokenRequest",
    "TokenPayload",
    # Device schemas
    "DeviceBase",
    "DeviceCreate",
    "DeviceUpdate",
    "DeviceResponse",
    "DeviceListResponse",
    "DeviceStatusCreate",
    "DeviceStatusResponse",
    "DeviceStatusListResponse",
    # Control schemas
    "CameraControlRequest",
    "MicrophoneControlRequest",
    "SpeakerControlRequest",
    "DisplayControlRequest",
    "ControlResponse",
    # ASR schemas
    "ASRSessionStartRequest",
    "ASRSessionStartResponse",
    "ASRSessionStopRequest",
    "ASRSessionStopResponse",
    "ASRSessionStatus",
    "ASRSessionStatusResponse",
    "RecognitionResult",
    # ASR Result schemas
    "ASRResultResponse",
    "ASRResultListResponse",
    "ASRResultSearchRequest",
    "ASRResultStatsResponse",
    # Alarm History schemas
    "AlarmHistoryBase",
    "AlarmHistoryCreate",
    "AlarmHistoryResponse",
    "AlarmHistoryListResponse",
    "AlarmHistoryFilter",
]
