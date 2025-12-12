# -*- coding: utf-8 -*-
"""
응급 상황 알림 모델

응급 상황 알림 이력을 저장하는 모델
"""

from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, Text, ForeignKey, Enum, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class AlertPriority(str, enum.Enum):
    """알림 우선순위"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, enum.Enum):
    """알림 상태"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    ACKNOWLEDGED = "acknowledged"


class EmergencyAlert(Base):
    """응급 상황 알림 테이블"""
    __tablename__ = "emergency_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    asr_result_id = Column(Integer, ForeignKey("asr_results.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # 알림 내용
    recognized_text = Column(Text, nullable=False)  # 인식된 텍스트
    emergency_keywords = Column(Text, nullable=False)  # JSON 형식: ["키워드1", "키워드2"]
    
    # 우선순위 및 상태
    priority = Column(Enum(AlertPriority, native_enum=False), default=AlertPriority.MEDIUM, nullable=False, index=True)
    status = Column(Enum(AlertStatus, native_enum=False), default=AlertStatus.PENDING, nullable=False, index=True)
    
    # API 전송 정보
    api_endpoint = Column(String(255), nullable=True)  # 전송한 API 엔드포인트
    api_response = Column(Text, nullable=True)  # API 응답 (성공/실패 정보)
    sent_at = Column(TIMESTAMP, nullable=True)  # 전송 시각
    
    # 메타데이터
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False, index=True)
    acknowledged_at = Column(TIMESTAMP, nullable=True)  # 확인 시각
    acknowledged_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # 확인한 사용자
    
    # Relationships
    device = relationship("Device", back_populates="emergency_alerts")
    asr_result = relationship("ASRResult")
    acknowledged_user = relationship("User")
    
    # 인덱스
    __table_args__ = (
        Index('idx_device_priority_created', 'device_id', 'priority', 'created_at'),
        Index('idx_status_created', 'status', 'created_at'),
    )
    
    def __repr__(self):
        return f"<EmergencyAlert(id={self.id}, device_id={self.device_id}, priority={self.priority}, status={self.status})>"

