"""
ASR API 라우터

음성인식 세션 관리 API

주요 기능:
- 장비의 음성인식 세션 시작/종료
- 세션 상태 조회
- MQTT로 CoreS3 장비에 명령 전송
- ASR 서버에서 음성인식 결과 수신 및 클라이언트에 브로드캐스트
"""

import logging
import json
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, Integer
from typing import Dict, Optional, List
from datetime import datetime, timedelta

from app.database import get_db
from app.models.device import Device
from app.models.asr_result import ASRResult
from app.schemas.asr import (
    ASRSessionStartRequest,
    ASRSessionStartResponse,
    ASRSessionStopRequest,
    ASRSessionStopResponse,
    ASRSessionStatusResponse,
    ASRSessionStatus,
    RecognitionResult,
)
from app.schemas.asr_result import (
    ASRResultResponse,
    ASRResultListResponse,
    ASRResultSearchRequest,
    ASRResultStatsResponse,
)
from app.schemas.emergency_alert import (
    EmergencyAlertResponse,
    EmergencyAlertListResponse,
    EmergencyAlertSearchRequest,
    EmergencyAlertStatsResponse,
)
from app.models.emergency_alert import AlertPriority, AlertStatus
from app.services.asr_service import asr_service
from app.services.mqtt_service import mqtt_service
from app.services.websocket_service import ws_manager
from app.utils.logger import logger

router = APIRouter(prefix="/asr", tags=["ASR (음성인식)"])


# 세션 상태 저장 (메모리)
# TODO: 데이터베이스에 저장하도록 개선
active_sessions: Dict[int, str] = {}  # {device_id: session_id}


@router.post(
    "/devices/{device_id}/session/start", response_model=ASRSessionStartResponse
)
async def start_device_asr_session(
    device_id: int,
    request: ASRSessionStartRequest,
    # TODO: 로그인 수정 후 활성화
    # current_user: User = Depends(require_operator),
    db: Session = Depends(get_db),
) -> ASRSessionStartResponse:
    """
    장비 음성인식 세션 시작

    장비의 음성인식 세션을 시작합니다.
    1. 장비 온라인 상태 확인
    2. ASR 서버에 세션 생성 요청
    3. MQTT로 CoreS3에 start_asr 명령 전송
    4. 세션 정보 반환

    Args:
        device_id: 장비 ID (데이터베이스 PK)
        request: 세션 시작 요청 (language, vad_enabled)
        db: 데이터베이스 세션

    Returns:
        세션 정보 (session_id, ws_url 등)

    Raises:
        HTTPException 404: 장비를 찾을 수 없음
        HTTPException 400: 장비가 오프라인 상태
        HTTPException 409: 이미 활성 세션이 존재
        HTTPException 500: ASR 서버 연결 실패 또는 MQTT 전송 실패

    Example:
        POST /asr/devices/1/session/start
        {
            "language": "ko",
            "vad_enabled": true
        }
    """
    logger.info(
        f"음성인식 세션 시작 요청: device_id={device_id}, language={request.language}"
    )

    # 1. 장비 확인
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        logger.warning(f"⚠️ 장비를 찾을 수 없음: {device_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="장비를 찾을 수 없습니다"
        )

    # 2. 장비 온라인 상태 확인
    if not device.is_online:
        logger.warning(f"⚠️ 장비 오프라인: {device.device_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="장비가 오프라인 상태입니다"
        )

    # 3. 이미 활성 세션이 있는지 확인
    if device_id in active_sessions:
        existing_session_id = active_sessions[device_id]
        logger.warning(
            f"⚠️ 이미 활성 세션 존재: device_id={device_id}, session_id={existing_session_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"이미 활성 세션이 존재합니다: {existing_session_id}",
        )

    try:
        # 4. ASR 서버에 세션 생성 요청
        logger.info(f"📡 ASR 서버에 세션 생성 요청: {device.device_id}")

        asr_result = await asr_service.create_session(
            device_id=device.device_id,
            language=request.language,
            vad_enabled=request.vad_enabled,
        )

        session_id = asr_result["session_id"]
        ws_url = asr_result["ws_url"]

        logger.info(f"✅ ASR 세션 생성 완료: {session_id}")

        # 5. MQTT로 CoreS3에 start_asr 명령 전송
        mqtt_topic = f"devices/{device.device_id}/control/microphone"
        mqtt_payload = {
            "command": "microphone",
            "action": "start_asr",
            "session_id": session_id,
            "ws_url": ws_url,
            "language": request.language,
            "request_id": f"asr_start_{device_id}_{session_id[:8]}",
        }

        logger.info(f"📤 MQTT 명령 전송: {mqtt_topic}")
        logger.debug(f"   Payload: {mqtt_payload}")

        mqtt_service.publish(mqtt_topic, json.dumps(mqtt_payload))

        # 6. 세션 상태 저장
        active_sessions[device_id] = session_id

        logger.info(
            f"✅ 음성인식 세션 시작 완료: device={device.device_name}, session={session_id}"
        )

        return ASRSessionStartResponse(
            session_id=session_id,
            device_id=device_id,
            device_name=device.device_name,
            ws_url=ws_url,
            status="started",
            message="음성인식이 시작되었습니다. CoreS3 장비가 자동으로 연결됩니다.",
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"❌ 음성인식 세션 시작 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"음성인식 세션 시작에 실패했습니다: {str(e)}",
        )


