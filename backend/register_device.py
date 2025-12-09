"""
장비 등록 스크립트
인증 우회 상태에서 Core S3 장비를 데이터베이스에 등록합니다.
"""
import requests
import json
from datetime import datetime

# 백엔드 서버 URL
API_BASE_URL = "http://localhost:8000"

# 펌웨어 config.h의 장비 정보
DEVICE_DATA = {
    "device_id": "core_s3_001",
    "device_name": "Core S3 Camera",
    "device_type": "CoreS3",
    "ip_address": "10.10.11.18",  # 실제 ESP32의 IP로 변경 필요
    "location": "Office",
    "description": "M5Stack Core S3 Camera Device"
}

def check_backend_health():
    """백엔드 서버 상태 확인"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 백엔드 서버 정상")
            print(f"   응답: {response.json()}")
            return True
        else:
            print(f"❌ 백엔드 서버 오류: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 백엔드 서버 연결 실패")
        print("   백엔드 서버가 실행 중인지 확인하세요:")
        print("   cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return False
    except Exception as e:
        print(f"❌ 예외 발생: {e}")
        return False

def check_existing_device(device_id):
    """이미 등록된 장비인지 확인"""
    try:
        response = requests.get(f"{API_BASE_URL}/devices/", timeout=5)
        if response.status_code == 200:
            devices = response.json().get("devices", [])
            for device in devices:
                if device.get("device_id") == device_id:
                    return device
        return None
    except Exception as e:
        print(f"❌ 장비 조회 실패: {e}")
        return None

def register_device(device_data):
    """장비 등록"""
    try:
        print(f"\n📝 장비 등록 중...")
        print(f"   장비 ID: {device_data['device_id']}")
        print(f"   장비명: {device_data['device_name']}")
        
        response = requests.post(
            f"{API_BASE_URL}/devices/",
            json=device_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 201:
            device = response.json()
            print("✅ 장비 등록 성공!")
            print(f"   등록 ID: {device.get('id')}")
            print(f"   장비명: {device.get('device_name')}")
            print(f"   RTSP URL: {device.get('rtsp_url')}")
            print(f"   MQTT Topic: {device.get('mqtt_topic')}")
            return device
        elif response.status_code == 400:
            error = response.json()
            if "이미 등록된" in error.get("detail", ""):
                print("⚠️  이미 등록된 장비입니다.")
                return None
            else:
                print(f"❌ 장비 등록 실패: {error.get('detail')}")
                return None
        else:
            print(f"❌ 장비 등록 실패: HTTP {response.status_code}")
            print(f"   응답: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 예외 발생: {e}")
        return None

def list_all_devices():
    """등록된 모든 장비 목록 조회"""
    try:
        response = requests.get(f"{API_BASE_URL}/devices/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            devices = data.get("devices", [])
            total = data.get("total", 0)
            
            print(f"\n📋 등록된 장비 목록 (총 {total}개)")
            print("=" * 80)
            
            if not devices:
                print("   등록된 장비가 없습니다.")
            else:
                for i, device in enumerate(devices, 1):
                    print(f"\n{i}. {device.get('device_name')} (ID: {device.get('device_id')})")
                    print(f"   타입: {device.get('device_type')}")
                    print(f"   IP: {device.get('ip_address')}")
                    print(f"   위치: {device.get('location')}")
                    print(f"   상태: {'🟢 온라인' if device.get('is_online') else '🔴 오프라인'}")
                    print(f"   등록일: {device.get('registered_at')}")
            
            print("=" * 80)
            return devices
        else:
            print(f"❌ 장비 목록 조회 실패: HTTP {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ 예외 발생: {e}")
        return []

def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("Core S3 Management System - 장비 등록")
    print("=" * 80)
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. 백엔드 서버 상태 확인
    print("[1/4] 백엔드 서버 상태 확인...")
    if not check_backend_health():
        return
    
    # 2. 기존 장비 확인
    print("\n[2/4] 기존 장비 확인...")
    existing_device = check_existing_device(DEVICE_DATA["device_id"])
    
    if existing_device:
        print(f"⚠️  장비 '{DEVICE_DATA['device_id']}'가 이미 등록되어 있습니다.")
        print(f"   등록 ID: {existing_device.get('id')}")
        print(f"   장비명: {existing_device.get('device_name')}")
        print(f"   등록일: {existing_device.get('registered_at')}")
        print("\n   스킵하고 다음 단계로 진행합니다.")
    else:
        print("✅ 신규 장비입니다.")
        
        # 3. 장비 등록
        print("\n[3/4] 장비 등록...")
        register_device(DEVICE_DATA)
    
    # 4. 전체 장비 목록 조회
    print("\n[4/4] 전체 장비 목록 조회...")
    list_all_devices()
    
    print("\n" + "=" * 80)
    print("✅ 완료!")
    print("=" * 80)
    print("\n다음 단계:")
    print("1. 프론트엔드 접속: http://localhost:3000")
    print("2. 대시보드에서 등록된 장비 확인")
    print("3. Core S3 펌웨어 업로드 (platformio run --target upload)")
    print("4. 장비가 MQTT로 연결되면 상태가 자동으로 업데이트됩니다.")
    print()

if __name__ == "__main__":
    main()
