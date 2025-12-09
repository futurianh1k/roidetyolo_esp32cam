"""
ASR 서비스

ASR (Automatic Speech Recognition) 서버와 통신하는 클라이언트 서비스

주요 기능:
- ASR 서버에 세션 생성/종료 요청
- 세션 상태 조회
- 에러 처리 및 재시도
"""

import asyncio
import logging
from typing import Optional, Dict
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class ASRService:
    """
    ASR 서버 클라이언트 서비스
    
    ASR 서버(Sherpa-ONNX 기반)와 HTTP 통신을 수행합니다.
    세션 관리, 상태 조회 등의 기능을 제공합니다.
    
    Attributes:
        asr_server_url (str): ASR 서버 URL
        timeout (float): HTTP 요청 타임아웃 (초)
        max_retries (int): 최대 재시도 횟수
    """
    
    def __init__(self, asr_server_url: str = None, timeout: float = 30.0, max_retries: int = 3):
        """
        ASR 서비스 초기화
        
        Args:
            asr_server_url: ASR 서버 URL (기본값: settings.ASR_SERVER_URL)
            timeout: HTTP 요청 타임아웃 (초)
            max_retries: 최대 재시도 횟수
        """
        self.asr_server_url = asr_server_url or getattr(settings, 'ASR_SERVER_URL', 'http://localhost:8001')
        self.timeout = timeout
        self.max_retries = max_retries
        
        logger.info(f"ASR Service 초기화: {self.asr_server_url}")
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """
        HTTP 요청 (재시도 로직 포함)
        
        Args:
            method: HTTP 메서드 (GET, POST 등)
            endpoint: API 엔드포인트 경로
            **kwargs: httpx 요청 파라미터
        
        Returns:
            응답 JSON 딕셔너리
        
        Raises:
            httpx.HTTPStatusError: HTTP 에러 발생 시
            httpx.RequestError: 네트워크 에러 발생 시
        """
        url = f"{self.asr_server_url}{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(method, url, **kwargs)
                    response.raise_for_status()
                    return response.json()
            
            except httpx.HTTPStatusError as e:
                logger.error(f"ASR 서버 HTTP 에러 (시도 {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(1)  # 1초 대기 후 재시도
            
            except httpx.RequestError as e:
                logger.error(f"ASR 서버 연결 실패 (시도 {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(1)
        
        raise RuntimeError("ASR 서버 요청 실패: 최대 재시도 횟수 초과")
    
    async def create_session(self, device_id: str, language: str = "auto", 
                           sample_rate: int = 16000, vad_enabled: bool = True) -> Dict:
        """
        ASR 세션 생성
        
        ASR 서버에 새로운 음성인식 세션을 생성합니다.
        
        Args:
            device_id: 장비 ID (예: "cores3_01")
            language: 언어 코드 (auto, ko, en, zh, ja, yue)
            sample_rate: 샘플레이트 (Hz)
            vad_enabled: VAD 활성화 여부
        
        Returns:
            {
                'session_id': 'uuid-xxxx',
                'ws_url': 'ws://...',
                'status': 'ready',
                'message': '...'
            }
        
        Raises:
            httpx.HTTPStatusError: ASR 서버 에러
            httpx.RequestError: 네트워크 에러
        
        Example:
            >>> asr_service = ASRService()
            >>> result = await asr_service.create_session("cores3_01", "ko")
            >>> print(f"Session ID: {result['session_id']}")
        """
        logger.info(f"ASR 세션 생성 요청: device_id={device_id}, language={language}")
        
        payload = {
            "device_id": device_id,
            "language": language,
            "sample_rate": sample_rate,
            "vad_enabled": vad_enabled
        }
        
        try:
            result = await self._request("POST", "/asr/session/start", json=payload)
            
            logger.info(f"✅ ASR 세션 생성 완료: {result['session_id']}")
            logger.debug(f"   WebSocket URL: {result['ws_url']}")
            
            return result
        
        except Exception as e:
            logger.error(f"❌ ASR 세션 생성 실패: {e}")
            raise
    
    async def get_session_status(self, session_id: str) -> Dict:
        """
        ASR 세션 상태 조회
        
        Args:
            session_id: 조회할 세션 ID
        
        Returns:
            {
                'session_id': '...',
                'device_id': '...',
                'is_active': True,
                'is_processing': False,
                'segments_count': 5,
                'last_result': '...',
                'created_at': '...',
                'language': '...'
            }
        
        Raises:
            httpx.HTTPStatusError: 세션을 찾을 수 없거나 서버 에러
            httpx.RequestError: 네트워크 에러
        
        Example:
            >>> status = await asr_service.get_session_status("uuid-xxxx")
            >>> print(f"Active: {status['is_active']}")
        """
        logger.debug(f"ASR 세션 상태 조회: {session_id}")
        
        try:
            result = await self._request("GET", f"/asr/session/{session_id}/status")
            
            logger.debug(f"세션 상태: active={result['is_active']}, processing={result['is_processing']}")
            
            return result
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"⚠️ 세션을 찾을 수 없음: {session_id}")
            raise
        
        except Exception as e:
            logger.error(f"❌ ASR 세션 상태 조회 실패: {e}")
            raise
    
    async def stop_session(self, session_id: str) -> Dict:
        """
        ASR 세션 종료
        
        Args:
            session_id: 종료할 세션 ID
        
        Returns:
            {
                'session_id': '...',
                'status': 'stopped',
                'message': '...',
                'segments_count': 5
            }
        
        Raises:
            httpx.HTTPStatusError: 세션을 찾을 수 없거나 서버 에러
            httpx.RequestError: 네트워크 에러
        
        Example:
            >>> result = await asr_service.stop_session("uuid-xxxx")
            >>> print(f"Stopped: {result['segments_count']} segments")
        """
        logger.info(f"ASR 세션 종료 요청: {session_id}")
        
        try:
            result = await self._request("POST", f"/asr/session/{session_id}/stop")
            
            logger.info(f"✅ ASR 세션 종료 완료: {session_id} ({result['segments_count']} 세그먼트)")
            
            return result
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"⚠️ 세션을 찾을 수 없음: {session_id}")
            raise
        
        except Exception as e:
            logger.error(f"❌ ASR 세션 종료 실패: {e}")
            raise
    
    async def list_sessions(self) -> Dict:
        """
        활성 세션 목록 조회
        
        Returns:
            {
                'total': 2,
                'sessions': [...]
            }
        
        Raises:
            httpx.RequestError: 네트워크 에러
        
        Example:
            >>> result = await asr_service.list_sessions()
            >>> print(f"Active sessions: {result['total']}")
        """
        logger.debug("ASR 활성 세션 목록 조회")
        
        try:
            result = await self._request("GET", "/asr/sessions")
            
            logger.debug(f"활성 세션: {result['total']}개")
            
            return result
        
        except Exception as e:
            logger.error(f"❌ ASR 세션 목록 조회 실패: {e}")
            raise
    
    async def health_check(self) -> Dict:
        """
        ASR 서버 헬스 체크
        
        Returns:
            {
                'status': 'healthy',
                'recognizer_loaded': True,
                'active_sessions': 2
            }
        
        Example:
            >>> health = await asr_service.health_check()
            >>> print(f"Status: {health['status']}")
        """
        logger.debug("ASR 서버 헬스 체크")
        
        try:
            result = await self._request("GET", "/health")
            return result
        
        except Exception as e:
            logger.error(f"❌ ASR 서버 헬스 체크 실패: {e}")
            raise


# 전역 인스턴스 (싱글톤)
asr_service = ASRService()


# 편의 함수 (전역 인스턴스 사용)
async def create_asr_session(device_id: str, language: str = "auto") -> Dict:
    """
    ASR 세션 생성 (전역 인스턴스 사용)
    
    Args:
        device_id: 장비 ID
        language: 언어 코드
    
    Returns:
        세션 정보 딕셔너리
    """
    return await asr_service.create_session(device_id, language)


async def stop_asr_session(session_id: str) -> Dict:
    """
    ASR 세션 종료 (전역 인스턴스 사용)
    
    Args:
        session_id: 세션 ID
    
    Returns:
        종료 정보 딕셔너리
    """
    return await asr_service.stop_session(session_id)


async def get_asr_session_status(session_id: str) -> Dict:
    """
    ASR 세션 상태 조회 (전역 인스턴스 사용)
    
    Args:
        session_id: 세션 ID
    
    Returns:
        세션 상태 딕셔너리
    """
    return await asr_service.get_session_status(session_id)
