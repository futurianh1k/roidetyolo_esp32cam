-- Migration: 001_add_status_report_interval
-- Description: devices 테이블에 status_report_interval 컬럼 추가
-- Date: 2024
-- 
-- 사용법 (MySQL CLI):
--   mysql -u <user> -p <database> < scripts/migrations/001_add_status_report_interval.sql
--
-- 또는 MySQL Workbench에서 직접 실행

-- 컬럼이 없을 때만 추가 (MySQL 8.0+에서는 IF NOT EXISTS 지원 안함)
-- 먼저 존재 여부 확인 후 수동 실행 권장

-- 1. 컬럼 추가
ALTER TABLE devices 
ADD COLUMN status_report_interval INT NOT NULL DEFAULT 60 
COMMENT '상태 보고 주기 (초), 기본값 60초';

-- 2. 기존 데이터 업데이트 (필요시)
-- UPDATE devices SET status_report_interval = 60 WHERE status_report_interval IS NULL;

-- 확인
SELECT 
    COLUMN_NAME, 
    DATA_TYPE, 
    IS_NULLABLE, 
    COLUMN_DEFAULT, 
    COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'devices' 
  AND COLUMN_NAME = 'status_report_interval';
