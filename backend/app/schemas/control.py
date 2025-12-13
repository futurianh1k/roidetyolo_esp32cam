"""
장비 제어 관련 Pydantic 스키마
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal


class CameraControlRequest(BaseModel):
    """
    카메라 제어 요청

    영상 sink 전송 기능:
    - sink_url: 영상 sink 주소 (URL)
    - stream_mode: 전송 방식 (mjpeg_stills, realtime_websocket, realtime_rtsp)
    - frame_interval: 프레임 간격 (ms, 스틸컷일 경우)
    """

    action: Literal["start", "pause", "stop"]
    sink_url: Optional[str] = Field(
        None,
        max_length=500,
        description="영상 sink 주소 (URL). 예: http://192.168.1.100:8080/video, ws://192.168.1.100:8080/stream, rtsp://192.168.1.100:8554/stream",
    )
    stream_mode: Optional[
        Literal["mjpeg_stills", "realtime_websocket", "realtime_rtsp"]
    ] = Field(
        None,
        description="전송 방식. mjpeg_stills: 주기적 JPEG 스틸컷, realtime_websocket: WebSocket 실시간 스트림, realtime_rtsp: RTSP 실시간 스트림",
    )
    frame_interval: Optional[int] = Field(
        None,
        ge=100,
        le=10000,
        description="프레임 간격 (밀리초, mjpeg_stills 모드일 경우만 사용). 최소 100ms, 최대 10000ms",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "action": "start",
                "sink_url": "http://192.168.1.100:8080/video",
                "stream_mode": "mjpeg_stills",
                "frame_interval": 1000,
            }
        }


class MicrophoneControlRequest(BaseModel):
    """
    마이크 제어 요청

    액션:
    - start: 일반 마이크 시작
    - pause: 일시정지
    - stop: 정지
    - start_asr: 음성인식 모드로 시작 (ASR 서버 연동)
    - stop_asr: 음성인식 모드 종료

    오디오 WebSocket 전송 기능:
    - ws_url: 오디오 스트림을 전송할 WebSocket 주소 (start 액션일 때 선택사항)
    """

    action: Literal["start", "pause", "stop", "start_asr", "stop_asr"]
    ws_url: Optional[str] = Field(
        None,
        max_length=500,
        description="오디오 WebSocket 주소 (URL). 예: ws://192.168.1.100:8080/audio",
    )

    class Config:
        json_schema_extra = {
            "example": {"action": "start", "ws_url": "ws://192.168.1.100:8080/audio"}
        }


class SpeakerControlRequest(BaseModel):
    """
    스피커 제어 요청

    액션:
    - play: 오디오 파일 재생 (audio_url 또는 audio_file 필요)
    - play_alarm: 내장 알람음 재생 (alarm_type 필요)
    - play_beep: 비프음 생성 및 재생 (frequency, duration 필요)
    - stop: 재생 중지
    """

    action: Literal["play", "play_alarm", "play_beep", "stop"]
    audio_url: Optional[str] = Field(None, max_length=500)
    audio_file: Optional[str] = Field(None, max_length=200)
    volume: Optional[int] = Field(None, ge=0, le=100)

    # play_alarm용 필드
    alarm_type: Optional[Literal["beep", "alert", "notification", "emergency"]] = Field(
        None,
        description="알람 타입: beep(짧은비프), alert(경고), notification(알림), emergency(긴급)",
    )
    repeat: Optional[int] = Field(None, ge=1, le=10, description="반복 횟수 (1-10)")

    # play_beep용 필드
    frequency: Optional[int] = Field(
        None, ge=200, le=5000, description="주파수 (Hz, 200-5000)"
    )
    duration: Optional[int] = Field(
        None, ge=50, le=5000, description="지속 시간 (ms, 50-5000)"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {"action": "play_alarm", "alarm_type": "emergency", "repeat": 2},
                {
                    "action": "play_beep",
                    "frequency": 1000,
                    "duration": 200,
                    "volume": 80,
                },
                {"action": "play", "audio_file": "alert.wav", "volume": 100},
            ]
        }


class DisplayControlRequest(BaseModel):
    """디스플레이 제어 요청"""

    action: Literal["show_text", "show_emoji", "clear"]
    content: Optional[str] = Field(None, max_length=500)
    emoji_id: Optional[str] = Field(None, max_length=50)


class SystemControlRequest(BaseModel):
    """
    시스템 제어 요청

    액션:
    - restart: 장비 재시작
    - wake: 장비 깨우기
    - sleep: 절전 모드 전환
    - set_interval: 상태 보고 주기 변경 (interval 필수)
    """

    action: Literal["restart", "wake", "sleep", "set_interval"]
    interval: Optional[int] = Field(
        None,
        ge=10,
        le=3600,
        description="상태 보고 주기 (초). set_interval 액션 시 필수. 최소 10초, 최대 3600초",
    )


class ControlResponse(BaseModel):
    """제어 응답"""

    success: bool
    message: str
    request_id: Optional[str] = None
