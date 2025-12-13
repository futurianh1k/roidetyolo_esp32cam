-- Migration: 002_create_alarm_history
-- Description: 알람 발송 이력 테이블 생성
-- Date: 2024
--
-- 사용법 (MySQL CLI):
--   mysql -u <user> -p <database> < scripts/migrations/002_create_alarm_history.sql

-- alarm_history 테이블 생성
CREATE TABLE IF NOT EXISTS alarm_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id INT NOT NULL COMMENT '장비 ID',
    
    -- 알람 정보
    alarm_type VARCHAR(20) NOT NULL COMMENT '알람 타입: sound(사운드), text(TTS), recorded(녹음)',
    alarm_subtype VARCHAR(50) COMMENT '서브타입: beep, alert, emergency 등',
    content TEXT COMMENT 'TTS 텍스트 또는 파일 경로',
    
    -- 트리거 정보
    triggered_by VARCHAR(20) NOT NULL DEFAULT 'system' COMMENT '트리거 주체: system, admin, user, schedule',
    triggered_user_id INT COMMENT '트리거한 사용자 ID (사용자가 트리거한 경우)',
    
    -- 메타데이터
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성 시간',
    parameters TEXT COMMENT 'JSON 형태의 추가 파라미터',
    
    -- 상태
    status VARCHAR(20) DEFAULT 'sent' COMMENT '상태: sent, delivered, failed',
    
    -- 인덱스
    INDEX idx_device_id (device_id),
    INDEX idx_alarm_type (alarm_type),
    INDEX idx_triggered_by (triggered_by),
    INDEX idx_created_at (created_at),
    
    -- 외래키
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    FOREIGN KEY (triggered_user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='알람 발송 이력';

-- 확인
SELECT 
    TABLE_NAME,
    TABLE_COMMENT
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME = 'alarm_history';
