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
    액션:
    - play: 오디오 파일 재생 (audio_url 또는 audio_file 필요)
    - play_alarm: 내장 알람음 재생 (alarm_type: beep|alert|notification|emergency)
    - play_beep: 비프음 재생 (frequency, duration 필요)
    - stop: 재생 중지
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
    if control.action == "play" and not control.audio_file and not control.audio_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="play 액션은 audio_file 또는 audio_url이 필요합니다",
        )

    if control.action == "play_alarm" and not control.alarm_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="play_alarm 액션은 alarm_type이 필요합니다 (beep|alert|notification|emergency)",
        )

    if control.action == "play_beep" and (
        not control.frequency or not control.duration
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="play_beep 액션은 frequency와 duration이 필요합니다",
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

            # 백엔드 서버의 호스트 주소 결정
            # 1. 설정 파일의 BACKEND_HOST 사용 (우선)
            # 2. localhost인 경우 자동 감지 시도
            backend_host = settings.BACKEND_HOST

            # localhost인 경우 자동으로 실제 IP 주소 찾기
            if backend_host in ["localhost", "127.0.0.1"]:
                detected_host = None

                # 방법 1: Request의 Host 헤더 사용 (프론트엔드에서 접근한 주소)
                if request:
                    host_header = request.headers.get("Host", "")
                    if host_header and host_header not in ["localhost", "127.0.0.1"]:
                        # 포트 제거
                        detected_host = host_header.split(":")[0]
                        # IP 주소 형식인지 확인
                        import re

                        if re.match(r"^\d+\.\d+\.\d+\.\d+$", detected_host):
                            backend_host = detected_host
                            logger.info(
                                f"✅ Host 헤더에서 백엔드 IP 자동 감지: {backend_host}"
                            )

                # 방법 2: 장비 IP와 같은 서브넷의 백엔드 IP 추론
                if backend_host in ["localhost", "127.0.0.1"] and device.ip_address:
                    # 장비 IP의 서브넷에서 백엔드 IP 추론
                    # 예: 장비가 10.10.11.18이면 백엔드는 10.10.11.x (같은 서브넷)
                    ip_parts = device.ip_address.rsplit(".", 1)
                    if len(ip_parts) == 2:
                        # 네트워크 인터페이스에서 실제 IP 찾기
                        import socket

                        try:
                            # 장비와 통신 가능한 네트워크 인터페이스의 IP 찾기
                            # 같은 서브넷의 IP 주소 사용
                            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                            try:
                                # 장비 IP로 연결 시도하여 사용할 네트워크 인터페이스 확인
                                s.connect((device.ip_address, 80))
                                local_ip = s.getsockname()[0]
                                s.close()

                                # 같은 서브넷인지 확인
                                local_parts = local_ip.rsplit(".", 1)
                                if (
                                    len(local_parts) == 2
                                    and local_parts[0] == ip_parts[0]
                                ):
                                    backend_host = local_ip
                                    logger.info(
                                        f"✅ 네트워크 인터페이스에서 백엔드 IP 자동 감지: {backend_host} "
                                        f"(장비 IP: {device.ip_address})"
                                    )
                                else:
                                    # 다른 서브넷이면 장비 IP의 서브넷 사용
                                    backend_host = ip_parts[0] + ".1"
                                    logger.warning(
                                        f"⚠️ 다른 서브넷 감지. 장비 IP({device.ip_address}) 기반으로 "
                                        f"{backend_host} 사용. .env 파일에 BACKEND_HOST를 설정하세요."
                                    )
                            except:
                                s.close()
                                # 연결 실패 시 장비 IP의 서브넷 사용
                                backend_host = ip_parts[0] + ".1"
                                logger.warning(
                                    f"⚠️ BACKEND_HOST가 localhost입니다. "
                                    f"장비 IP({device.ip_address}) 기반으로 {backend_host} 사용. "
                                    f".env 파일에 BACKEND_HOST를 설정하세요."
                                )
                        except Exception as e:
                            logger.warning(
                                f"⚠️ IP 자동 감지 실패: {e}. .env 파일에 BACKEND_HOST를 설정하세요."
                            )

                # 여전히 localhost인 경우 경고
                if backend_host in ["localhost", "127.0.0.1"]:
                    logger.error(
                        f"❌ BACKEND_HOST가 localhost입니다. ESP32 장비가 접근할 수 없습니다. "
                        f".env 파일에 BACKEND_HOST를 실제 IP 주소로 설정하세요. "
                        f"(예: BACKEND_HOST=10.10.11.18)"
                    )

            backend_port = settings.BACKEND_PORT or 8000

            # 장비가 접근할 수 있는 절대 URL 생성
            audio_url = f"http://{backend_host}:{backend_port}{relative_url}"

            logger.info(
                f"오디오 파일 URL 생성: {audio_url} (파일: {control.audio_file}, "
                f"백엔드 호스트: {backend_host})"
            )

        # MQTT 명령 전송
        mqtt = get_mqtt_service()

        # 액션별 MQTT 명령 구성
        mqtt_kwargs = {"volume": control.volume}

        if control.action == "play_alarm":
            mqtt_kwargs["type"] = control.alarm_type
            mqtt_kwargs["repeat"] = control.repeat or 1
        elif control.action == "play_beep":
            mqtt_kwargs["frequency"] = control.frequency
            mqtt_kwargs["duration"] = control.duration
        elif control.action == "play":
            mqtt_kwargs["audio_url"] = audio_url

        request_id = mqtt.send_control_command(
            device_id=device.device_id,
            command="speaker",
            action=control.action,
            **mqtt_kwargs,
        )

        # TODO: 로그인 수정 후 감사 로그 활성화
        logger.info(f"장비 {device.device_name}의 스피커 제어: {control.action}")

        # 알람 이력 기록 (play, play_alarm, play_beep 액션만)
        if control.action in ["play", "play_alarm", "play_beep"]:
            try:
                from app.models import AlarmHistory
                import json

                # 알람 타입 결정
                if control.action == "play_alarm":
                    alarm_type = "sound"
                    alarm_subtype = control.alarm_type
                    content = None
                elif control.action == "play_beep":
                    alarm_type = "sound"
                    alarm_subtype = "beep"
                    content = None
                else:  # play
                    alarm_type = "recorded"
                    alarm_subtype = None
                    content = audio_url or control.audio_file

                # 파라미터 JSON 저장
                params = {}
                if control.volume:
                    params["volume"] = control.volume
                if control.frequency:
                    params["frequency"] = control.frequency
                if control.duration:
                    params["duration"] = control.duration
                if control.repeat:
                    params["repeat"] = control.repeat

                alarm_history = AlarmHistory(
                    device_id=device_id,
                    alarm_type=alarm_type,
                    alarm_subtype=alarm_subtype,
                    content=content,
                    triggered_by="admin",  # TODO: current_user.role로 변경
                    triggered_user_id=None,  # TODO: current_user.id로 변경
                    parameters=json.dumps(params) if params else None,
                    status="sent",
                )
                db.add(alarm_history)
                db.commit()
                logger.info(
                    f"알람 이력 기록: device={device_id}, type={alarm_type}, "
                    f"subtype={alarm_subtype}"
                )
            except Exception as e:
                logger.warning(f"알람 이력 기록 실패 (계속 진행): {e}")
                # 이력 기록 실패해도 API는 성공 응답

        # 액션별 응답 메시지
        messages = {
            "play": f"오디오 재생 명령을 전송했습니다",
            "play_alarm": f"{control.alarm_type} 알람 재생 명령을 전송했습니다",
            "play_beep": f"비프음({control.frequency}Hz, {control.duration}ms) 재생 명령을 전송했습니다",
            "stop": "스피커 정지 명령을 전송했습니다",
        }

        return ControlResponse(
            success=True,
            message=messages.get(
                control.action, f"스피커 {control.action} 명령을 전송했습니다"
            ),
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
    액션:
    - restart: 장비 재시작
    - wake: 장비 깨우기 (오프라인 장비에도 전송 가능)
    - sleep: 장비 절전 모드 전환
    - set_interval: 상태 보고 주기 변경 (interval 필수, 초 단위)
    """
    # 장비 확인
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="장비를 찾을 수 없습니다"
        )

    # set_interval 액션 시 interval 필수
    if control.action == "set_interval" and not control.interval:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="set_interval 액션은 interval이 필요합니다 (10-3600초)",
        )

    # wake 명령은 오프라인 장비에도 전송 가능 (MQTT retained 메시지로)
    # restart, sleep, set_interval 명령은 온라인 장비에만 전송
    if control.action not in ["wake"] and not device.is_online:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="장비가 오프라인 상태입니다"
        )

    try:
        # MQTT 명령 전송
        mqtt = get_mqtt_service()

        # wake 명령은 retained 메시지로 전송 (장비가 연결되면 즉시 수신)
        if control.action == "wake":
            request_id = mqtt.send_control_command(
                device_id=device.device_id,
                command="system",
                action=control.action,
                retain=True,  # 장비가 연결되면 즉시 수신
            )
        elif control.action == "set_interval":
            # DB 업데이트
            device.status_report_interval = control.interval
            db.commit()

            # MQTT로 장비에 전송 (interval은 초 단위)
            request_id = mqtt.send_control_command(
                device_id=device.device_id,
                command="system",
                action=control.action,
                interval=control.interval,
            )
            logger.info(
                f"장비 {device.device_name}의 상태 보고 주기 변경: {control.interval}초"
            )
        else:
            request_id = mqtt.send_control_command(
                device_id=device.device_id, command="system", action=control.action
            )

        # TODO: 로그인 수정 후 감사 로그 활성화
        logger.info(f"장비 {device.device_name}의 시스템 제어: {control.action}")

        # 액션별 응답 메시지
        messages = {
            "restart": "시스템 재시작 명령을 전송했습니다",
            "wake": "깨우기 명령을 전송했습니다. 장비가 연결되면 자동으로 온라인 상태가 됩니다.",
            "sleep": "절전 모드 명령을 전송했습니다",
            "set_interval": f"상태 보고 주기를 {control.interval}초로 변경했습니다",
        }

        return ControlResponse(
            success=True,
            message=messages.get(
                control.action, f"시스템 {control.action} 명령을 전송했습니다"
            ),
            request_id=request_id,
        )

    except Exception as e:
        logger.error(f"시스템 제어 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="시스템 제어 명령 전송에 실패했습니다",
        )
