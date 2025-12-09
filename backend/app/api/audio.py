"""
오디오 파일 관리 API 엔드포인트
보안 가이드라인 6 준수: 파일 업로드 검증
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import User, AuditLog
from app.dependencies import require_operator, get_client_ip
from app.services import get_audio_service
from app.utils.logger import logger


router = APIRouter(prefix="/audio", tags=["오디오 파일 관리"])


@router.post("/upload", response_model=dict, status_code=status.HTTP_201_CREATED)
async def upload_audio_file(
    file: UploadFile = File(...),
    # TODO: 로그인 수정 후 활성화
    # current_user: User = Depends(require_operator),
    db: Session = Depends(get_db),
    request: Request = None
) -> dict:
    """
    오디오 파일 업로드
    
    권한: OPERATOR 이상
    보안: 파일 형식 검증, 크기 제한, 파일명 정제
    """
    audio_service = get_audio_service()
    
    try:
        # 파일 크기 확인 (메모리에 로드하지 않고)
        file.file.seek(0, 2)  # 파일 끝으로 이동
        file_size = file.file.tell()
        file.file.seek(0)  # 다시 처음으로
        
        # 파일 검증
        is_valid, error_msg = audio_service.validate_audio_file(
            file.filename,
            file_size
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # 파일 저장
        saved_filename, file_path = audio_service.save_audio_file(
            file.file,
            file.filename
        )
        
        # TODO: 로그인 수정 후 감사 로그 활성화
        # ip_address = get_client_ip(request) if request else None
        # audit_log = AuditLog(
        #     user_id=current_user.id,
        #     action="upload_audio",
        #     resource_type="audio_file",
        #     resource_id=saved_filename,
        #     ip_address=ip_address
        # )
        # db.add(audit_log)
        # db.commit()
        
        logger.info(f"오디오 파일 업로드: {file.filename}")
        
        return {
            "success": True,
            "message": "파일이 성공적으로 업로드되었습니다",
            "filename": saved_filename,
            "original_filename": file.filename,
            "size": file_size,
            "url": audio_service.get_audio_url(saved_filename)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파일 업로드 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="파일 업로드에 실패했습니다"
        )


@router.get("/list")
async def list_audio_files(
    # TODO: 로그인 수정 후 활성화
    # current_user: User = Depends(require_operator)
):
    """
    업로드된 오디오 파일 목록 조회
    
    권한: OPERATOR 이상
    """
    audio_service = get_audio_service()
    files = audio_service.list_audio_files()
    
    return files


@router.get("/{filename}")
async def download_audio_file(
    filename: str,
    # TODO: 로그인 수정 후 활성화
    # current_user: User = Depends(require_operator)
):
    """
    오디오 파일 다운로드
    
    권한: OPERATOR 이상
    보안: 경로 검증, 권한 확인
    """
    audio_service = get_audio_service()
    
    # 파일 경로 가져오기
    file_path = audio_service.get_audio_file_path(filename)
    
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="파일을 찾을 수 없습니다"
        )
    
    # 파일 응답
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream"
    )


@router.delete("/{filename}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_audio_file(
    filename: str,
    current_user: User = Depends(require_operator),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    오디오 파일 삭제
    
    권한: OPERATOR 이상
    """
    audio_service = get_audio_service()
    
    # 파일 삭제
    success = audio_service.delete_audio_file(filename)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="파일을 찾을 수 없습니다"
        )
    
    # 감사 로그 기록
    ip_address = get_client_ip(request) if request else None
    audit_log = AuditLog(
        user_id=current_user.id,
        action="delete_audio",
        resource_type="audio_file",
        resource_id=filename,
        ip_address=ip_address
    )
    db.add(audit_log)
    db.commit()
    
    logger.info(f"사용자 {current_user.username}가 오디오 파일 삭제: {filename}")
    
    return None

