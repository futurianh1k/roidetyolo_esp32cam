# -*- coding: utf-8 -*-
"""
응급 상황 알림 서비스

응급 상황 알림 전송 및 이력 관리
"""

import logging
import json
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.emergency_alert import EmergencyAlert, AlertPriority, AlertStatus
from app.models.asr_result import ASRResult

logger = logging.getLogger(__name__)


def calculate_priority(emergency_keywords: List[str]) -> AlertPriority:
    """
    응급 키워드를 기반으로 우선순위 계산
    
    Args:
        emergency_keywords: 응급 키워드 리스트
    
    Returns:
        AlertPriority: 계산된 우선순위
    """
    # 키워드 기반 우선순위 매핑
    critical_keywords = ["쓰러졌어", "의식없어", "심장마비", "호흡곤란"]
    high_keywords = ["도와줘", "구조", "응급", "위험"]
    medium_keywords = ["아파", "불편", "도움"]
    
    keywords_lower = [kw.lower() for kw in emergency_keywords]
    
    # Critical 우선순위 체크
    if any(kw in keywords_lower for kw in critical_keywords):
        return AlertPriority.CRITICAL
    
    # High 우선순위 체크
    if any(kw in keywords_lower for kw in high_keywords):
        return AlertPriority.HIGH
    
    # Medium 우선순위 체크
    if any(kw in keywords_lower for kw in medium_keywords):
        return AlertPriority.MEDIUM
    
    # 기본값
    return AlertPriority.LOW


def create_emergency_alert(
    db: Session,
    device_id: int,
    recognized_text: str,
    emergency_keywords: List[str],
    asr_result_id: Optional[int] = None,
    api_endpoint: Optional[str] = None,
    api_response: Optional[str] = None,
    sent: bool = False,
) -> EmergencyAlert:
    """
    응급 상황 알림 이력 생성
    
    Args:
        db: 데이터베이스 세션
        device_id: 장비 ID
        recognized_text: 인식된 텍스트
        emergency_keywords: 응급 키워드 리스트
        asr_result_id: ASR 결과 ID (선택)
        api_endpoint: API 엔드포인트 (선택)
        api_response: API 응답 (선택)
        sent: 전송 성공 여부
    
    Returns:
        EmergencyAlert: 생성된 알림 이력
    """
    # 우선순위 계산
    priority = calculate_priority(emergency_keywords)
    
    # 상태 설정
    status = AlertStatus.SENT if sent else AlertStatus.PENDING
    
    # 키워드를 JSON 형식으로 저장
    keywords_json = json.dumps(emergency_keywords, ensure_ascii=False)
    
    # 알림 이력 생성
    alert = EmergencyAlert(
        device_id=device_id,
        asr_result_id=asr_result_id,
        recognized_text=recognized_text,
        emergency_keywords=keywords_json,
        priority=priority,
        status=status,
        api_endpoint=api_endpoint,
        api_response=api_response,
        sent_at=datetime.now() if sent else None,
    )
    
    db.add(alert)
    db.commit()
    db.refresh(alert)
    
    logger.info(
        f"📝 응급 상황 알림 이력 생성: id={alert.id}, device_id={device_id}, "
        f"priority={priority}, status={status}"
    )
    
    return alert


def update_alert_status(
    db: Session,
    alert_id: int,
    status: AlertStatus,
    api_response: Optional[str] = None,
) -> Optional[EmergencyAlert]:
    """
    알림 상태 업데이트
    
    Args:
        db: 데이터베이스 세션
        alert_id: 알림 ID
        status: 새로운 상태
        api_response: API 응답 (선택)
    
    Returns:
        EmergencyAlert: 업데이트된 알림 이력
    """
    alert = db.query(EmergencyAlert).filter(EmergencyAlert.id == alert_id).first()
    
    if not alert:
        logger.warning(f"⚠️ 알림을 찾을 수 없음: {alert_id}")
        return None
    
    alert.status = status
    
    if status == AlertStatus.SENT:
        alert.sent_at = datetime.now()
    
    if api_response:
        alert.api_response = api_response
    
    db.commit()
    db.refresh(alert)
    
    logger.info(f"✅ 알림 상태 업데이트: id={alert_id}, status={status}")
    
    return alert


def acknowledge_alert(
    db: Session,
    alert_id: int,
    user_id: int,
) -> Optional[EmergencyAlert]:
    """
    알림 확인 처리
    
    Args:
        db: 데이터베이스 세션
        alert_id: 알림 ID
        user_id: 확인한 사용자 ID
    
    Returns:
        EmergencyAlert: 업데이트된 알림 이력
    """
    alert = db.query(EmergencyAlert).filter(EmergencyAlert.id == alert_id).first()
    
    if not alert:
        logger.warning(f"⚠️ 알림을 찾을 수 없음: {alert_id}")
        return None
    
    alert.status = AlertStatus.ACKNOWLEDGED
    alert.acknowledged_at = datetime.now()
    alert.acknowledged_by = user_id
    
    db.commit()
    db.refresh(alert)
    
    logger.info(f"✅ 알림 확인 처리: id={alert_id}, user_id={user_id}")
    
    return alert

