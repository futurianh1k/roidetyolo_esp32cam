"""
MQTT 서비스
장비와의 양방향 통신 관리
참고: paho-mqtt 라이브러리 사용
"""

import json
import asyncio
from typing import Optional, Dict, Callable
from datetime import datetime
import paho.mqtt.client as mqtt
import uuid

from app.config import settings
from app.utils.logger import logger


class MQTTService:
    """MQTT 클라이언트 서비스"""

    def __init__(self):
        self.client: Optional[mqtt.Client] = None
        self.connected: bool = False
        self.message_handlers: Dict[str, Callable] = {}

    def connect(self) -> None:
        """MQTT 브로커에 연결"""
        try:
            # 클라이언트 생성
            client_id = f"backend_{uuid.uuid4().hex[:8]}"
            self.client = mqtt.Client(client_id=client_id)

            # 인증 설정
            if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
                self.client.username_pw_set(
                    settings.MQTT_USERNAME, settings.MQTT_PASSWORD
                )

            # TLS 설정
            if settings.MQTT_USE_TLS:
                self.client.tls_set()

            # 콜백 설정
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message

            # 연결
            logger.info(
                f"MQTT 브로커 연결 중: {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}"
            )
            self.client.connect(
                settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, keepalive=60
            )

            # 백그라운드 루프 시작
            self.client.loop_start()

        except Exception as e:
            logger.error(f"MQTT 연결 실패: {e}")
            raise

    def disconnect(self) -> None:
        """MQTT 브로커 연결 해제"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            logger.info("MQTT 연결 해제")

    def _on_connect(self, client, userdata, flags, rc):
        """연결 성공 콜백"""
        if rc == 0:
            self.connected = True
            logger.info("MQTT 브로커 연결 성공")

            # 모든 장비의 응답 토픽 구독
            self.subscribe("devices/+/response")
            self.subscribe("devices/+/status")
        else:
            logger.error(f"MQTT 연결 실패: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """연결 해제 콜백"""
        self.connected = False
        if rc != 0:
            logger.warning(f"MQTT 연결 끊김: {rc}")
        else:
            logger.info("MQTT 정상 연결 해제")

    def _on_message(self, client, userdata, msg):
        """메시지 수신 콜백"""
        try:
            topic = msg.topic
            payload = msg.payload.decode("utf-8")

            logger.info(f"MQTT 메시지 수신: {topic}")

            # 핸들러 실행
            for pattern, handler in self.message_handlers.items():
                if self._match_topic(topic, pattern):
                    handler(topic, payload)

        except Exception as e:
            logger.error(f"MQTT 메시지 처리 오류: {e}")

    def _match_topic(self, topic: str, pattern: str) -> bool:
        """토픽 매칭 (와일드카드 지원)"""
        topic_parts = topic.split("/")
        pattern_parts = pattern.split("/")

        if len(topic_parts) != len(pattern_parts):
            return False

        for t, p in zip(topic_parts, pattern_parts):
            if p == "+":  # 단일 레벨 와일드카드
                continue
            elif p == "#":  # 다중 레벨 와일드카드
                return True
            elif t != p:
                return False

        return True

    def subscribe(self, topic: str) -> None:
        """토픽 구독"""
        if self.client and self.connected:
            self.client.subscribe(topic)
            logger.info(f"MQTT 토픽 구독: {topic}")

    def unsubscribe(self, topic: str) -> None:
        """토픽 구독 해제"""
        if self.client and self.connected:
            self.client.unsubscribe(topic)
            logger.info(f"MQTT 토픽 구독 해제: {topic}")

    def publish(self, topic: str, payload: dict, qos: int = 1) -> bool:
        """메시지 발행"""
        if not self.client or not self.connected:
            logger.error("MQTT 연결되지 않음")
            return False

        try:
            # JSON으로 변환
            message = json.dumps(payload)

            # 발행
            result = self.client.publish(topic, message, qos=qos)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"MQTT 메시지 발행: {topic}")
                return True
            else:
                logger.error(f"MQTT 메시지 발행 실패: {result.rc}")
                return False

        except Exception as e:
            logger.error(f"MQTT 메시지 발행 오류: {e}")
            return False

    def register_handler(self, topic_pattern: str, handler: Callable) -> None:
        """메시지 핸들러 등록"""
        self.message_handlers[topic_pattern] = handler
        logger.info(f"MQTT 핸들러 등록: {topic_pattern}")

    def unregister_handler(self, topic_pattern: str) -> None:
        """메시지 핸들러 해제"""
        if topic_pattern in self.message_handlers:
            del self.message_handlers[topic_pattern]
            logger.info(f"MQTT 핸들러 해제: {topic_pattern}")

    def send_control_command(
        self, device_id: str, command: str, action: str, **kwargs
    ) -> str:
        """
        장비 제어 명령 전송

        Args:
            device_id: 장비 ID
            command: 명령 타입 (camera, microphone, speaker, display)
            action: 액션
            **kwargs: 추가 파라미터

        Returns:
            str: 요청 ID
        """
        request_id = uuid.uuid4().hex

        payload = {
            "command": command,
            "action": action,
            "timestamp": int(datetime.utcnow().timestamp()),
            "request_id": request_id,
            **kwargs,
        }

        topic = f"devices/{device_id}/control/{command}"

        if self.publish(topic, payload):
            return request_id
        else:
            raise Exception("MQTT 메시지 전송 실패")


# 전역 MQTT 서비스 인스턴스
mqtt_service = MQTTService()


def get_mqtt_service() -> MQTTService:
    """MQTT 서비스 인스턴스 가져오기"""
    return mqtt_service
