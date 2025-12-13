"""
장비 관리 API 테스트
"""

import pytest
from app.models import Device


class TestDeviceList:
    """장비 목록 조회 테스트"""

    def test_list_devices_empty(self, client):
        """빈 장비 목록 조회"""
        response = client.get("/devices/")
        assert response.status_code == 200
        data = response.json()
        assert data["devices"] == []
        assert data["total"] == 0

    def test_list_devices_with_data(self, client, db_session):
        """장비가 있는 경우 목록 조회"""
        # 테스트 장비 생성
        device = Device(
            device_id="test_device_001",
            device_name="Test Device",
            device_type="camera",
            is_online=True,
        )
        db_session.add(device)
        db_session.commit()

        response = client.get("/devices/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["devices"][0]["device_id"] == "test_device_001"

    def test_list_devices_pagination(self, client, db_session):
        """페이지네이션 테스트"""
        # 15개 장비 생성
        for i in range(15):
            device = Device(
                device_id=f"device_{i:03d}",
                device_name=f"Device {i}",
                device_type="camera",
            )
            db_session.add(device)
        db_session.commit()

        # 첫 페이지 (10개)
        response = client.get("/devices/?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["devices"]) == 10
        assert data["total"] == 15

        # 두 번째 페이지 (5개)
        response = client.get("/devices/?page=2&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["devices"]) == 5


class TestDeviceRegister:
    """장비 등록 테스트"""

    def test_register_device_success(self, client):
        """정상 장비 등록"""
        response = client.post(
            "/devices/",
            json={
                "device_id": "new_device_001",
                "device_name": "New Camera",
                "device_type": "camera",
                "ip_address": "192.168.1.100",
                "location": "Office",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["device_id"] == "new_device_001"
        assert data["device_name"] == "New Camera"
        assert data["ip_address"] == "192.168.1.100"
        # RTSP URL 자동 생성 확인
        assert "rtsp://" in data["rtsp_url"]

    def test_register_device_duplicate_id(self, client, db_session):
        """중복 device_id로 등록 실패"""
        # 기존 장비 생성
        device = Device(
            device_id="existing_device", device_name="Existing", device_type="camera"
        )
        db_session.add(device)
        db_session.commit()

        # 동일 ID로 등록 시도
        response = client.post(
            "/devices/",
            json={
                "device_id": "existing_device",
                "device_name": "New Device",
                "device_type": "camera",
            },
        )
        assert response.status_code == 400
        assert "이미 등록된" in response.json()["detail"]

    def test_register_device_duplicate_ip(self, client, db_session):
        """중복 IP로 등록 실패"""
        # 기존 장비 생성
        device = Device(
            device_id="device_with_ip",
            device_name="Device with IP",
            device_type="camera",
            ip_address="192.168.1.50",
        )
        db_session.add(device)
        db_session.commit()

        # 동일 IP로 등록 시도
        response = client.post(
            "/devices/",
            json={
                "device_id": "new_device",
                "device_name": "New Device",
                "device_type": "camera",
                "ip_address": "192.168.1.50",
            },
        )
        assert response.status_code == 400
        assert "이미 사용 중인 IP" in response.json()["detail"]


class TestDeviceDetail:
    """장비 상세 조회 테스트"""

    def test_get_device_success(self, client, db_session):
        """정상 장비 조회"""
        device = Device(
            device_id="detail_test",
            device_name="Detail Test Device",
            device_type="camera",
            location="Test Room",
        )
        db_session.add(device)
        db_session.commit()

        response = client.get(f"/devices/{device.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["device_id"] == "detail_test"
        assert data["location"] == "Test Room"

    def test_get_device_not_found(self, client):
        """존재하지 않는 장비 조회"""
        response = client.get("/devices/99999")
        assert response.status_code == 404


class TestDeviceUpdate:
    """장비 수정 테스트"""

    def test_update_device_success(self, client, db_session):
        """정상 장비 수정"""
        device = Device(
            device_id="update_test", device_name="Before Update", device_type="camera"
        )
        db_session.add(device)
        db_session.commit()

        response = client.put(
            f"/devices/{device.id}",
            json={"device_name": "After Update", "location": "New Location"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["device_name"] == "After Update"
        assert data["location"] == "New Location"


class TestDeviceDelete:
    """장비 삭제 테스트"""

    def test_delete_device_success(self, client, db_session):
        """정상 장비 삭제"""
        device = Device(
            device_id="delete_test", device_name="To Delete", device_type="camera"
        )
        db_session.add(device)
        db_session.commit()
        device_id = device.id

        response = client.delete(f"/devices/{device_id}")
        assert response.status_code == 204

        # 삭제 확인
        response = client.get(f"/devices/{device_id}")
        assert response.status_code == 404

    def test_delete_device_not_found(self, client):
        """존재하지 않는 장비 삭제"""
        response = client.delete("/devices/99999")
        assert response.status_code == 404
