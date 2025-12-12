# -*- coding: utf-8 -*-
"""
ASR 결과 모델

음성인식 결과를 데이터베이스에 저장하는 모델
"""

from sqlalchemy import Column, Integer, String, Boolean, Float, TIMESTAMP, Text, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class ASRResult(Base):
    """ASR 결과 테이블"""
    __tablename__ = "asr_results"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(100), nullable=False, index=True)  # ASR 세션 ID
    
    # 인식 결과
    text = Column(Text, nullable=False)  # 인식된 텍스트
    timestamp = Column(String(50), nullable=False)  # 인식 시각 (문자열 형식)
    duration = Column(Float, nullable=False)  # 음성 길이 (초)
    
    # 응급 상황 정보
    is_emergency = Column(Boolean, default=False, nullable=False, index=True)
    emergency_keywords = Column(Text, nullable=True)  # JSON 형식으로 저장: ["키워드1", "키워드2"]
    
    # 메타데이터
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    device = relationship("Device", back_populates="asr_results")
    
    # 인덱스: 장비별 조회, 응급 상황 조회, 시간 범위 조회 최적화
    __table_args__ = (
        Index('idx_device_created', 'device_id', 'created_at'),
        Index('idx_emergency_created', 'is_emergency', 'created_at'),
    )
    
    def __repr__(self):
        return f"<ASRResult(id={self.id}, device_id={self.device_id}, text='{self.text[:30]}...', emergency={self.is_emergency})>"

