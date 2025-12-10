"""
오디오 파일 처리 서비스
보안 가이드라인 6 준수: 파일 업로드 검증
"""
import os
import uuid
from pathlib import Path
from typing import Optional, BinaryIO
import shutil

from app.config import settings
from app.utils.logger import logger
from app.utils.validators import validate_file_extension, sanitize_filename


class AudioService:
    """오디오 파일 관리 서비스"""
    
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR) / "audio"
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_audio_file(self, filename: str, file_size: int) -> tuple[bool, str]:
        """
        오디오 파일 검증
        보안 가이드라인 6: 화이트리스트, 크기 제한
        
        Args:
            filename: 파일명
            file_size: 파일 크기 (바이트)
        
        Returns:
            tuple[bool, str]: (유효성 여부, 오류 메시지)
        """
        # 확장자 검증
        if not validate_file_extension(
            filename,
            settings.allowed_audio_extensions_list
        ):
            return False, f"허용되지 않는 파일 형식입니다. 허용: {settings.ALLOWED_AUDIO_EXTENSIONS}"
        
        # 파일 크기 검증
        if file_size > settings.MAX_UPLOAD_SIZE:
            max_mb = settings.MAX_UPLOAD_SIZE / 1024 / 1024
            return False, f"파일 크기가 너무 큽니다. 최대: {max_mb}MB"
        
        return True, ""
    
    def save_audio_file(
        self,
        file: BinaryIO,
        original_filename: str
    ) -> tuple[str, str]:
        """
        오디오 파일 저장
        보안: 파일명 정제, 웹 루트 외부 저장
        
        Args:
            file: 파일 객체
            original_filename: 원본 파일명
        
        Returns:
            tuple[str, str]: (저장된 파일명, 파일 경로)
        """
        try:
            # 파일명 정제
            safe_filename = sanitize_filename(original_filename)
            
            # 고유 파일명 생성 (충돌 방지)
            file_ext = safe_filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
            
            # 저장 경로
            file_path = self.upload_dir / unique_filename
            
            # 파일 저장
            with open(file_path, 'wb') as f:
                shutil.copyfileobj(file, f)
            
            logger.info(f"오디오 파일 저장: {unique_filename}")
            
            return unique_filename, str(file_path)
        
        except Exception as e:
            logger.error(f"오디오 파일 저장 실패: {e}")
            raise
    
    def delete_audio_file(self, filename: str) -> bool:
        """
        오디오 파일 삭제
        
        Args:
            filename: 파일명
        
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            file_path = self.upload_dir / filename
            
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
                logger.info(f"오디오 파일 삭제: {filename}")
                return True
            else:
                logger.warning(f"오디오 파일 없음: {filename}")
                return False
        
        except Exception as e:
            logger.error(f"오디오 파일 삭제 실패: {e}")
            return False
    
    def get_audio_file_path(self, filename: str) -> Optional[Path]:
        """
        오디오 파일 경로 가져오기
        
        Args:
            filename: 파일명
        
        Returns:
            Optional[Path]: 파일 경로 또는 None
        """
        file_path = self.upload_dir / filename
        
        if file_path.exists() and file_path.is_file():
            return file_path
        
        return None
    
    def get_audio_url(self, filename: str) -> str:
        """
        오디오 파일 URL 생성
        
        Args:
            filename: 파일명
        
        Returns:
            str: 파일 URL (상대 경로)
        """
        return f"/audio/{filename}"
    
    def list_audio_files(self) -> list[dict]:
        """
        업로드된 오디오 파일 목록
        
        Returns:
            list[dict]: 파일 정보 리스트
        """
        files = []
        
        for file_path in self.upload_dir.glob('*'):
            if file_path.is_file():
                files.append({
                    'filename': file_path.name,
                    'size': file_path.stat().st_size,
                    'created_at': file_path.stat().st_ctime,
                    'url': self.get_audio_url(file_path.name)
                })
        
        return files


# 전역 오디오 서비스 인스턴스
audio_service = AudioService()


def get_audio_service() -> AudioService:
    """오디오 서비스 인스턴스 가져오기"""
    return audio_service

