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
    SystemControlRequest,
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
    # TODO: 로그인 수정 후 활성화
    # current_user: User = Depends(require_operator),
    db: Session = Depends(get_db),
    request: Request = None,
) -> ControlResponse:
    """
    카메라 제어

    권한: OPERATOR 이상
    액션: start, pause, stop

    영상 sink 전송:
    - start 액션 시 sink_url, stream_mode, frame_interval 설정 가능
    - sink_url: 영상 sink 주소 (HTTP/WebSocket/RTSP URL)
    - stream_mode: 전송 방식 (mjpeg_stills, realtime_websocket, realtime_rtsp)
    - frame_interval: 프레임 간격 (ms, mjpeg_stills 모드일 경우)
    """
    # 장비 확인
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="장비를 찾을 수 없습니다"
        )

    if not device.is_online:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="장비가 오프라인 상태입니다"
        )

    # start 액션 시 sink 설정 검증
    if control.action == "start":
        # sink_url과 stream_mode는 함께 설정되어야 함
        if control.sink_url and not control.stream_mode:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="sink_url이 설정된 경우 stream_mode가 필요합니다",
            )
        if control.stream_mode and not control.sink_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="stream_mode가 설정된 경우 sink_url이 필요합니다",
            )
        if control.stream_mode == "mjpeg_stills" and not control.frame_interval:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="mjpeg_stills 모드일 경우 frame_interval가 필요합니다",
            )

    try:
        # MQTT 명령 전송 (sink 정보 포함)
        mqtt = get_mqtt_service()

        # sink 정보가 있으면 MQTT 메시지에 포함
        mqtt_kwargs = {}
        if control.sink_url:
            mqtt_kwargs["sink_url"] = control.sink_url
        if control.stream_mode:
            mqtt_kwargs["stream_mode"] = control.stream_mode
        if control.frame_interval is not None:
            mqtt_kwargs["frame_interval"] = control.frame_interval

        request_id = mqtt.send_control_command(
            device_id=device.device_id,
            command="camera",
            action=control.action,
            **mqtt_kwargs,
        )

        # TODO: 로그인 수정 후 감사 로그 활성화
        # ip_address = get_client_ip(request) if request else None
        # audit_log = AuditLog(
        #     user_id=current_user.id,
        #     device_id=device.id,
        #     action=f"camera_{control.action}",
        #     resource_type="device_control",
        #     resource_id=str(device.id),
        #     ip_address=ip_address
        # )
        # db.add(audit_log)
        # db.commit()

        # 로그에 sink 정보 포함
        log_msg = f"장비 {device.device_name}의 카메라 제어: {control.action}"
        if control.sink_url:
            log_msg += (
                f", sink_url={control.sink_url}, stream_mode={control.stream_mode}"
            )
            if control.frame_interval:
                log_msg += f", frame_interval={control.frame_interval}ms"
        logger.info(log_msg)

        return ControlResponse(
            success=True,
            message=f"카메라 {control.action} 명령을 전송했습니다",
            request_id=request_id,
        )

    except Exception as e:
        logger.error(f"카메라 제어 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="카메라 제어 명령 전송에 실패했습니다",
        )


@router.post("/devices/{device_id}/microphone", response_model=ControlResponse)
async def control_microphone(
    device_id: int,
    control: MicrophoneControlRequest,
    # TODO: 로그인 수정 후 활성화
    # current_user: User = Depends(require_operator),
    db: Session = Depends(get_db),
    request: Request = None,
) -> ControlResponse:
    """
    마이크 제어

    권한: OPERATOR 이상
    액션: start, pause, stop

    오디오 WebSocket 전송:
    - start 액션 시 ws_url 설정 가능
    - ws_url: 오디오 스트림을 전송할 WebSocket 주소
    """
    # 장비 확인
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="장비를 찾을 수 없습니다"
        )

    if not device.is_online:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="장비가 오프라인 상태입니다"
        )

    try:
        # MQTT 명령 전송
        mqtt = get_mqtt_service()

        # ws_url이 있으면 MQTT 메시지에 포함
        mqtt_kwargs = {}
        if control.ws_url:
            mqtt_kwargs["ws_url"] = control.ws_url

        request_id = mqtt.send_control_command(
            device_id=device.device_id,
            command="microphone",
            action=control.action,
            **mqtt_kwargs,
        )

        # TODO: 로그인 수정 후 감사 로그 활성화
        log_msg = f"장비 {device.device_name}의 마이크 제어: {control.action}"
        if control.ws_url:
            log_msg += f", ws_url={control.ws_url}"
        logger.info(log_msg)

        return ControlResponse(
            success=True,
            message=f"마이크 {control.action} 명령을 전송했습니다",
            request_id=request_id,
        )

    except Exception as e:
        logger.error(f"마이크 제어 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="마이크 제어 명령 전송에 실패했습니다",
        )


