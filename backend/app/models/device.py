"""
장비 관련 모델
"""

from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Device(Base):
    """장비 테이블"""

    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(
        String(50), unique=True, nullable=False, index=True
    )  # MAC 주소 또는 고유 ID
    device_name = Column(String(100), nullable=False)
    device_type = Column(String(50), default="CoreS3", nullable=False)
    ip_address = Column(String(45), nullable=True)
    rtsp_url = Column(String(255), nullable=True)
    mqtt_topic = Column(String(100), nullable=True)
    is_online = Column(Boolean, default=False, nullable=False, index=True)
    registered_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    last_seen_at = Column(TIMESTAMP, nullable=True)
    location = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    status_report_interval = Column(
        Integer, default=60, nullable=False
    )  # 상태 보고 주기 (초), 기본값 60초

    # 카메라 스트림 전송 설정
    camera_sink_url = Column(String(500), nullable=True)  # 영상 sink URL
    camera_stream_mode = Column(
        String(50), default="mjpeg_stills", nullable=True
    )  # 전송 방식: mjpeg_stills, realtime_websocket, realtime_rtsp
    camera_frame_interval_ms = Column(
        Integer, default=1000, nullable=False
    )  # 프레임 전송 주기 (ms), 기본값 1000ms

    # Relationships
    status_records = relationship(
        "DeviceStatus", back_populates="device", cascade="all, delete-orphan"
    )
    audit_logs = relationship("AuditLog", back_populates="device")
    asr_results = relationship(
        "ASRResult", back_populates="device", cascade="all, delete-orphan"
    )
    emergency_alerts = relationship(
        "EmergencyAlert", back_populates="device", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Device(id={self.id}, device_id='{self.device_id}', name='{self.device_name}')>"
