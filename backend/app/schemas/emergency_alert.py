# -*- coding: utf-8 -*-
"""
응급 상황 알림 스키마

응급 상황 알림 조회 및 관리를 위한 Pydantic 스키마
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.emergency_alert import AlertPriority, AlertStatus


class EmergencyAlertResponse(BaseModel):
    """응급 상황 알림 응답 스키마"""
    
    id: int
    device_id: int
    device_name: str
    asr_result_id: Optional[int]
    recognized_text: str
    emergency_keywords: List[str]
    priority: AlertPriority
    status: AlertStatus
    api_endpoint: Optional[str]
    api_response: Optional[str]
    sent_at: Optional[datetime]
    created_at: datetime
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[int]
    acknowledged_by_username: Optional[str]
    
    class Config:
        from_attributes = True


class EmergencyAlertListResponse(BaseModel):
    """응급 상황 알림 목록 응답 스키마"""
    
    total: int
    page: int
    page_size: int
    alerts: List[EmergencyAlertResponse]


class EmergencyAlertSearchRequest(BaseModel):
    """응급 상황 알림 검색 요청 스키마"""
    
    device_id: Optional[int] = None
    priority: Optional[AlertPriority] = None
    status: Optional[AlertStatus] = None
    start_date: Optional[str] = Field(None, description="시작 날짜 (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="종료 날짜 (YYYY-MM-DD)")
    page: int = Field(1, ge=1, description="페이지 번호")
    page_size: int = Field(20, ge=1, le=100, description="페이지 크기")


class EmergencyAlertStatsResponse(BaseModel):
    """응급 상황 알림 통계 응답 스키마"""
    
    total_count: int
    by_priority: dict
    by_status: dict
    by_device: List[dict]
    recent_alerts: List[dict]  # 최근 10개 알림

