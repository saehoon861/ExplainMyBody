-- 전체 DB 마이그레이션: pgvector, 테이블 이름 변경, 새 컬럼 추가
-- 실행: psql -U postgres -d explainmybody -h localhost -f migrations/002_add_pgvector_and_embeddings.sql

-- ============================================================================
-- 1. pgvector 확장 설치
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- 2. user_goals → user_details 테이블 이름 변경 및 컬럼 추가
-- ============================================================================

-- 2.1 테이블 이름 변경
ALTER TABLE IF EXISTS user_goals RENAME TO user_details;

-- 2.2 새 컬럼 추가
ALTER TABLE user_details 
ADD COLUMN IF NOT EXISTS preferences TEXT,
ADD COLUMN IF NOT EXISTS health_specifics TEXT,
ADD COLUMN IF NOT EXISTS is_active INTEGER DEFAULT 1;

-- 2.3 weekly_plan 컬럼 제거 (WeeklyPlan 테이블로 분리)
ALTER TABLE user_details 
DROP COLUMN IF EXISTS weekly_plan;

-- 2.4 인덱스 이름 변경
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_user_goals_id') THEN
        ALTER INDEX ix_user_goals_id RENAME TO ix_user_details_id;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_user_goals_user_id') THEN
        ALTER INDEX ix_user_goals_user_id RENAME TO ix_user_details_user_id;
    END IF;
END $$;

-- ============================================================================
-- 3. analysis_reports → inbody_analysis_reports 테이블 이름 변경
-- ============================================================================

-- 3.1 테이블 이름 변경
ALTER TABLE IF EXISTS analysis_reports RENAME TO inbody_analysis_reports;

-- 3.2 embedding_1536을 Text에서 Vector(1536)으로 변경
-- (기존 데이터가 NULL이거나 없으면 그냥 타입만 변경)
ALTER TABLE inbody_analysis_reports 
ALTER COLUMN embedding_1536 TYPE vector(1536) USING 
    CASE 
        WHEN embedding_1536 IS NULL THEN NULL
        ELSE embedding_1536::vector(1536)
    END;

-- 3.3 embedding_1024 필드 추가 (Ollama bge-m3)
ALTER TABLE inbody_analysis_reports 
ADD COLUMN IF NOT EXISTS embedding_1024 vector(1024);

-- 3.4 인덱스 이름 변경
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_analysis_reports_id') THEN
        ALTER INDEX ix_analysis_reports_id RENAME TO ix_inbody_analysis_reports_id;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_analysis_reports_user_id') THEN
        ALTER INDEX ix_analysis_reports_user_id RENAME TO ix_inbody_analysis_reports_user_id;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_analysis_reports_record_id') THEN
        ALTER INDEX ix_analysis_reports_record_id RENAME TO ix_inbody_analysis_reports_record_id;
    END IF;
END $$;

-- 3.5 pgvector HNSW 인덱스 생성 (빠른 유사도 검색)
CREATE INDEX IF NOT EXISTS idx_inbody_analysis_reports_embedding_1536_hnsw
ON inbody_analysis_reports USING hnsw (embedding_1536 vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_inbody_analysis_reports_embedding_1024_hnsw
ON inbody_analysis_reports USING hnsw (embedding_1024 vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- ============================================================================
-- 4. health_records 테이블 수정
-- ============================================================================

-- 4.1 measurements: JSON → JSONB 변경
ALTER TABLE health_records 
ALTER COLUMN measurements TYPE JSONB USING measurements::JSONB;

-- 4.2 body_type1, body_type2 컬럼 제거 (measurements JSONB 내부로 이동)
-- 먼저 기존 데이터를 measurements에 통합
UPDATE health_records
SET measurements = measurements || 
    jsonb_build_object(
        'body_type1', body_type1,
        'body_type2', body_type2
    )
WHERE body_type1 IS NOT NULL OR body_type2 IS NOT NULL;

-- 컬럼 제거
ALTER TABLE health_records 
DROP COLUMN IF EXISTS body_type1,
DROP COLUMN IF EXISTS body_type2;

-- 4.3 created_at에 NOT NULL 제약조건 추가
ALTER TABLE health_records 
ALTER COLUMN created_at SET NOT NULL;

-- ============================================================================
-- 5. users 테이블 수정
-- ============================================================================

-- 5.1 username에 UNIQUE 제약조건 추가
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'users_username_key'
    ) THEN
        ALTER TABLE users ADD CONSTRAINT users_username_key UNIQUE (username);
    END IF;
END $$;

-- 5.2 created_at에 NOT NULL 제약조건 추가
ALTER TABLE users 
ALTER COLUMN created_at SET NOT NULL;

-- ============================================================================
-- 6. weekly_plans 테이블 생성
-- ============================================================================

CREATE TABLE IF NOT EXISTS weekly_plans (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    week_number INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    plan_data JSONB NOT NULL,
    model_version VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6.1 weekly_plans 인덱스
CREATE INDEX IF NOT EXISTS idx_weekly_plans_user_id ON weekly_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_weekly_plans_user_week ON weekly_plans(user_id, week_number);

-- ============================================================================
-- 완료 메시지
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Migration 002 completed successfully!';
    RAISE NOTICE '========================================';
    RAISE NOTICE '';
    RAISE NOTICE '✅ 1. pgvector extension installed';
    RAISE NOTICE '✅ 2. user_goals → user_details (renamed)';
    RAISE NOTICE '   - Added: preferences, health_specifics, is_active';
    RAISE NOTICE '   - Removed: weekly_plan';
    RAISE NOTICE '✅ 3. analysis_reports → inbody_analysis_reports (renamed)';
    RAISE NOTICE '   - embedding_1536: Text → vector(1536)';
    RAISE NOTICE '   - embedding_1024: vector(1024) added';
    RAISE NOTICE '   - HNSW indexes created';
    RAISE NOTICE '✅ 4. health_records updated';
    RAISE NOTICE '   - measurements: JSON → JSONB';
    RAISE NOTICE '   - body_type1, body_type2 moved to measurements';
    RAISE NOTICE '   - created_at: NOT NULL';
    RAISE NOTICE '✅ 5. users updated';
    RAISE NOTICE '   - username: UNIQUE constraint added';
    RAISE NOTICE '   - created_at: NOT NULL';
    RAISE NOTICE '✅ 6. weekly_plans table created';
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
END $$;
