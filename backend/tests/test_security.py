"""
보안 모듈 테스트
"""

import pytest
from app.security import (
    verify_password,
    get_password_hash,
    validate_password_strength,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
    verify_token_type,
)


class TestPasswordHashing:
    """비밀번호 해싱 테스트"""

    def test_password_hash_different(self):
        """같은 비밀번호도 다른 해시 생성 (salt 적용)"""
        password = "TestPassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        assert hash1 != hash2  # 다른 해시여야 함

    def test_password_verify_correct(self):
        """올바른 비밀번호 검증"""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_password_verify_wrong(self):
        """잘못된 비밀번호 검증"""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        assert verify_password("wrongpassword", hashed) is False

    def test_bcrypt_format(self):
        """BCrypt 형식 확인"""
        hashed = get_password_hash("test123")
        # BCrypt 해시는 $2b$ 또는 $2a$로 시작
        assert hashed.startswith("$2")


class TestPasswordStrength:
    """비밀번호 강도 검증 테스트"""

    def test_valid_password(self):
        """유효한 비밀번호"""
        is_valid, msg = validate_password_strength("ValidPass123!")
        assert is_valid is True
        assert msg == ""

    def test_too_short(self):
        """너무 짧은 비밀번호"""
        is_valid, msg = validate_password_strength("Ab1!")
        assert is_valid is False
        assert "8자" in msg

    def test_too_long(self):
        """너무 긴 비밀번호"""
        long_password = "A" * 129 + "a1"
        is_valid, msg = validate_password_strength(long_password)
        assert is_valid is False
        assert "128자" in msg

    def test_no_uppercase(self):
        """대문자 없음"""
        is_valid, msg = validate_password_strength("lowercase123")
        assert is_valid is False
        assert "대문자" in msg

    def test_no_lowercase(self):
        """소문자 없음"""
        is_valid, msg = validate_password_strength("UPPERCASE123")
        assert is_valid is False
        assert "소문자" in msg

    def test_no_digit(self):
        """숫자 없음"""
        is_valid, msg = validate_password_strength("NoDigitHere!")
        assert is_valid is False
        assert "숫자" in msg


class TestJWTToken:
    """JWT 토큰 테스트"""

    def test_create_access_token(self):
        """Access Token 생성"""
        data = {"sub": 1, "username": "testuser"}
        token = create_access_token(data)
        assert token is not None
        assert len(token.split(".")) == 3  # JWT는 3부분

    def test_create_refresh_token(self):
        """Refresh Token 생성"""
        data = {"sub": 1}
        token = create_refresh_token(data)
        assert token is not None

    def test_decode_valid_token(self):
        """유효한 토큰 디코딩"""
        data = {"sub": 1, "username": "testuser"}
        token = create_access_token(data)
        decoded = decode_token(token)
        assert decoded is not None
        assert decoded["sub"] == 1
        assert decoded["username"] == "testuser"
        assert decoded["type"] == "access"

    def test_decode_invalid_token(self):
        """유효하지 않은 토큰 디코딩"""
        decoded = decode_token("invalid.token.here")
        assert decoded is None

    def test_verify_token_type_access(self):
        """Access Token 타입 검증"""
        data = {"sub": 1}
        token = create_access_token(data)
        payload = decode_token(token)
        assert verify_token_type(payload, "access") is True
        assert verify_token_type(payload, "refresh") is False

    def test_verify_token_type_refresh(self):
        """Refresh Token 타입 검증"""
        data = {"sub": 1}
        token = create_refresh_token(data)
        payload = decode_token(token)
        assert verify_token_type(payload, "refresh") is True
        assert verify_token_type(payload, "access") is False


class TestTokenHash:
    """토큰 해시 테스트 (Refresh Token DB 저장용)"""

    def test_hash_token_consistent(self):
        """같은 토큰은 같은 해시"""
        token = "some-refresh-token-value"
        hash1 = hash_token(token)
        hash2 = hash_token(token)
        assert hash1 == hash2

    def test_hash_token_different_tokens(self):
        """다른 토큰은 다른 해시"""
        token1 = "token-one"
        token2 = "token-two"
        assert hash_token(token1) != hash_token(token2)

    def test_hash_is_sha256(self):
        """SHA-256 형식 확인 (64자 hex)"""
        hashed = hash_token("test-token")
        assert len(hashed) == 64
        assert all(c in "0123456789abcdef" for c in hashed)
