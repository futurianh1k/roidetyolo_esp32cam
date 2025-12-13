"""
알람 이력 API 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models import AlarmHistory, Device
from app.schemas.alarm_history import (
    AlarmHistoryResponse,
    AlarmHistoryListResponse,
)
from app.utils.logger import logger

router = APIRouter(prefix="/alarm-history", tags=["alarm-history"])


@router.get("", response_model=AlarmHistoryListResponse)
async def get_alarm_history(
    device_id: Optional[int] = Query(None, description="장비 ID로 필터링"),
    alarm_type: Optional[str] = Query(
        None, description="알람 타입 (sound, text, recorded)"
    ),
    triggered_by: Optional[str] = Query(
        None, description="트리거 주체 (system, admin, user, schedule)"
    ),
    start_date: Optional[datetime] = Query(None, description="시작 날짜"),
    end_date: Optional[datetime] = Query(None, description="종료 날짜"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    db: Session = Depends(get_db),
) -> AlarmHistoryListResponse:
    """
    알람 이력 목록 조회

    필터:
    - device_id: 특정 장비의 이력만 조회
    - alarm_type: 알람 타입 필터 (sound, text, recorded)
    - triggered_by: 트리거 주체 필터 (system, admin, user, schedule)
    - start_date, end_date: 날짜 범위 필터
    """
    query = db.query(AlarmHistory)

    # 필터 적용
    if device_id:
        query = query.filter(AlarmHistory.device_id == device_id)
    if alarm_type:
        query = query.filter(AlarmHistory.alarm_type == alarm_type)
    if triggered_by:
        query = query.filter(AlarmHistory.triggered_by == triggered_by)
    if start_date:
        query = query.filter(AlarmHistory.created_at >= start_date)
    if end_date:
        query = query.filter(AlarmHistory.created_at <= end_date)

    # 전체 개수
    total = query.count()

    # 정렬 및 페이지네이션
    items = (
        query.order_by(desc(AlarmHistory.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return AlarmHistoryListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/device/{device_id}", response_model=AlarmHistoryListResponse)
async def get_device_alarm_history(
    device_id: int,
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    db: Session = Depends(get_db),
) -> AlarmHistoryListResponse:
    """특정 장비의 알람 이력 조회"""
    # 장비 존재 확인
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="장비를 찾을 수 없습니다",
        )

    query = db.query(AlarmHistory).filter(AlarmHistory.device_id == device_id)

    total = query.count()

    items = (
        query.order_by(desc(AlarmHistory.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return AlarmHistoryListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{history_id}", response_model=AlarmHistoryResponse)
async def get_alarm_history_detail(
    history_id: int,
    db: Session = Depends(get_db),
) -> AlarmHistoryResponse:
    """알람 이력 상세 조회"""
    history = db.query(AlarmHistory).filter(AlarmHistory.id == history_id).first()

    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="알람 이력을 찾을 수 없습니다",
        )

    return history


@router.delete("/{history_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alarm_history(
    history_id: int,
    db: Session = Depends(get_db),
):
    """알람 이력 삭제 (관리자 전용)"""
    history = db.query(AlarmHistory).filter(AlarmHistory.id == history_id).first()

    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="알람 이력을 찾을 수 없습니다",
        )

    db.delete(history)
    db.commit()

    logger.info(f"알람 이력 삭제: id={history_id}")