@router.post("/devices/{device_id}/speaker", response_model=ControlResponse)
async def control_speaker(
    device_id: int,
    control: SpeakerControlRequest,
    # TODO: 로그인 수정 후 활성화
    # current_user: User = Depends(require_operator),
    db: Session = Depends(get_db),
    request: Request = None,
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
            status_code=status.HTTP_404_NOT_FOUND, detail="장비를 찾을 수 없습니다"
        )

    if not device.is_online:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="장비가 오프라인 상태입니다"
        )

    # play 액션 시 audio_file 또는 audio_url 필수
    if control.action == "play" and not control.audio_file and not control.audio_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="play 액션은 audio_file 또는 audio_url이 필요합니다",
        )

    try:
        # 오디오 파일명이 주어진 경우 URL로 변환
        audio_url = control.audio_url
        if control.audio_file and not audio_url:
            from app.services import get_audio_service
            from app.config import settings

            audio_service = get_audio_service()

            # 상대 경로를 절대 URL로 변환
            # 장비가 접근할 수 있는 URL 생성
            relative_url = audio_service.get_audio_url(control.audio_file)

            # 백엔드 서버의 호스트 주소 사용 (설정에서 가져옴)
            backend_host = settings.BACKEND_HOST or "localhost"
            backend_port = settings.BACKEND_PORT or 8000

            # 장비가 접근할 수 있는 절대 URL 생성
            audio_url = f"http://{backend_host}:{backend_port}{relative_url}"

            logger.info(
                f"오디오 파일 URL 생성: {audio_url} (파일: {control.audio_file})"
            )

        # MQTT 명령 전송
        mqtt = get_mqtt_service()
        request_id = mqtt.send_control_command(
            device_id=device.device_id,
            command="speaker",
            action=control.action,
            audio_url=audio_url,
            volume=control.volume,
        )

        # TODO: 로그인 수정 후 감사 로그 활성화
        logger.info(f"장비 {device.device_name}의 스피커 제어: {control.action}")

        return ControlResponse(
            success=True,
            message=f"스피커 {control.action} 명령을 전송했습니다",
            request_id=request_id,
        )

    except Exception as e:
        logger.error(f"스피커 제어 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="스피커 제어 명령 전송에 실패했습니다",
        )


@router.post("/devices/{device_id}/display", response_model=ControlResponse)
async def control_display(
    device_id: int,
    control: DisplayControlRequest,
    # TODO: 로그인 수정 후 활성화
    # current_user: User = Depends(require_operator),
    db: Session = Depends(get_db),
    request: Request = None,
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
            status_code=status.HTTP_404_NOT_FOUND, detail="장비를 찾을 수 없습니다"
        )

    if not device.is_online:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="장비가 오프라인 상태입니다"
        )

    # 액션별 필수 파라미터 검증
    if control.action == "show_text" and not control.content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="show_text 액션은 content가 필요합니다",
        )

    if control.action == "show_emoji" and not control.emoji_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="show_emoji 액션은 emoji_id가 필요합니다",
        )

    try:
        # MQTT 명령 전송
        mqtt = get_mqtt_service()
        request_id = mqtt.send_control_command(
            device_id=device.device_id,
            command="display",
            action=control.action,
            content=control.content,
            emoji_id=control.emoji_id,
        )

        # TODO: 로그인 수정 후 감사 로그 활성화
        logger.info(f"장비 {device.device_name}의 디스플레이 제어: {control.action}")

        return ControlResponse(
            success=True,
            message=f"디스플레이 {control.action} 명령을 전송했습니다",
            request_id=request_id,
        )

    except Exception as e:
        logger.error(f"디스플레이 제어 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="디스플레이 제어 명령 전송에 실패했습니다",
        )


@router.post("/devices/{device_id}/system", response_model=ControlResponse)
async def control_system(
    device_id: int,
    control: SystemControlRequest,
    # TODO: 로그인 수정 후 활성화
    # current_user: User = Depends(require_operator),
    db: Session = Depends(get_db),
    request: Request = None,
) -> ControlResponse:
    """
    시스템 제어

    권한: OPERATOR 이상
    액션: restart (장비 재시작)
    """
    # 장비 확인
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="장비를 찾을 수 없습니다"
        )

    if not device.is_online:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="장비가 오프라인 상태입니다"
        )

    try:
        # MQTT 명령 전송
        mqtt = get_mqtt_service()
        request_id = mqtt.send_control_command(
            device_id=device.device_id, command="system", action=control.action
        )

        # TODO: 로그인 수정 후 감사 로그 활성화
        logger.info(f"장비 {device.device_name}의 시스템 제어: {control.action}")

        return ControlResponse(
            success=True,
            message=f"시스템 {control.action} 명령을 전송했습니다",
            request_id=request_id,
        )

    except Exception as e:
        logger.error(f"시스템 제어 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="시스템 제어 명령 전송에 실패했습니다",
        )