@router.post("/devices/{device_id}/session/stop", response_model=ASRSessionStopResponse)
async def stop_device_asr_session(
    device_id: int,
    request: ASRSessionStopRequest,
    # TODO: 로그인 수정 후 활성화
    # current_user: User = Depends(require_operator),
    db: Session = Depends(get_db),
) -> ASRSessionStopResponse:
    """
    장비 음성인식 세션 종료

    장비의 음성인식 세션을 종료합니다.
    1. 장비 확인
    2. MQTT로 CoreS3에 stop_asr 명령 전송
    3. ASR 서버에 세션 종료 요청
    4. 세션 상태 제거

    Args:
        device_id: 장비 ID
        request: 세션 종료 요청 (session_id)
        db: 데이터베이스 세션

    Returns:
        세션 종료 정보

    Raises:
        HTTPException 404: 장비를 찾을 수 없음
        HTTPException 400: 활성 세션이 없음
        HTTPException 500: ASR 서버 또는 MQTT 통신 실패

    Example:
        POST /asr/devices/1/session/stop
        {
            "session_id": "550e8400-e29b-41d4-a716-446655440000"
        }
    """
    logger.info(
        f"음성인식 세션 종료 요청: device_id={device_id}, session_id={request.session_id}"
    )

    # 1. 장비 확인
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        logger.warning(f"⚠️ 장비를 찾을 수 없음: {device_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="장비를 찾을 수 없습니다"
        )

    # 2. 활성 세션 확인
    if device_id not in active_sessions:
        logger.warning(f"⚠️ 활성 세션이 없음: device_id={device_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="활성 음성인식 세션이 없습니다",
        )

    stored_session_id = active_sessions[device_id]

    # 세션 ID 일치 확인 (선택적)
    if stored_session_id != request.session_id:
        logger.warning(
            f"⚠️ 세션 ID 불일치: stored={stored_session_id}, requested={request.session_id}"
        )

    try:
        # 3. MQTT로 CoreS3에 stop_asr 명령 전송
        mqtt_topic = f"devices/{device.device_id}/control/microphone"
        mqtt_payload = {
            "command": "microphone",
            "action": "stop_asr",
            "session_id": request.session_id,
            "request_id": f"asr_stop_{device_id}_{request.session_id[:8]}",
        }

        logger.info(f"📤 MQTT 종료 명령 전송: {mqtt_topic}")

        mqtt_service.publish(mqtt_topic, json.dumps(mqtt_payload))

        # 4. ASR 서버에 세션 종료 요청
        logger.info(f"📡 ASR 서버에 세션 종료 요청: {request.session_id}")

        asr_result = await asr_service.stop_session(request.session_id)

        # 5. 세션 상태 제거
        del active_sessions[device_id]

        logger.info(
            f"✅ 음성인식 세션 종료 완료: device={device.device_name}, session={request.session_id}"
        )

        return ASRSessionStopResponse(
            session_id=request.session_id,
            device_id=device_id,
            status="stopped",
            segments_count=asr_result.get("segments_count", 0),
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"❌ 음성인식 세션 종료 실패: {e}", exc_info=True)

        # 에러 발생해도 세션 상태는 제거
        if device_id in active_sessions:
            del active_sessions[device_id]

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"음성인식 세션 종료에 실패했습니다: {str(e)}",
        )


