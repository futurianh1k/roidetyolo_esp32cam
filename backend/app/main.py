"""
FastAPI 메인 애플리케이션
보안 가이드라인 준수
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db
from app.api import auth, users, devices, control, audio, websocket, asr, alarm_history
from app.services import mqtt_service
from app.services.device_monitor import device_monitor
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} 시작")
    logger.info(f"환경: {settings.ENVIRONMENT}")

    # 데이터베이스 초기화
    try:
        init_db()
        logger.info("데이터베이스 초기화 완료")
    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {e}")

    # MQTT 서비스 연결
    try:
        mqtt_service.connect()

        # MQTT 메시지 핸들러 등록
        from app.services.mqtt_handlers import (
            handle_device_status,
            handle_device_response,
        )

        mqtt_service.register_handler("devices/+/status", handle_device_status)
        mqtt_service.register_handler("devices/+/response", handle_device_response)

        logger.info("MQTT 브로커 연결 완료")
    except Exception as e:
        logger.error(f"MQTT 브로커 연결 실패: {e}")
        logger.warning("MQTT 없이 서버를 시작합니다. 장비 제어 기능이 제한됩니다.")

    # 장비 모니터링 서비스 시작
    try:
        await device_monitor.start()
        logger.info("장비 모니터링 서비스 시작 완료")
    except Exception as e:
        logger.error(f"장비 모니터링 서비스 시작 실패: {e}")

    yield

    # 종료
    try:
        await device_monitor.stop()
        logger.info("장비 모니터링 서비스 중지")
    except Exception as e:
        logger.error(f"장비 모니터링 서비스 중지 실패: {e}")

    try:
        mqtt_service.disconnect()
        logger.info("MQTT 브로커 연결 해제")
    except Exception as e:
        logger.error(f"MQTT 연결 해제 실패: {e}")

    logger.info(f"{settings.APP_NAME} 종료")


# FastAPI 앱 생성
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Core S3 장비 관리 시스템 API",
    lifespan=lifespan,
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(devices.router)
app.include_router(control.router)
app.include_router(audio.router)
app.include_router(websocket.router)
app.include_router(asr.router)  # ASR (음성인식) API
app.include_router(alarm_history.router)  # 알람 이력 API


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "mqtt_connected": mqtt_service.connected if mqtt_service else False,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
