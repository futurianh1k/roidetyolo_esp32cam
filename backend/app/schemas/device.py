"""
장비 관련 Pydantic 스키마
보안 가이드라인 3-1 준수: 입력 검증
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional
from datetime import datetime

from app.models.device_status import ComponentStatus
from app.utils.validators import validate_device_id, validate_ip_address, validate_mqtt_topic


class DeviceBase(BaseModel):
    """장비 기본 스키마"""
    device_id: str = Field(..., min_length=3, max_length=50)
    device_name: str = Field(..., min_length=1, max_length=100)
    device_type: str = Field(default="CoreS3", max_length=50)
    ip_address: Optional[str] = Field(None, max_length=45)
    mqtt_topic: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    
    @field_validator('device_id')
    def validate_device_id_format(cls, v):
        if not validate_device_id(v):
            raise ValueError('유효하지 않은 장비 ID 형식입니다')
        return v
    
    @field_validator('ip_address')
    def validate_ip_format(cls, v):
        if v and not validate_ip_address(v):
            raise ValueError('유효하지 않은 IP 주소 형식입니다')
        return v
    
    @field_validator('mqtt_topic')
    def validate_topic_format(cls, v):
        if v and not validate_mqtt_topic(v):
            raise ValueError('유효하지 않은 MQTT 토픽 형식입니다')
        return v


class DeviceCreate(DeviceBase):
    """장비 생성 스키마"""
    pass


class DeviceUpdate(BaseModel):
    """장비 수정 스키마"""
    device_name: Optional[str] = Field(None, min_length=1, max_length=100)
    ip_address: Optional[str] = Field(None, max_length=45)
    mqtt_topic: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    is_online: Optional[bool] = None


class DeviceResponse(DeviceBase):
    """장비 응답 스키마"""
    id: int
    rtsp_url: Optional[str] = None
    is_online: bool
    registered_at: datetime
    last_seen_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class DeviceListResponse(BaseModel):
    """장비 목록 응답 스키마"""
    devices: list[DeviceResponse]
    total: int
    page: int
    page_size: int


class DeviceStatusCreate(BaseModel):
    """장비 상태 생성 스키마"""
    battery_level: Optional[int] = Field(None, ge=0, le=100)
    memory_usage: Optional[int] = Field(None, ge=0)
    storage_usage: Optional[int] = Field(None, ge=0)
    temperature: Optional[float] = Field(None, ge=-40, le=125)
    cpu_usage: Optional[int] = Field(None, ge=0, le=100)
    camera_status: ComponentStatus = ComponentStatus.STOPPED
    mic_status: ComponentStatus = ComponentStatus.STOPPED


class DeviceStatusResponse(DeviceStatusCreate):
    """장비 상태 응답 스키마"""
    id: int
    device_id: int
    recorded_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DeviceStatusListResponse(BaseModel):
    """장비 상태 목록 응답 스키마"""
    statuses: list[DeviceStatusResponse]
    total: int

