"""
장비 제어 API 엔드포인트
보안 가이드라인 2, 9 준수: 권한 제어, 감사 로그
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Device, User, AuditLog
from app.schemas.control import (
    CameraControlRequest,
    MicrophoneControlRequest,
    SpeakerControlRequest,
    DisplayControlRequest,
    ControlResponse,
)
from app.dependencies import (
    require_operator,
    get_client_ip,
)
from app.services import get_mqtt_service
from app.utils.logger import logger


router = APIRouter(prefix="/control", tags=["장비 제어"])


@router.post("/devices/{device_id}/camera", response_model=ControlResponse)
async def control_camera(
    device_id: int,
    control: CameraControlRequest,
    current_user: User = Depends(require_operator),
    db: Session = Depends(get_db),
    request: Request = None
) -> ControlResponse:
    """
    카메라 제어
    
    권한: OPERATOR 이상
    액션: start, pause, stop
    """
    # 장비 확인
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="장비를 찾을 수 없습니다"
        )
    
    if not device.is_online:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="장비가 오프라인 상태입니다"
        )
    
    try:
        # MQTT 명령 전송
        mqtt = get_mqtt_service()
        request_id = mqtt.send_control_command(
            device_id=device.device_id,
            command="camera",
            action=control.action
        )
        
        # 감사 로그 기록
        ip_address = get_client_ip(request) if request else None
        audit_log = AuditLog(
            user_id=current_user.id,
            device_id=device.id,
            action=f"camera_{control.action}",
            resource_type="device_control",
            resource_id=str(device.id),
            ip_address=ip_address
        )
        db.add(audit_log)
        db.commit()
        
        logger.info(
            f"사용자 {current_user.username}가 장비 {device.device_name}의 "
            f"카메라 제어: {control.action}"
        )
        
        return ControlResponse(
            success=True,
            message=f"카메라 {control.action} 명령을 전송했습니다",
            request_id=request_id
        )
    
    except Exception as e:
        logger.error(f"카메라 제어 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="카메라 제어 명령 전송에 실패했습니다"
        )


@router.post("/devices/{device_id}/microphone", response_model=ControlResponse)
async def control_microphone(
    device_id: int,
    control: MicrophoneControlRequest,
    current_user: User = Depends(require_operator),
    db: Session = Depends(get_db),
    request: Request = None
) -> ControlResponse:
    """
    마이크 제어
    
    권한: OPERATOR 이상
    액션: start, pause, stop
    """
    # 장비 확인
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="장비를 찾을 수 없습니다"
        )
    
    if not device.is_online:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="장비가 오프라인 상태입니다"
        )
    
    try:
        # MQTT 명령 전송
        mqtt = get_mqtt_service()
        request_id = mqtt.send_control_command(
            device_id=device.device_id,
            command="microphone",
            action=control.action
        )
        
        # 감사 로그 기록
        ip_address = get_client_ip(request) if request else None
        audit_log = AuditLog(
            user_id=current_user.id,
            device_id=device.id,
            action=f"microphone_{control.action}",
            resource_type="device_control",
            resource_id=str(device.id),
            ip_address=ip_address
        )
        db.add(audit_log)
        db.commit()
        
        logger.info(
            f"사용자 {current_user.username}가 장비 {device.device_name}의 "
            f"마이크 제어: {control.action}"
        )
        
        return ControlResponse(
            success=True,
            message=f"마이크 {control.action} 명령을 전송했습니다",
            request_id=request_id
        )
    
    except Exception as e:
        logger.error(f"마이크 제어 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="마이크 제어 명령 전송에 실패했습니다"
        )


@router.post("/devices/{device_id}/speaker", response_model=ControlResponse)
async def control_speaker(
    device_id: int,
    control: SpeakerControlRequest,
    current_user: User = Depends(require_operator),
    db: Session = Depends(get_db),
    request: Request = None
) -> ControlResponse:
    """
    스피커 제어
    
    권한: OPERATOR 이상
    액션: play (audio_url 필요), stop
    """
    # 장비 확인
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="장비를 찾을 수 없습니다"
        )
    
    if not device.is_online:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="장비가 오프라인 상태입니다"
        )
    
    # play 액션 시 audio_url 필수
    if control.action == "play" and not control.audio_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="play 액션은 audio_url이 필요합니다"
        )
    
    try:
        # MQTT 명령 전송
        mqtt = get_mqtt_service()
        request_id = mqtt.send_control_command(
            device_id=device.device_id,
            command="speaker",
            action=control.action,
            audio_url=control.audio_url
        )
        
        # 감사 로그 기록
        ip_address = get_client_ip(request) if request else None
        audit_log = AuditLog(
            user_id=current_user.id,
            device_id=device.id,
            action=f"speaker_{control.action}",
            resource_type="device_control",
            resource_id=str(device.id),
            ip_address=ip_address
        )
        db.add(audit_log)
        db.commit()
        
        logger.info(
            f"사용자 {current_user.username}가 장비 {device.device_name}의 "
            f"스피커 제어: {control.action}"
        )
        
        return ControlResponse(
            success=True,
            message=f"스피커 {control.action} 명령을 전송했습니다",
            request_id=request_id
        )
    
    except Exception as e:
        logger.error(f"스피커 제어 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="스피커 제어 명령 전송에 실패했습니다"
        )


@router.post("/devices/{device_id}/display", response_model=ControlResponse)
async def control_display(
    device_id: int,
    control: DisplayControlRequest,
    current_user: User = Depends(require_operator),
    db: Session = Depends(get_db),
    request: Request = None
) -> ControlResponse:
    """
    디스플레이 제어
    
    권한: OPERATOR 이상
    액션: show_text (content 필요), show_emoji (emoji_id 필요), clear
    """
    # 장비 확인
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="장비를 찾을 수 없습니다"
        )
    
    if not device.is_online:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="장비가 오프라인 상태입니다"
        )
    
    # 액션별 필수 파라미터 검증
    if control.action == "show_text" and not control.content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="show_text 액션은 content가 필요합니다"
        )
    
    if control.action == "show_emoji" and not control.emoji_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="show_emoji 액션은 emoji_id가 필요합니다"
        )
    
    try:
        # MQTT 명령 전송
        mqtt = get_mqtt_service()
        request_id = mqtt.send_control_command(
            device_id=device.device_id,
            command="display",
            action=control.action,
            content=control.content,
            emoji_id=control.emoji_id
        )
        
        # 감사 로그 기록
        ip_address = get_client_ip(request) if request else None
        audit_log = AuditLog(
            user_id=current_user.id,
            device_id=device.id,
            action=f"display_{control.action}",
            resource_type="device_control",
            resource_id=str(device.id),
            ip_address=ip_address
        )
        db.add(audit_log)
        db.commit()
        
        logger.info(
            f"사용자 {current_user.username}가 장비 {device.device_name}의 "
            f"디스플레이 제어: {control.action}"
        )
        
        return ControlResponse(
            success=True,
            message=f"디스플레이 {control.action} 명령을 전송했습니다",
            request_id=request_id
        )
    
    except Exception as e:
        logger.error(f"디스플레이 제어 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="디스플레이 제어 명령 전송에 실패했습니다"
        )

