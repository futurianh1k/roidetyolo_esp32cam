-- Phase 3 데이터베이스 마이그레이션 스크립트
-- ASR 결과 및 응급 상황 알림 테이블 생성
-- 
-- 사용법:
--   MySQL: mysql -u [username] -p [database_name] < phase3_migration.sql
--   또는 MySQL Workbench에서 실행

-- ============================================
-- 1. ASR 결과 테이블 생성
-- ============================================
CREATE TABLE IF NOT EXISTS asr_results (
    id INTEGER AUTO_INCREMENT PRIMARY KEY,
    device_id INTEGER NOT NULL,
    session_id VARCHAR(100) NOT NULL,
    text TEXT NOT NULL,
    timestamp VARCHAR(50) NOT NULL,
    duration FLOAT NOT NULL,
    is_emergency BOOLEAN NOT NULL DEFAULT FALSE,
    emergency_keywords TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    INDEX idx_device_id (device_id),
    INDEX idx_session_id (session_id),
    INDEX idx_is_emergency (is_emergency),
    INDEX idx_created_at (created_at),
    INDEX idx_device_created (device_id, created_at),
    INDEX idx_emergency_created (is_emergency, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 2. 응급 상황 알림 테이블 생성
-- ============================================
CREATE TABLE IF NOT EXISTS emergency_alerts (
    id INTEGER AUTO_INCREMENT PRIMARY KEY,
    device_id INTEGER NOT NULL,
    asr_result_id INTEGER NULL,
    recognized_text TEXT NOT NULL,
    emergency_keywords TEXT NOT NULL,
    priority ENUM('low', 'medium', 'high', 'critical') NOT NULL DEFAULT 'medium',
    status ENUM('pending', 'sent', 'failed', 'acknowledged') NOT NULL DEFAULT 'pending',
    api_endpoint VARCHAR(255) NULL,
    api_response TEXT NULL,
    sent_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP NULL,
    acknowledged_by INTEGER NULL,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    FOREIGN KEY (asr_result_id) REFERENCES asr_results(id) ON DELETE SET NULL,
    FOREIGN KEY (acknowledged_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_device_id (device_id),
    INDEX idx_asr_result_id (asr_result_id),
    INDEX idx_priority (priority),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_device_priority_created (device_id, priority, created_at),
    INDEX idx_status_created (status, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 마이그레이션 완료
-- ============================================
-- 테이블 생성 확인:
--   SHOW TABLES LIKE 'asr_results';
--   SHOW TABLES LIKE 'emergency_alerts';
-- 
-- 테이블 구조 확인:
--   DESCRIBE asr_results;
--   DESCRIBE emergency_alerts;

