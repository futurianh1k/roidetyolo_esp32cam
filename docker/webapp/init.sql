-- ============================================================
-- CoreS3 Management System - Database Initialization
-- ============================================================

-- 타임존 설정
SET time_zone = '+09:00';

-- 문자셋 설정
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- ============================================================
-- 테이블 생성은 SQLAlchemy가 자동으로 처리합니다.
-- 이 파일은 MySQL 초기 설정만 담당합니다.
-- ============================================================

-- 권한 설정 (필요 시)
-- GRANT ALL PRIVILEGES ON cores3_db.* TO 'cores3user'@'%';
-- FLUSH PRIVILEGES;

-- 완료 메시지
SELECT 'MySQL initialization complete. Tables will be created by SQLAlchemy.' AS message;
