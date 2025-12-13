"""
알람 이력 관련 Pydantic 스키마
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal
from datetime import datetime


class AlarmHistoryBase(BaseModel):
    """알람 이력 기본 스키마"""

    alarm_type: Literal["sound", "text", "recorded"] = Field(
        ..., description="알람 타입: sound(사운드), text(TTS), recorded(녹음)"
    )
    alarm_subtype: Optional[str] = Field(
        None,
        max_length=50,
        description="알람 서브타입: beep, alert, emergency 등",
    )
    content: Optional[str] = Field(None, description="TTS 텍스트 또는 파일 경로")
    triggered_by: Literal["system", "admin", "user", "schedule"] = Field(
        default="system", description="트리거 주체"
    )
    parameters: Optional[str] = Field(None, description="추가 파라미터 (JSON)")


class AlarmHistoryCreate(AlarmHistoryBase):
    """알람 이력 생성 스키마"""

    device_id: int = Field(..., description="장비 ID")
    triggered_user_id: Optional[int] = Field(None, description="트리거한 사용자 ID")


class AlarmHistoryResponse(AlarmHistoryBase):
    """알람 이력 응답 스키마"""

    id: int
    device_id: int
    triggered_user_id: Optional[int] = None
    created_at: datetime
    status: str = "sent"

    model_config = ConfigDict(from_attributes=True)


class AlarmHistoryListResponse(BaseModel):
    """알람 이력 목록 응답 스키마"""

    items: list[AlarmHistoryResponse]
    total: int
    page: int
    page_size: int


class AlarmHistoryFilter(BaseModel):
    """알람 이력 필터 스키마"""

    device_id: Optional[int] = None
    alarm_type: Optional[Literal["sound", "text", "recorded"]] = None
    triggered_by: Optional[Literal["system", "admin", "user", "schedule"]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
