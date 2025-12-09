"""
장비 제어 관련 Pydantic 스키마
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal


class CameraControlRequest(BaseModel):
    """카메라 제어 요청"""
    action: Literal["start", "pause", "stop"]


class MicrophoneControlRequest(BaseModel):
    """
    마이크 제어 요청
    
    액션:
    - start: 일반 마이크 시작
    - pause: 일시정지
    - stop: 정지
    - start_asr: 음성인식 모드로 시작 (ASR 서버 연동)
    - stop_asr: 음성인식 모드 종료
    """
    action: Literal["start", "pause", "stop", "start_asr", "stop_asr"]


class SpeakerControlRequest(BaseModel):
    """스피커 제어 요청"""
    action: Literal["play", "stop"]
    audio_url: Optional[str] = Field(None, max_length=500)
    audio_file: Optional[str] = Field(None, max_length=200)
    volume: Optional[int] = Field(None, ge=0, le=100)


class DisplayControlRequest(BaseModel):
    """디스플레이 제어 요청"""
    action: Literal["show_text", "show_emoji", "clear"]
    content: Optional[str] = Field(None, max_length=500)
    emoji_id: Optional[str] = Field(None, max_length=50)


class SystemControlRequest(BaseModel):
    """시스템 제어 요청"""
    action: Literal["restart"]


class ControlResponse(BaseModel):
    """제어 응답"""
    success: bool
    message: str
    request_id: Optional[str] = None

