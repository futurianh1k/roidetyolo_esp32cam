"""
장비 모니터링 서비스
장비 온라인/오프라인 자동 감지 (Heartbeat 기반)
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Set
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Device
from app.utils.logger import logger


class DeviceMonitor:
    """장비 상태 모니터링 서비스"""

    def __init__(self):
        self.running = False
        self.check_interval = 30  # 30초마다 체크
        self.offline_threshold = 60  # 60초 동안 상태 보고 없으면 오프라인
        self._task = None
        self._recently_offline: Set[int] = set()  # 최근 오프라인 처리된 장비 ID

    async def start(self):
        """모니터링 시작"""
        if self.running:
            logger.warning("DeviceMonitor가 이미 실행 중입니다")
            return

        self.running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info(
            f"DeviceMonitor 시작 (check_interval={self.check_interval}s, offline_threshold={self.offline_threshold}s)"
        )

    async def stop(self):
        """모니터링 중지"""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("DeviceMonitor 중지")

    async def _monitor_loop(self):
        """모니터링 루프"""
        while self.running:
            try:
                await self._check_devices()
            except Exception as e:
                logger.error(f"장비 상태 체크 오류: {e}", exc_info=True)

            await asyncio.sleep(self.check_interval)

    async def _check_devices(self):
        """모든 장비 상태 체크"""
        db: Session = SessionLocal()

        try:
            # 온라인 상태인 장비 조회
            online_devices = db.query(Device).filter(Device.is_online == True).all()

            now = datetime.utcnow()
            threshold_time = now - timedelta(seconds=self.offline_threshold)

            offline_count = 0
            for device in online_devices:
                # last_seen_at이 threshold 이전이면 오프라인 처리
                if device.last_seen_at and device.last_seen_at < threshold_time:
                    device.is_online = False
                    offline_count += 1

                    # 최근에 이미 로깅했으면 건너뛰기
                    if device.id not in self._recently_offline:
                        self._recently_offline.add(device.id)
                        logger.info(
                            f"장비 {device.device_id} ({device.device_name}) 오프라인 처리 "
                            f"(마지막 응답: {device.last_seen_at})"
                        )

                        # WebSocket으로 오프라인 상태 브로드캐스트
                        await self._broadcast_offline_status(device)
                elif device.id in self._recently_offline:
                    # 다시 온라인이 되면 recently_offline에서 제거
                    self._recently_offline.discard(device.id)

            if offline_count > 0:
                db.commit()
                logger.debug(f"오프라인 처리된 장비: {offline_count}개")

        except Exception as e:
            logger.error(f"장비 상태 체크 DB 오류: {e}")
            db.rollback()
        finally:
            db.close()

    async def _broadcast_offline_status(self, device: Device):
        """WebSocket으로 오프라인 상태 브로드캐스트"""
        try:
            from app.services.websocket_service import get_ws_manager

            ws_manager = get_ws_manager()
            await ws_manager.send_device_online_status(device.id, False)
        except Exception as e:
            logger.warning(f"WebSocket 오프라인 브로드캐스트 실패: {e}")

    def mark_device_online(self, device_id: int):
        """장비를 온라인으로 마킹 (recently_offline에서 제거)"""
        self._recently_offline.discard(device_id)


# 전역 인스턴스
device_monitor = DeviceMonitor()


def get_device_monitor() -> DeviceMonitor:
    """DeviceMonitor 인스턴스 가져오기"""
    return device_monitor
