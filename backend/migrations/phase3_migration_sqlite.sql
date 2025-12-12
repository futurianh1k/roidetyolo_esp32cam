-- Phase 3 데이터베이스 마이그레이션 스크립트 (SQLite 버전)
-- ASR 결과 및 응급 상황 알림 테이블 생성
-- 
-- 사용법:
--   sqlite3 [database_file] < phase3_migration_sqlite.sql
--   또는 sqlite3에서 .read phase3_migration_sqlite.sql

-- ============================================
-- 1. ASR 결과 테이블 생성
-- ============================================
CREATE TABLE IF NOT EXISTS asr_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    session_id VARCHAR(100) NOT NULL,
    text TEXT NOT NULL,
    timestamp VARCHAR(50) NOT NULL,
    duration REAL NOT NULL,
    is_emergency INTEGER NOT NULL DEFAULT 0,
    emergency_keywords TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_asr_results_device_id ON asr_results(device_id);
CREATE INDEX IF NOT EXISTS idx_asr_results_session_id ON asr_results(session_id);
CREATE INDEX IF NOT EXISTS idx_asr_results_is_emergency ON asr_results(is_emergency);
CREATE INDEX IF NOT EXISTS idx_asr_results_created_at ON asr_results(created_at);
CREATE INDEX IF NOT EXISTS idx_device_created ON asr_results(device_id, created_at);
CREATE INDEX IF NOT EXISTS idx_emergency_created ON asr_results(is_emergency, created_at);

-- ============================================
-- 2. 응급 상황 알림 테이블 생성
-- ============================================
CREATE TABLE IF NOT EXISTS emergency_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    asr_result_id INTEGER NULL,
    recognized_text TEXT NOT NULL,
    emergency_keywords TEXT NOT NULL,
    priority VARCHAR(20) NOT NULL DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high', 'critical')),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'sent', 'failed', 'acknowledged')),
    api_endpoint VARCHAR(255) NULL,
    api_response TEXT NULL,
    sent_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP NULL,
    acknowledged_by INTEGER NULL,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    FOREIGN KEY (asr_result_id) REFERENCES asr_results(id) ON DELETE SET NULL,
    FOREIGN KEY (acknowledged_by) REFERENCES users(id) ON DELETE SET NULL
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_emergency_alerts_device_id ON emergency_alerts(device_id);
CREATE INDEX IF NOT EXISTS idx_emergency_alerts_asr_result_id ON emergency_alerts(asr_result_id);
CREATE INDEX IF NOT EXISTS idx_emergency_alerts_priority ON emergency_alerts(priority);
CREATE INDEX IF NOT EXISTS idx_emergency_alerts_status ON emergency_alerts(status);
CREATE INDEX IF NOT EXISTS idx_emergency_alerts_created_at ON emergency_alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_device_priority_created ON emergency_alerts(device_id, priority, created_at);
CREATE INDEX IF NOT EXISTS idx_status_created ON emergency_alerts(status, created_at);

-- ============================================
-- 마이그레이션 완료
-- ============================================
-- 테이블 생성 확인:
--   .tables
-- 
-- 테이블 구조 확인:
--   .schema asr_results
--   .schema emergency_alerts

