-- ============================================================
-- CoreS3 Management System - Database Initialization
-- ============================================================

-- 기본 테이블 생성은 SQLAlchemy가 자동으로 처리합니다.
-- 이 파일은 초기 데이터나 추가 설정을 위해 사용됩니다.

-- 기본 관리자 계정 (비밀번호: admin123)
-- 실제 배포 시 변경 필수!
-- INSERT INTO users (username, email, hashed_password, is_active, is_admin)
-- VALUES ('admin', 'admin@example.com', '$2b$12$...', true, true)
-- ON DUPLICATE KEY UPDATE username = username;

-- 타임존 설정
SET time_zone = '+09:00';

-- 완료 메시지
SELECT 'Database initialized successfully!' AS message;
