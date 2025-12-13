"""
인증 API 테스트
"""

import pytest


class TestAuthRegister:
    """회원가입 테스트"""

    def test_register_success(self, client):
        """정상 회원가입"""
        response = client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "NewPassword123!",
                "role": "viewer",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "password" not in data  # 비밀번호는 응답에 없어야 함

    def test_register_weak_password(self, client):
        """약한 비밀번호로 회원가입 실패"""
        response = client.post(
            "/auth/register",
            json={
                "username": "weakuser",
                "email": "weak@example.com",
                "password": "weak",  # 너무 짧음
                "role": "viewer",
            },
        )
        assert response.status_code == 400
        assert "8자" in response.json()["detail"]

    def test_register_duplicate_username(self, client, test_user):
        """중복 사용자명으로 회원가입 실패"""
        response = client.post(
            "/auth/register",
            json={
                "username": test_user.username,  # 이미 존재
                "email": "another@example.com",
                "password": "ValidPassword123!",
                "role": "viewer",
            },
        )
        assert response.status_code == 400
        assert "이미 존재" in response.json()["detail"]


class TestAuthLogin:
    """로그인 테스트"""

    def test_login_success(self, client, test_user):
        """정상 로그인"""
        response = client.post(
            "/auth/login", json={"username": "testuser", "password": "TestPassword123!"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, test_user):
        """잘못된 비밀번호로 로그인 실패"""
        response = client.post(
            "/auth/login", json={"username": "testuser", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        # 보안: 사용자명/비밀번호 중 무엇이 틀렸는지 알려주지 않음
        assert "사용자명 또는 비밀번호" in response.json()["detail"]

    def test_login_nonexistent_user(self, client):
        """존재하지 않는 사용자로 로그인 실패"""
        response = client.post(
            "/auth/login", json={"username": "nonexistent", "password": "somepassword"}
        )
        assert response.status_code == 401


class TestAuthRefresh:
    """토큰 갱신 테스트"""

    def test_refresh_token_success(self, client, test_user):
        """정상 토큰 갱신"""
        # 먼저 로그인
        login_response = client.post(
            "/auth/login", json={"username": "testuser", "password": "TestPassword123!"}
        )
        refresh_token = login_response.json()["refresh_token"]

        # 토큰 갱신
        response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        # 새 토큰은 이전 토큰과 달라야 함
        assert data["refresh_token"] != refresh_token

    def test_refresh_invalid_token(self, client):
        """잘못된 토큰으로 갱신 실패"""
        response = client.post(
            "/auth/refresh", json={"refresh_token": "invalid.token.here"}
        )
        assert response.status_code == 401


class TestAuthMe:
    """현재 사용자 정보 조회 테스트"""

    def test_get_me_success(self, client, test_user, auth_headers):
        """인증된 사용자 정보 조회"""
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email

    def test_get_me_unauthorized(self, client):
        """인증 없이 조회 실패"""
        response = client.get("/auth/me")
        assert response.status_code == 401
