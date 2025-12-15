"""
카메라 스트림 프록시 API

CORS 문제를 해결하기 위해 백엔드에서 ESP32-CAM 스트림을 프록시합니다.
프론트엔드는 같은 도메인의 백엔드 API를 호출하여 CORS 제한을 우회합니다.

참고자료:
- FastAPI StreamingResponse: https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse
- MJPEG Streaming: https://en.wikipedia.org/wiki/Motion_JPEG
"""

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
import httpx
import asyncio
from typing import AsyncGenerator

from app.database import get_db
from app.models import Device
from app.utils.logger import logger
from fastapi import Depends

router = APIRouter(prefix="/stream", tags=["stream"])

# 스트림 프록시 설정
STREAM_TIMEOUT = 30.0  # 연결 타임아웃 (초)
CHUNK_SIZE = 1024 * 8  # 8KB 청크 (더 작게)


@router.get("/test/{device_id}")
async def test_stream_connection(
    device_id: int,
    db: Session = Depends(get_db),
):
    """
    장비 스트림 연결을 테스트합니다. (디버깅용)
    """
    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        return JSONResponse(
            status_code=404,
            content={"error": "장비를 찾을 수 없습니다", "device_id": device_id},
        )

    # 스트림 URL 결정 (HTTP 스트림만 지원, RTSP는 무시)
    stream_url = None

    # rtsp_url이 http:// 로 시작하면 사용
    if device.rtsp_url and device.rtsp_url.startswith("http"):
        stream_url = device.rtsp_url

    # HTTP URL이 없으면 IP 주소로 생성
    if not stream_url and device.ip_address:
        ip = device.ip_address
        if ":" in ip and "/" in ip:
            stream_url = f"http://{ip}"
        elif ":" in ip:
            stream_url = f"http://{ip}/stream"
        else:
            stream_url = f"http://{ip}:81/stream"

    result = {
        "device_id": device_id,
        "device_name": device.device_name,
        "ip_address": device.ip_address,
        "rtsp_url": device.rtsp_url,
        "rtsp_url_note": (
            "RTSP URLs are not supported for HTTP proxy"
            if device.rtsp_url and device.rtsp_url.startswith("rtsp")
            else None
        ),
        "is_online": device.is_online,
        "computed_stream_url": stream_url,
    }

    if not stream_url:
        result["error"] = "스트림 URL을 결정할 수 없습니다"
        return JSONResponse(status_code=400, content=result)

    # 연결 테스트
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
            response = await client.get(stream_url, follow_redirects=True)
            result["connection_status"] = response.status_code
            result["content_type"] = response.headers.get("content-type", "unknown")
            result["success"] = response.status_code == 200

            # 첫 몇 바이트 확인
            if response.status_code == 200:
                result["first_bytes_hex"] = (
                    response.content[:50].hex() if response.content else "empty"
                )

    except httpx.TimeoutException:
        result["error"] = "연결 타임아웃"
        result["success"] = False
    except httpx.ConnectError as e:
        result["error"] = f"연결 실패: {str(e)}"
        result["success"] = False
    except Exception as e:
        result["error"] = f"예외 발생: {str(e)}"
        result["success"] = False

    return JSONResponse(content=result)


async def stream_proxy(stream_url: str) -> AsyncGenerator[bytes, None]:
    """
    ESP32-CAM MJPEG 스트림을 프록시합니다.

    Args:
        stream_url: ESP32-CAM 스트림 URL (예: http://camera-ip:81/stream)

    Yields:
        스트림 데이터 청크
    """
    logger.info(f"Starting stream proxy: {stream_url}")

    # 타임아웃 설정: connect=5초, read=None(무제한)
    timeout = httpx.Timeout(connect=5.0, read=None, write=None, pool=None)

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            async with client.stream(
                "GET", stream_url, follow_redirects=True
            ) as response:
                logger.info(
                    f"Stream response: status={response.status_code}, headers={dict(response.headers)}"
                )

                if response.status_code != 200:
                    logger.error(
                        f"Stream error: {response.status_code} from {stream_url}"
                    )
                    return

                chunk_count = 0
                async for chunk in response.aiter_bytes(CHUNK_SIZE):
                    chunk_count += 1
                    if chunk_count <= 3:
                        logger.debug(f"Stream chunk #{chunk_count}: {len(chunk)} bytes")
                    yield chunk

        except httpx.TimeoutException as e:
            logger.error(f"Stream timeout: {stream_url} - {e}")
        except httpx.ConnectError as e:
            logger.error(f"Stream connect error: {stream_url} - {e}")
        except Exception as e:
            logger.error(f"Stream error: {stream_url} - {type(e).__name__}: {e}")


