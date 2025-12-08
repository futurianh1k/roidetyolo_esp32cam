"""
WebSocket API 엔드포인트
실시간 통신
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional
import json

from app.dependencies.auth import get_current_user
from app.models import User
from app.services import get_ws_manager
from app.utils.logger import logger
from app.security import decode_token


router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    WebSocket 연결 엔드포인트
    
    인증: JWT 토큰을 쿼리 파라미터로 전달
    예: ws://localhost:8000/ws?token=YOUR_ACCESS_TOKEN
    """
    ws_manager = get_ws_manager()
    user_id = None
    
    try:
        # 토큰 검증
        if not token:
            await websocket.close(code=1008, reason="토큰이 필요합니다")
            return
        
        payload = decode_token(token)
        if not payload:
            await websocket.close(code=1008, reason="유효하지 않은 토큰입니다")
            return
        
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=1008, reason="유효하지 않은 토큰입니다")
            return
        
        # 연결 수락
        await ws_manager.connect(websocket, user_id)
        
        # 연결 성공 메시지
        await websocket.send_json({
            "type": "connected",
            "message": "WebSocket 연결 성공",
            "user_id": user_id
        })
        
        # 메시지 수신 루프
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # 메시지 타입별 처리
                msg_type = message.get("type")
                
                if msg_type == "subscribe_device":
                    # 장비 구독
                    device_id = message.get("device_id")
                    if device_id:
                        ws_manager.subscribe_device(user_id, device_id)
                        await websocket.send_json({
                            "type": "subscribed",
                            "device_id": device_id
                        })
                
                elif msg_type == "unsubscribe_device":
                    # 장비 구독 해제
                    device_id = message.get("device_id")
                    if device_id:
                        ws_manager.unsubscribe_device(user_id, device_id)
                        await websocket.send_json({
                            "type": "unsubscribed",
                            "device_id": device_id
                        })
                
                elif msg_type == "ping":
                    # Ping-Pong
                    await websocket.send_json({"type": "pong"})
            
            except json.JSONDecodeError:
                logger.warning(f"잘못된 JSON 형식: user_id={user_id}")
                await websocket.send_json({
                    "type": "error",
                    "message": "잘못된 메시지 형식입니다"
                })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket 연결 종료: user_id={user_id}")
    
    except Exception as e:
        logger.error(f"WebSocket 오류: {e}")
    
    finally:
        if user_id:
            ws_manager.disconnect(websocket, user_id)

