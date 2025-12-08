"""
비밀번호 보안 처리
보안 가이드라인 1-1 준수: BCrypt 해싱
"""
from passlib.context import CryptContext

# BCrypt 컨텍스트 (rounds=12로 설정)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    비밀번호 검증
    
    Args:
        plain_password: 평문 비밀번호
        hashed_password: 해시된 비밀번호
    
    Returns:
        bool: 비밀번호 일치 여부
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    비밀번호 해시 생성
    
    Args:
        password: 평문 비밀번호
    
    Returns:
        str: BCrypt 해시된 비밀번호
    """
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    비밀번호 강도 검증
    
    Args:
        password: 검증할 비밀번호
    
    Returns:
        tuple[bool, str]: (유효성 여부, 오류 메시지)
    """
    if len(password) < 8:
        return False, "비밀번호는 최소 8자 이상이어야 합니다"
    
    if len(password) > 128:
        return False, "비밀번호는 최대 128자까지 가능합니다"
    
    # 최소 하나의 대문자, 소문자, 숫자 포함 체크
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    if not (has_upper and has_lower and has_digit):
        return False, "비밀번호는 대문자, 소문자, 숫자를 각각 최소 1개 포함해야 합니다"
    
    return True, ""