@router.get(
    "/devices/{device_id}/session/status", response_model=ASRSessionStatusResponse
)
async def get_device_asr_session_status(
    device_id: int,
    # TODO: 로그인 수정 후 활성화
    # current_user: User = Depends(require_operator),
    db: Session = Depends(get_db),
) -> ASRSessionStatusResponse:
    """
    장비 음성인식 세션 상태 조회

    장비의 현재 활성 음성인식 세션 상태를 조회합니다.

    Args:
        device_id: 장비 ID
        db: 데이터베이스 세션

    Returns:
        세션 상태 정보

    Raises:
        HTTPException 404: 장비를 찾을 수 없음

    Example:
        GET /asr/devices/1/session/status
    """
    logger.debug(f"음성인식 세션 상태 조회: device_id={device_id}")

    # 장비 확인
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="장비를 찾을 수 없습니다"
        )

    # 활성 세션 확인
    has_active_session = device_id in active_sessions
    session_info = None

    if has_active_session:
        session_id = active_sessions[device_id]

        try:
            # ASR 서버에서 세션 상태 조회
            asr_status = await asr_service.get_session_status(session_id)

            session_info = ASRSessionStatus(
                session_id=asr_status["session_id"],
                is_active=asr_status["is_active"],
                is_processing=asr_status["is_processing"],
                segments_count=asr_status["segments_count"],
                last_result=asr_status.get("last_result"),
                created_at=asr_status["created_at"],
            )

        except Exception as e:
            logger.error(f"❌ ASR 세션 상태 조회 실패: {e}")
            # 세션이 ASR 서버에 없으면 로컬 상태도 제거
            if device_id in active_sessions:
                del active_sessions[device_id]
            has_active_session = False

    return ASRSessionStatusResponse(
        device_id=device_id,
        device_name=device.device_name,
        has_active_session=has_active_session,
        session=session_info,
    )


@router.get("/sessions")
async def list_all_asr_sessions(
    # TODO: 로그인 수정 후 활성화
    # current_user: User = Depends(require_admin)
):
    """
    모든 활성 ASR 세션 목록 조회

    시스템의 모든 활성 음성인식 세션을 조회합니다.

    Returns:
        {
            'total': 2,
            'local_sessions': {...},
            'asr_server_sessions': {...}
        }

    Note:
        관리자 권한 필요 (현재는 인증 비활성화)

    Example:
        GET /asr/sessions
    """
    logger.debug("모든 ASR 세션 조회")

    try:
        # ASR 서버에서 세션 목록 조회
        asr_result = await asr_service.list_sessions()

        return {
            "total": len(active_sessions),
            "local_sessions": {
                device_id: session_id
                for device_id, session_id in active_sessions.items()
            },
            "asr_server_sessions": asr_result,
        }

    except Exception as e:
        logger.error(f"❌ ASR 세션 목록 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ASR 세션 목록 조회에 실패했습니다: {str(e)}",
        )


@router.get("/health")
async def asr_health_check():
    """
    ASR 서버 헬스 체크

    ASR 서버의 상태를 확인합니다.

    Returns:
        {
            'status': 'healthy',
            'asr_server': {...}
        }

    Example:
        GET /asr/health
    """
    logger.debug("ASR 서버 헬스 체크")

    try:
        health = await asr_service.health_check()

        return {
            "status": "healthy" if health.get("status") == "healthy" else "unhealthy",
            "asr_server": health,
        }

    except Exception as e:
        logger.error(f"❌ ASR 서버 헬스 체크 실패: {e}")
        return {"status": "unhealthy", "error": str(e)}


