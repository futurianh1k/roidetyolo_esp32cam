"""
MQTT 메시지 핸들러
장비로부터 수신한 MQTT 메시지 처리
"""
import json
from datetime import datetime
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Device, DeviceStatus
from app.utils.logger import logger
from app.services.websocket_service import get_ws_manager


def handle_device_status(topic: str, payload: str):
    """
    장비 상태 메시지 처리
    
    Topic: devices/{device_id}/status
    Payload: {
        device_id, battery_level, memory_usage, temperature,
        cpu_usage, camera_status, mic_status, online, ...
    }
    """
    try:
        # JSON 파싱
        data = json.loads(payload)
        device_id = data.get('device_id')
        
        if not device_id:
            logger.error("상태 메시지에 device_id가 없습니다")
            return
        
        # 온라인/오프라인 메시지 확인 (LWT)
        online_status = data.get('online')
        if online_status is not None and not online_status:
            # 오프라인 메시지 (LWT)
            _handle_device_offline(device_id)
            return
        
        # DB 세션 생성
        db: Session = SessionLocal()
        
        try:
            # 장비 조회
            device = db.query(Device).filter(Device.device_id == device_id).first()
            
            if not device:
                logger.warning(f"등록되지 않은 장비: {device_id}")
                return
            
            # 장비 상태 업데이트
            device.is_online = True
            device.last_seen_at = datetime.utcnow()
            
            # 상태 기록 생성
            status = DeviceStatus(
                device_id=device.id,
                battery_level=data.get('battery_level'),
                memory_usage=data.get('memory_usage'),
                storage_usage=data.get('storage_usage'),
                temperature=data.get('temperature'),
                cpu_usage=data.get('cpu_usage'),
                camera_status=data.get('camera_status', 'stopped'),
                mic_status=data.get('mic_status', 'stopped')
            )
            
            db.add(status)
            db.commit()
            db.refresh(status)
            
            logger.info(f"장비 {device_id} 상태 업데이트: 배터리 {data.get('battery_level')}%, 온도 {data.get('temperature')}°C")
            
            # WebSocket으로 실시간 브로드캐스트
            try:
                ws_manager = get_ws_manager()
                asyncio = __import__('asyncio')
                
                # 비동기 함수를 동기적으로 실행
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                if loop.is_running():
                    # 이미 실행 중인 이벤트 루프가 있으면 asyncio.create_task 사용
                    asyncio.create_task(
                        ws_manager.send_device_status(device.id, {
                            'device_id': device.id,
                            'device_name': device.device_name,
                            'is_online': device.is_online,
                            'battery_level': status.battery_level,
                            'memory_usage': status.memory_usage,
                            'temperature': status.temperature,
                            'cpu_usage': status.cpu_usage,
                            'camera_status': status.camera_status,
                            'mic_status': status.mic_status,
                            'recorded_at': status.recorded_at.isoformat(),
                            'timestamp': status.recorded_at.isoformat()
                        })
                    )
                else:
                    loop.run_until_complete(
                        ws_manager.send_device_status(device.id, {
                            'device_id': device.id,
                            'device_name': device.device_name,
                            'is_online': device.is_online,
                            'battery_level': status.battery_level,
                            'memory_usage': status.memory_usage,
                            'temperature': status.temperature,
                            'cpu_usage': status.cpu_usage,
                            'camera_status': status.camera_status,
                            'mic_status': status.mic_status,
                            'recorded_at': status.recorded_at.isoformat(),
                            'timestamp': status.recorded_at.isoformat()
                        })
                    )
            except Exception as ws_error:
                logger.warning(f"WebSocket 브로드캐스트 실패: {ws_error}")
        
        finally:
            db.close()
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 실패: {e}")
    except Exception as e:
        logger.error(f"상태 메시지 처리 오류: {e}", exc_info=True)


def _handle_device_offline(device_id: str):
    """
    장비 오프라인 처리 (LWT)
    """
    db: Session = SessionLocal()
    
    try:
        device = db.query(Device).filter(Device.device_id == device_id).first()
        
        if device:
            device.is_online = False
            device.last_seen_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"장비 {device_id} 오프라인 처리됨")
            
            # WebSocket 브로드캐스트
            try:
                ws_manager = get_ws_manager()
                asyncio = __import__('asyncio')
                
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                if loop.is_running():
                    asyncio.create_task(
                        ws_manager.send_device_online_status(device.id, False)
                    )
                else:
                    loop.run_until_complete(
                        ws_manager.send_device_online_status(device.id, False)
                    )
            except Exception as e:
                logger.warning(f"WebSocket 브로드캐스트 실패: {e}")
    
    finally:
        db.close()


def handle_device_response(topic: str, payload: str):
    """
    장비 응답 메시지 처리
    
    Topic: devices/{device_id}/response
    Payload: {
        request_id, command, action, success, message
    }
    """
    try:
        # JSON 파싱
        data = json.loads(payload)
        request_id = data.get('request_id')
        command = data.get('command')
        action = data.get('action')
        success = data.get('success')
        message = data.get('message')
        
        logger.info(
            f"제어 응답 수신 - Request: {request_id}, "
            f"Command: {command}/{action}, "
            f"Success: {success}, "
            f"Message: {message}"
        )
        
        # TODO: 응답 대기 중인 요청이 있다면 처리
        # (현재는 로깅만 수행)
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 실패: {e}")
    except Exception as e:
        logger.error(f"응답 메시지 처리 오류: {e}", exc_info=True)
