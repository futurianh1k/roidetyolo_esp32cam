"""
입력 검증 유틸리티
보안 가이드라인 3-1 준수: 백엔드 입력 검증
"""
import re
from typing import Optional


def validate_device_id(device_id: str) -> bool:
    """
    장비 ID 검증 (MAC 주소 또는 고유 ID 형식)
    
    Args:
        device_id: 장비 ID
    
    Returns:
        bool: 유효성 여부
    """
    # MAC 주소 형식: XX:XX:XX:XX:XX:XX 또는 XX-XX-XX-XX-XX-XX
    mac_pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
    
    # 또는 영숫자+언더스코어 조합 (3-50자)
    id_pattern = r'^[a-zA-Z0-9_-]{3,50}$'
    
    return bool(re.match(mac_pattern, device_id) or re.match(id_pattern, device_id))


def validate_ip_address(ip: str) -> bool:
    """
    IP 주소 검증 (IPv4, IPv6)
    
    Args:
        ip: IP 주소
    
    Returns:
        bool: 유효성 여부
    """
    # IPv4
    ipv4_pattern = r'^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}$'
    
    # IPv6 (간단한 패턴)
    ipv6_pattern = r'^(([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|::)$'
    
    return bool(re.match(ipv4_pattern, ip) or re.match(ipv6_pattern, ip))


def validate_mqtt_topic(topic: str) -> bool:
    """
    MQTT 토픽 검증
    
    Args:
        topic: MQTT 토픽
    
    Returns:
        bool: 유효성 여부
    """
    if not topic or len(topic) > 200:
        return False
    
    # MQTT 토픽은 알파벳, 숫자, /, _, - 허용
    pattern = r'^[a-zA-Z0-9/_-]+$'
    return bool(re.match(pattern, topic))


def validate_file_extension(filename: str, allowed_extensions: list[str]) -> bool:
    """
    파일 확장자 검증
    보안 가이드라인 6 준수: 화이트리스트 방식
    
    Args:
        filename: 파일명
        allowed_extensions: 허용된 확장자 리스트
    
    Returns:
        bool: 유효성 여부
    """
    if not filename or '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in [e.lower() for e in allowed_extensions]


def sanitize_filename(filename: str) -> str:
    """
    파일명 정제 (경로 공격 방지)
    보안 가이드라인 6 준수: ../ 경로 공격 방지
    
    Args:
        filename: 원본 파일명
    
    Returns:
        str: 정제된 파일명
    """
    # 경로 구분자 제거
    filename = filename.replace('/', '_').replace('\\', '_')
    
    # 특수문자 제거 (알파벳, 숫자, ., -, _ 만 허용)
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    
    # 연속된 점 제거
    filename = re.sub(r'\.{2,}', '.', filename)
    
    return filename


def validate_range(value: int, min_val: int, max_val: int) -> bool:
    """
    숫자 범위 검증
    
    Args:
        value: 검증할 값
        min_val: 최소값
        max_val: 최대값
    
    Returns:
        bool: 범위 내 여부
    """
    return min_val <= value <= max_val

