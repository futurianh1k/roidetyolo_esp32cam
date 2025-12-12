# -*- coding: utf-8 -*-
"""
ASR 결과 스키마

ASR 결과 조회 및 검색을 위한 Pydantic 스키마
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ASRResultResponse(BaseModel):
    """ASR 결과 응답 스키마"""
    
    id: int
    device_id: int
    device_name: str
    session_id: str
    text: str
    timestamp: str
    duration: float
    is_emergency: bool
    emergency_keywords: List[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ASRResultListResponse(BaseModel):
    """ASR 결과 목록 응답 스키마"""
    
    total: int
    page: int
    page_size: int
    results: List[ASRResultResponse]


class ASRResultSearchRequest(BaseModel):
    """ASR 결과 검색 요청 스키마"""
    
    device_id: Optional[int] = None
    session_id: Optional[str] = None
    text_query: Optional[str] = Field(None, description="텍스트 검색 (부분 일치)")
    is_emergency: Optional[bool] = None
    start_date: Optional[str] = Field(None, description="시작 날짜 (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="종료 날짜 (YYYY-MM-DD)")
    page: int = Field(1, ge=1, description="페이지 번호")
    page_size: int = Field(20, ge=1, le=100, description="페이지 크기")


class ASRResultStatsResponse(BaseModel):
    """ASR 결과 통계 응답 스키마"""
    
    total_count: int
    emergency_count: int
    total_duration: float
    average_duration: float
    device_stats: List[dict]  # 장비별 통계

