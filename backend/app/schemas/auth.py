"""
인증 관련 Pydantic 스키마
"""
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """로그인 요청 스키마"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)


class TokenResponse(BaseModel):
    """토큰 응답 스키마"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """토큰 갱신 요청 스키마"""
    refresh_token: str


class TokenPayload(BaseModel):
    """토큰 페이로드 스키마"""
    sub: int  # user_id
    username: str
    role: str
    exp: int
    iat: int
    type: str