@router.get("/proxy")
async def proxy_stream(
    url: str = Query(..., description="프록시할 스트림 URL"),
):
    """
    외부 스트림 URL을 프록시합니다.

    CORS 문제를 해결하기 위해 백엔드에서 스트림을 가져와 전달합니다.

    Args:
        url: 프록시할 스트림 URL (예: http://camera-ip:81/stream)

    Returns:
        MJPEG 스트림 응답
    """
    if not url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="스트림 URL이 필요합니다",
        )

    # URL 유효성 검사
    if not url.startswith(("http://", "https://")):
        url = f"http://{url}"

    logger.info(f"Proxying stream: {url}")

    return StreamingResponse(
        stream_proxy(url),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get("/info/{device_id}")
async def get_stream_info(
    device_id: int,
    db: Session = Depends(get_db),
):
    """
    장비의 사용 가능한 스트림 URL 정보를 반환합니다.

    Args:
        device_id: 장비 DB ID

    Returns:
        스트림 URL 정보 (HTTP, RTSP 등)
    """
    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="장비를 찾을 수 없습니다",
        )

    # HTTP 스트림 URL 생성
    http_stream_url = None
    if device.ip_address:
        ip = device.ip_address
        if ":" in ip and "/" in ip:
            http_stream_url = f"http://{ip}"
        elif ":" in ip:
            http_stream_url = f"http://{ip}/stream"
        else:
            http_stream_url = f"http://{ip}:81/stream"

    # RTSP URL
    rtsp_url = device.rtsp_url if device.rtsp_url else None

    return {
        "device_id": device_id,
        "device_name": device.device_name,
        "is_online": device.is_online,
        "streams": {
            "http": {
                "url": http_stream_url,
                "proxy_url": (
                    f"/stream/device/{device_id}?type=http" if http_stream_url else None
                ),
                "supported": True,
                "description": "HTTP MJPEG 스트림 (브라우저 호환)",
            },
            "rtsp": {
                "url": rtsp_url,
                "supported": False,  # 브라우저에서 직접 재생 불가
                "description": "RTSP 스트림 (VLC 등 외부 플레이어 필요)",
                "external_players": ["VLC", "ffplay", "MPV"],
            },
        },
        "recommended": "http",
    }


@router.get("/device/{device_id}")
async def proxy_device_stream(
    device_id: int,
    stream_type: str = Query("http", description="스트림 타입: http 또는 rtsp"),
    db: Session = Depends(get_db),
):
    """
    장비 ID로 해당 장비의 카메라 스트림을 프록시합니다.

    Args:
        device_id: 장비 DB ID
        stream_type: 스트림 타입 (http: MJPEG 프록시, rtsp: RTSP URL 반환)

    Returns:
        http: MJPEG 스트림 응답
        rtsp: RTSP URL 정보 (JSON)
    """
    # 장비 조회
    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="장비를 찾을 수 없습니다",
        )

    if not device.is_online:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="장비가 오프라인 상태입니다",
        )

    # RTSP 타입 요청 시 URL 정보만 반환
    if stream_type.lower() == "rtsp":
        rtsp_url = device.rtsp_url
        if not rtsp_url:
            # RTSP URL이 없으면 기본 URL 생성
            if device.ip_address:
                rtsp_url = f"rtsp://{device.ip_address}:554/stream"
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="RTSP URL이 설정되지 않았습니다",
                )

        return JSONResponse(
            content={
                "device_id": device_id,
                "device_name": device.device_name,
                "stream_type": "rtsp",
                "url": rtsp_url,
                "note": "RTSP 스트림은 브라우저에서 직접 재생할 수 없습니다. VLC, ffplay 등 외부 플레이어를 사용하세요.",
                "commands": {
                    "vlc": f"vlc {rtsp_url}",
                    "ffplay": f"ffplay {rtsp_url}",
                    "mpv": f"mpv {rtsp_url}",
                },
            }
        )

    # HTTP 스트림 URL 결정
    stream_url = None

    # rtsp_url이 http:// 로 시작하면 사용 (HTTP MJPEG 스트림)
    if device.rtsp_url and device.rtsp_url.startswith("http"):
        stream_url = device.rtsp_url

    # HTTP URL이 없으면 IP 주소로 HTTP 스트림 URL 생성
    if not stream_url and device.ip_address:
        ip = device.ip_address
        if ":" in ip and "/" in ip:
            stream_url = f"http://{ip}"
        elif ":" in ip:
            stream_url = f"http://{ip}/stream"
        else:
            # ESP32-CAM 기본 MJPEG 스트림 포트 (81)
            stream_url = f"http://{ip}:81/stream"

    if not stream_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="장비의 스트림 URL이 설정되지 않았습니다",
        )

    logger.info(f"Proxying device stream: device_id={device_id}, url={stream_url}")

    return StreamingResponse(
        stream_proxy(stream_url),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "Access-Control-Allow-Origin": "*",
            "X-Device-Id": str(device_id),
            "X-Device-Name": device.device_name,
            "X-Stream-Type": "http",
        },
    )


@router.get("/snapshot/{device_id}")
async def get_device_snapshot(
    device_id: int,
    db: Session = Depends(get_db),
):
    """
    장비의 현재 스냅샷(단일 프레임)을 가져옵니다.

    Args:
        device_id: 장비 DB ID

    Returns:
        JPEG 이미지 응답
    """
    # 장비 조회
    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="장비를 찾을 수 없습니다",
        )

    if not device.is_online:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="장비가 오프라인 상태입니다",
        )

    # 스냅샷 URL 결정 (일반적으로 /capture 엔드포인트)
    ip = device.ip_address
    if not ip:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="장비의 IP 주소가 설정되지 않았습니다",
        )

    # ESP32-CAM 스냅샷 URL
    if ":" in ip:
        snapshot_url = f"http://{ip.split(':')[0]}:81/capture"
    else:
        snapshot_url = f"http://{ip}:81/capture"

    logger.info(f"Getting snapshot: device_id={device_id}, url={snapshot_url}")

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            response = await client.get(snapshot_url)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"스냅샷을 가져올 수 없습니다: {response.status_code}",
                )

            return StreamingResponse(
                iter([response.content]),
                media_type="image/jpeg",
                headers={
                    "Cache-Control": "no-cache",
                    "Access-Control-Allow-Origin": "*",
                    "X-Device-Id": str(device_id),
                },
            )

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="스냅샷 요청 시간 초과",
        )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="장비에 연결할 수 없습니다",
        )
