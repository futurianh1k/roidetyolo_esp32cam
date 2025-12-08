"""
장비 제어 관련 Pydantic 스키마
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal


class CameraControlRequest(BaseModel):
    """카메라 제어 요청"""
    action: Literal["start", "pause", "stop"]


class MicrophoneControlRequest(BaseModel):
    """마이크 제어 요청"""
    action: Literal["start", "pause", "stop"]


class SpeakerControlRequest(BaseModel):
    """스피커 제어 요청"""
    action: Literal["play", "stop"]
    audio_url: Optional[str] = Field(None, max_length=500)


class DisplayControlRequest(BaseModel):
    """디스플레이 제어 요청"""
    action: Literal["show_text", "show_emoji", "clear"]
    content: Optional[str] = Field(None, max_length=500)
    emoji_id: Optional[str] = Field(None, max_length=50)


class ControlResponse(BaseModel):
    """제어 응답"""
    success: bool
    message: str
    request_id: Optional[str] = None

