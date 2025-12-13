"""
알람 발송 이력 모델

알람 타입:
- sound: 사운드/비프음 재생
- text: TTS 텍스트 음성 변환
- recorded: 녹음된 메시지 재생
"""

from sqlalchemy import Column, Integer, String, TIMESTAMP, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class AlarmType(str, enum.Enum):
    """알람 타입"""

    SOUND = "sound"  # 사운드/비프음 (beep, alert, notification, emergency)
    TEXT = "text"  # TTS 텍스트
    RECORDED = "recorded"  # 녹음된 메시지


class AlarmTrigger(str, enum.Enum):
    """알람 트리거 (누가 활성화했는지)"""

    SYSTEM = "system"  # 시스템 자동
    ADMIN = "admin"  # 관리자
    USER = "user"  # 일반 사용자
    SCHEDULE = "schedule"  # 스케줄


class AlarmHistory(Base):
    """알람 발송 이력 테이블"""

    __tablename__ = "alarm_history"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)

    # 알람 정보
    alarm_type = Column(String(20), nullable=False, index=True)  # sound, text, recorded
    alarm_subtype = Column(
        String(50), nullable=True
    )  # beep, alert, emergency 또는 파일명 등
    content = Column(Text, nullable=True)  # TTS 텍스트 또는 파일 경로

    # 트리거 정보
    triggered_by = Column(
        String(20), nullable=False, default="system"
    )  # system, admin, user, schedule
    triggered_user_id = Column(
        Integer, ForeignKey("users.id"), nullable=True
    )  # 사용자가 트리거한 경우

    # 메타데이터
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    parameters = Column(Text, nullable=True)  # JSON 형태의 추가 파라미터

    # 상태
    status = Column(
        String(20), default="sent", nullable=False
    )  # sent, delivered, failed

    # Relationships
    device = relationship("Device", backref="alarm_history")
    triggered_user = relationship("User", backref="triggered_alarms")

    def __repr__(self):
        return f"<AlarmHistory(id={self.id}, device={self.device_id}, type={self.alarm_type}, by={self.triggered_by})>"
