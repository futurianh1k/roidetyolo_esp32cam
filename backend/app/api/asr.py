"""
ASR API 라우터

음성인식 세션 관리 API

주요 기능:
- 장비의 음성인식 세션 시작/종료
- 세션 상태 조회
- MQTT로 CoreS3 장비에 명령 전송
"""

import logging
import json
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Dict

from app.database import get_db
from app.models.device import Device
from app.schemas.asr import (
    ASRSessionStartRequest,
    ASRSessionStartResponse,
    ASRSessionStopRequest,
    ASRSessionStopResponse,
    ASRSessionStatusResponse,
    ASRSessionStatus,
)
from app.services.asr_service import asr_service
from app.services.mqtt_service import mqtt_service
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
