"""
WebSocket 서비스
실시간 장비 상태 업데이트
"""
from typing import Dict, Set
from fastapi import WebSocket
import json
import asyncio

from app.utils.logger import logger


class WebSocketManager:
    """WebSocket 연결 관리자"""
    
    def __init__(self):
        # 활성 연결: {user_id: {websocket, websocket, ...}}
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        
        # 장비별 구독: {device_id: {user_id, user_id, ...}}
        self.device_subscriptions: Dict[int, Set[int]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """WebSocket 연결 추가"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        logger.info(f"WebSocket 연결: user_id={user_id}")
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        """WebSocket 연결 제거"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        # 장비 구독에서도 제거
        for device_id in list(self.device_subscriptions.keys()):
            if user_id in self.device_subscriptions[device_id]:
                self.device_subscriptions[device_id].discard(user_id)
                
                if not self.device_subscriptions[device_id]:
                    del self.device_subscriptions[device_id]
        
        logger.info(f"WebSocket 연결 해제: user_id={user_id}")
    
    def subscribe_device(self, user_id: int, device_id: int):
        """장비 상태 구독"""
        if device_id not in self.device_subscriptions:
            self.device_subscriptions[device_id] = set()
        
        self.device_subscriptions[device_id].add(user_id)
        logger.info(f"장비 구독: user_id={user_id}, device_id={device_id}")
    
    def unsubscribe_device(self, user_id: int, device_id: int):
        """장비 상태 구독 해제"""
        if device_id in self.device_subscriptions:
            self.device_subscriptions[device_id].discard(user_id)
            
            if not self.device_subscriptions[device_id]:
                del self.device_subscriptions[device_id]
        
        logger.info(f"장비 구독 해제: user_id={user_id}, device_id={device_id}")
    
    async def send_personal_message(self, message: dict, user_id: int):
        """특정 사용자에게 메시지 전송"""
        if user_id not in self.active_connections:
            return
        
        message_str = json.dumps(message)
        
        # 해당 사용자의 모든 연결에 전송
        disconnected = []
        for websocket in self.active_connections[user_id]:
            try:
                await websocket.send_text(message_str)
            except Exception as e:
                logger.error(f"메시지 전송 실패: {e}")
                disconnected.append(websocket)
        
        # 실패한 연결 제거
        for websocket in disconnected:
            self.disconnect(websocket, user_id)
    
    async def broadcast_to_subscribers(self, device_id: int, message: dict):
        """장비를 구독 중인 사용자들에게 브로드캐스트"""
        if device_id not in self.device_subscriptions:
            return
        
        message_str = json.dumps(message)
        
        for user_id in self.device_subscriptions[device_id]:
            if user_id not in self.active_connections:
                continue
            
            disconnected = []
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_text(message_str)
                except Exception as e:
                    logger.error(f"브로드캐스트 실패: {e}")
                    disconnected.append(websocket)
            
            # 실패한 연결 제거
            for websocket in disconnected:
                self.disconnect(websocket, user_id)
    
    async def broadcast_all(self, message: dict):
        """모든 연결된 클라이언트에게 브로드캐스트"""
        message_str = json.dumps(message)
        
        for user_id, connections in list(self.active_connections.items()):
            disconnected = []
            for websocket in connections:
                try:
                    await websocket.send_text(message_str)
                except Exception as e:
                    logger.error(f"브로드캐스트 실패: {e}")
                    disconnected.append(websocket)
            
            # 실패한 연결 제거
            for websocket in disconnected:
                self.disconnect(websocket, user_id)
    
    async def send_device_status(self, device_id: int, status: dict):
        """장비 상태 업데이트 전송"""
        message = {
            "type": "device_status",
            "device_id": device_id,
            "status": status,
            "timestamp": status.get("timestamp")
        }
        
        await self.broadcast_to_subscribers(device_id, message)
    
    async def send_device_online_status(self, device_id: int, is_online: bool):
        """장비 온라인 상태 업데이트"""
        message = {
            "type": "device_online",
            "device_id": device_id,
            "is_online": is_online
        }
        
        await self.broadcast_to_subscribers(device_id, message)
    
    async def send_control_response(self, user_id: int, response: dict):
        """제어 명령 응답 전송"""
        message = {
            "type": "control_response",
            "response": response
        }
        
        await self.send_personal_message(message, user_id)


# 전역 WebSocket 매니저 인스턴스
ws_manager = WebSocketManager()


def get_ws_manager() -> WebSocketManager:
    """WebSocket 매니저 인스턴스 가져오기"""
    return ws_manager