@router.post("/result")
async def receive_asr_result(
    result: RecognitionResult,
    db: Session = Depends(get_db),
):
    """
    ASR 서버로부터 음성인식 결과 수신

    RK3588 ASR 서버에서 음성인식이 완료되면 이 엔드포인트로 결과를 전송합니다.
    결과를 받으면 해당 장비를 구독 중인 모든 클라이언트에게 브로드캐스트합니다.

    Args:
        result: 음성인식 결과 데이터
            - device_id: 장비 ID
            - session_id: 세션 ID
            - text: 인식된 텍스트
            - timestamp: 인식 시각
            - duration: 음성 길이
            - is_emergency: 응급 상황 여부
            - emergency_keywords: 감지된 응급 키워드
        db: 데이터베이스 세션

    Returns:
        {
            "status": "success",
            "message": "음성인식 결과가 저장되었습니다",
            "broadcasted_to_users": [...],
            "timestamp": "2025-12-08T10:30:45.123456"
        }

    Example:
        POST /asr/result
        {
            "device_id": 1,
            "device_name": "CoreS3-01",
            "session_id": "550e8400-e29b-41d4-a716-446655440000",
            "text": "안녕하세요",
            "timestamp": "2025-12-08 10:30:45",
            "duration": 2.3,
            "is_emergency": false,
            "emergency_keywords": []
        }
    """
    logger.info(
        f"🎤 음성인식 결과 수신: device_id={result.device_id}, device_id_string={result.device_id_string}, text='{result.text}'"
    )

    try:
        # 1. 장비 확인 (device_id 또는 device_id_string으로 조회)
        device = None
        device_id_for_db = None

        if result.device_id:
            device = db.query(Device).filter(Device.id == result.device_id).first()
            device_id_for_db = result.device_id
        elif result.device_id_string:
            device = (
                db.query(Device)
                .filter(Device.device_id == result.device_id_string)
                .first()
            )
            if device:
                device_id_for_db = device.id
                # result 객체의 device_id 업데이트 (나중에 사용하기 위해)
                result.device_id = device.id

        if not device:
            device_id_str = (
                str(result.device_id) if result.device_id else result.device_id_string
            )
            logger.warning(
                f"⚠️ 장비를 찾을 수 없음: device_id={result.device_id}, device_id_string={result.device_id_string}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="장비를 찾을 수 없습니다"
            )

        device_id_for_db = device.id

        # 2. 응급 상황 감지 및 알림 이력 저장
        if result.is_emergency:
            logger.warning(
                f"🚨 응급 상황 감지: device_id={device_id_for_db}, keywords={result.emergency_keywords}"
            )

            # 응급 상황 알림 이력 생성 (전송 전)
            try:
                from app.services.emergency_alert_service import create_emergency_alert

                alert = create_emergency_alert(
                    db=db,
                    device_id=device_id_for_db,
                    recognized_text=result.text,
                    emergency_keywords=result.emergency_keywords,
                    asr_result_id=None,  # 아직 저장 전이므로 나중에 업데이트
                    sent=False,
                )
                logger.info(f"📝 응급 상황 알림 이력 생성: alert_id={alert.id}")
            except Exception as e:
                logger.error(f"❌ 응급 상황 알림 이력 생성 실패: {e}", exc_info=True)

        # 3. 데이터베이스에 결과 저장
        emergency_keywords_json = (
            json.dumps(result.emergency_keywords, ensure_ascii=False)
            if result.emergency_keywords
            else None
        )

        asr_result = ASRResult(
            device_id=device_id_for_db,
            session_id=result.session_id,
            text=result.text,
            timestamp=result.timestamp,
            duration=result.duration,
            is_emergency=result.is_emergency,
            emergency_keywords=emergency_keywords_json,
        )
        db.add(asr_result)
        db.commit()
        db.refresh(asr_result)

        logger.info(
            f"💾 ASR 결과 저장 완료: id={asr_result.id}, device_id={device_id_for_db}"
        )

        # 응급 상황인 경우 알림 이력의 asr_result_id 업데이트
        if result.is_emergency:
            try:
                from app.models.emergency_alert import EmergencyAlert

                alert = (
                    db.query(EmergencyAlert)
                    .filter(
                        EmergencyAlert.device_id == device_id_for_db,
                        EmergencyAlert.asr_result_id.is_(None),
                        EmergencyAlert.recognized_text == result.text,
                    )
                    .order_by(EmergencyAlert.created_at.desc())
                    .first()
                )

                if alert:
                    alert.asr_result_id = asr_result.id
                    db.commit()
                    logger.info(
                        f"✅ 알림 이력에 ASR 결과 ID 연결: alert_id={alert.id}, asr_result_id={asr_result.id}"
                    )
            except Exception as e:
                logger.error(f"❌ 알림 이력 업데이트 실패: {e}", exc_info=True)

        # 4. WebSocket으로 구독 중인 클라이언트들에게 브로드캐스트
        message = {
            "type": "asr_result",
            "device_id": device_id_for_db,
            "device_name": result.device_name,
            "session_id": result.session_id,
            "text": result.text,
            "timestamp": result.timestamp,
            "duration": result.duration,
            "is_emergency": result.is_emergency,
            "emergency_keywords": result.emergency_keywords,
        }

        # 장비를 구독 중인 모든 사용자에게 브로드캐스트
        await ws_manager.broadcast_to_subscribers(device_id_for_db, message)

        logger.info(
            f"✅ 음성인식 결과 브로드캐스트 완료: {device_id_for_db} -> {len(ws_manager.device_subscriptions.get(device_id_for_db, set()))} 사용자"
        )

        # 5. 응답 반환
        return {
            "status": "success",
            "message": "음성인식 결과가 저장되었습니다",
            "device_id": device_id_for_db,
            "text": result.text,
            "is_emergency": result.is_emergency,
            "broadcasted_count": len(
                ws_manager.device_subscriptions.get(device_id_for_db, set())
            ),
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"❌ 음성인식 결과 처리 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"음성인식 결과 처리에 실패했습니다: {str(e)}",
        )


