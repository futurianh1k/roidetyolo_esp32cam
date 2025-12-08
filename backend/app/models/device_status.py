"""
장비 상태 모델
"""
from sqlalchemy import Column, Integer, Float, Enum, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class ComponentStatus(str, enum.Enum):
    """컴포넌트 상태"""
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"


class DeviceStatus(Base):
    """장비 상태 테이블"""
    __tablename__ = "device_status"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 장비 상태 정보
    battery_level = Column(Integer, nullable=True)  # 0-100%
    memory_usage = Column(Integer, nullable=True)   # KB
    storage_usage = Column(Integer, nullable=True)  # KB
    temperature = Column(Float, nullable=True)      # 섭씨
    cpu_usage = Column(Integer, nullable=True)      # 0-100%
    
    # 컴포넌트 상태
    camera_status = Column(Enum(ComponentStatus), default=ComponentStatus.STOPPED, nullable=False)
    mic_status = Column(Enum(ComponentStatus), default=ComponentStatus.STOPPED, nullable=False)
    
    recorded_at = Column(TIMESTAMP, server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    device = relationship("Device", back_populates="status_records")
    
    def __repr__(self):
        return f"<DeviceStatus(id={self.id}, device_id={self.device_id}, battery={self.battery_level}%)>"

