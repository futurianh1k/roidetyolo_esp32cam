"""
FastAPI 메인 애플리케이션
보안 가이드라인 준수
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db
from app.api import auth, users, devices, control, audio, websocket
from app.services import mqtt_service
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
        logger.info("MQTT 브로커 연결 완료")
    except Exception as e:
        logger.error(f"MQTT 브로커 연결 실패: {e}")
        logger.warning("MQTT 없이 서버를 시작합니다. 장비 제어 기능이 제한됩니다.")
    
    yield
    
    # 종료
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
    lifespan=lifespan
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


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "mqtt_connected": mqtt_service.connected if mqtt_service else False
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