@router.get("/results", response_model=ASRResultListResponse)
async def get_asr_results(
    device_id: Optional[int] = Query(None, description="장비 ID 필터"),
    session_id: Optional[str] = Query(None, description="세션 ID 필터"),
    is_emergency: Optional[bool] = Query(None, description="응급 상황 필터"),
    text_query: Optional[str] = Query(None, description="텍스트 검색"),
    start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    db: Session = Depends(get_db),
):
    """
    ASR 결과 조회 (검색 및 필터링 지원)

    Args:
        device_id: 장비 ID로 필터링
        session_id: 세션 ID로 필터링
        is_emergency: 응급 상황 여부로 필터링
        text_query: 텍스트 검색 (부분 일치)
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date: 종료 날짜 (YYYY-MM-DD)
        page: 페이지 번호
        page_size: 페이지 크기

    Returns:
        ASR 결과 목록
    """
    try:
        # 쿼리 빌드
        query = db.query(ASRResult, Device.device_name).join(
            Device, ASRResult.device_id == Device.id
        )

        # 필터 적용
        if device_id:
            query = query.filter(ASRResult.device_id == device_id)

        if session_id:
            query = query.filter(ASRResult.session_id == session_id)

        if is_emergency is not None:
            query = query.filter(ASRResult.is_emergency == is_emergency)

        if text_query:
            query = query.filter(ASRResult.text.contains(text_query))

        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(ASRResult.created_at >= start_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="시작 날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식을 사용하세요.",
                )

        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                query = query.filter(ASRResult.created_at < end_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="종료 날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식을 사용하세요.",
                )

        # 총 개수
        total = query.count()

        # 정렬 및 페이지네이션
        results = (
            query.order_by(ASRResult.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        # 응답 형식 변환
        result_list = []
        for asr_result, device_name in results:
            emergency_keywords = []
            if asr_result.emergency_keywords:
                try:
                    emergency_keywords = json.loads(asr_result.emergency_keywords)
                except (json.JSONDecodeError, TypeError):
                    emergency_keywords = []

            result_list.append(
                ASRResultResponse(
                    id=asr_result.id,
                    device_id=asr_result.device_id,
                    device_name=device_name,
                    session_id=asr_result.session_id,
                    text=asr_result.text,
                    timestamp=asr_result.timestamp,
                    duration=asr_result.duration,
                    is_emergency=asr_result.is_emergency,
                    emergency_keywords=emergency_keywords,
                    created_at=asr_result.created_at,
                )
            )

        return ASRResultListResponse(
            total=total,
            page=page,
            page_size=page_size,
            results=result_list,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ ASR 결과 조회 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ASR 결과 조회에 실패했습니다: {str(e)}",
        )


@router.get("/results/stats", response_model=ASRResultStatsResponse)
async def get_asr_stats(
    device_id: Optional[int] = Query(None, description="장비 ID 필터"),
    start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """
    ASR 결과 통계 조회

    Args:
        device_id: 장비 ID로 필터링
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date: 종료 날짜 (YYYY-MM-DD)

    Returns:
        ASR 결과 통계
    """
    try:
        # 쿼리 빌드
        query = db.query(ASRResult)

        # 필터 적용
        if device_id:
            query = query.filter(ASRResult.device_id == device_id)

        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(ASRResult.created_at >= start_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="시작 날짜 형식이 올바르지 않습니다.",
                )

        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                query = query.filter(ASRResult.created_at < end_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="종료 날짜 형식이 올바르지 않습니다.",
                )

        # 통계 계산
        total_count = query.count()
        emergency_count = query.filter(ASRResult.is_emergency == True).count()

        duration_stats = (
            db.query(
                func.sum(ASRResult.duration).label("total_duration"),
                func.avg(ASRResult.duration).label("avg_duration"),
            )
            .filter(ASRResult.id.in_([r.id for r in query.all()]))
            .first()
        )

        total_duration = duration_stats.total_duration or 0.0
        average_duration = duration_stats.avg_duration or 0.0

        # 장비별 통계
        device_stats_query = db.query(
            ASRResult.device_id,
            Device.device_name,
            func.count(ASRResult.id).label("count"),
            func.sum(ASRResult.duration).label("total_duration"),
            func.sum(func.cast(ASRResult.is_emergency, Integer)).label(
                "emergency_count"
            ),
        ).join(Device, ASRResult.device_id == Device.id)

        if device_id:
            device_stats_query = device_stats_query.filter(
                ASRResult.device_id == device_id
            )

        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            device_stats_query = device_stats_query.filter(
                ASRResult.created_at >= start_dt
            )

        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            device_stats_query = device_stats_query.filter(
                ASRResult.created_at < end_dt
            )

        device_stats = device_stats_query.group_by(
            ASRResult.device_id, Device.device_name
        ).all()

        device_stats_list = [
            {
                "device_id": stat.device_id,
                "device_name": stat.device_name,
                "count": stat.count,
                "total_duration": float(stat.total_duration or 0.0),
                "emergency_count": stat.emergency_count or 0,
            }
            for stat in device_stats
        ]

        return ASRResultStatsResponse(
            total_count=total_count,
            emergency_count=emergency_count,
            total_duration=float(total_duration),
            average_duration=float(average_duration),
            device_stats=device_stats_list,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ ASR 통계 조회 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ASR 통계 조회에 실패했습니다: {str(e)}",
        )


@router.get("/results/{result_id}", response_model=ASRResultResponse)
async def get_asr_result(
    result_id: int,
    db: Session = Depends(get_db),
):
    """
    특정 ASR 결과 조회

    Args:
        result_id: ASR 결과 ID

    Returns:
        ASR 결과 상세 정보
    """
    try:
        result = (
            db.query(ASRResult, Device.device_name)
            .join(Device, ASRResult.device_id == Device.id)
            .filter(ASRResult.id == result_id)
            .first()
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ASR 결과를 찾을 수 없습니다: {result_id}",
            )

        asr_result, device_name = result

        emergency_keywords = []
        if asr_result.emergency_keywords:
            try:
                emergency_keywords = json.loads(asr_result.emergency_keywords)
            except (json.JSONDecodeError, TypeError):
                emergency_keywords = []

        return ASRResultResponse(
            id=asr_result.id,
            device_id=asr_result.device_id,
            device_name=device_name,
            session_id=asr_result.session_id,
            text=asr_result.text,
            timestamp=asr_result.timestamp,
            duration=asr_result.duration,
            is_emergency=asr_result.is_emergency,
            emergency_keywords=emergency_keywords,
            created_at=asr_result.created_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ ASR 결과 조회 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ASR 결과 조회에 실패했습니다: {str(e)}",
        )
