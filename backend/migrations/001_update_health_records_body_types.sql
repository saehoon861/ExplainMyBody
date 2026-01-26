-- 데이터베이스 마이그레이션: health_records 테이블 업데이트
-- body_type을 body_type1, body_type2로 분리

-- 1. 새 컬럼 추가
ALTER TABLE health_records 
ADD COLUMN body_type1 VARCHAR(100),
ADD COLUMN body_type2 VARCHAR(100);

-- 2. 기존 body_type 데이터를 body_type1으로 복사 (있다면)
UPDATE health_records 
SET body_type1 = body_type 
WHERE body_type IS NOT NULL;

-- 3. 기존 body_type 컬럼 삭제
ALTER TABLE health_records 
DROP COLUMN body_type;

-- 변경 확인
SELECT id, user_id, source, body_type1, body_type2, measured_at, created_at 
FROM health_records 
ORDER BY created_at DESC 
LIMIT 5;
