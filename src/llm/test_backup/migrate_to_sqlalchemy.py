#!/usr/bin/env python3
"""
기존 psycopg2 테이블을 SQLAlchemy + pgvector 스키마로 마이그레이션
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv
from shared.db_models import Base

load_dotenv()


def migrate_database():
    """데이터베이스 마이그레이션"""

    connection_string = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/explainmybody"
    )

    print("=" * 60)
    print("SQLAlchemy + pgvector 마이그레이션")
    print("=" * 60)
    print(f"\n📊 Database: {connection_string}")

    engine = create_engine(connection_string, echo=False)

    # 1. pgvector extension 활성화
    print("\n1️⃣  pgvector extension 활성화...")
    with engine.connect() as conn:
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
            print("  ✅ pgvector extension 활성화 완료")
        except Exception as e:
            print(f"  ⚠️  pgvector extension 활성화 실패: {e}")
            return False

    # 2. 기존 테이블 확인
    print("\n2️⃣  기존 테이블 확인...")
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    print(f"  기존 테이블: {existing_tables}")

    # 3. 테이블 업데이트 전략 선택
    print("\n3️⃣  마이그레이션 전략 선택:")
    print("  [1] 기존 테이블 유지하고 embedding 컬럼만 추가 (권장)")
    print("  [2] 모든 테이블 삭제 후 재생성 (데이터 손실)")
    print("  [3] 취소")

    choice = input("\n선택 (1-3): ").strip()

    if choice == "3":
        print("마이그레이션 취소됨")
        return False

    with engine.connect() as conn:
        if choice == "2":
            # 옵션 2: 모든 테이블 삭제 후 재생성
            print("\n⚠️  모든 테이블을 삭제하고 재생성합니다...")
            confirm = input("정말로 모든 데이터를 삭제하시겠습니까? (yes/no): ")
            if confirm.lower() != "yes":
                print("취소됨")
                return False

            print("  - 테이블 삭제 중...")
            Base.metadata.drop_all(bind=engine)
            print("  ✅ 기존 테이블 삭제 완료")

            print("  - 테이블 재생성 중...")
            Base.metadata.create_all(bind=engine)
            print("  ✅ 테이블 재생성 완료")

        else:  # 옵션 1 (기본)
            # health_records 테이블 컬럼명 변경
            print("\n  - health_records 테이블 컬럼명 변경...")
            try:
                columns = [col["name"] for col in inspector.get_columns("health_records")]
                if "measured_at" in columns and "record_date" not in columns:
                    conn.execute(text("ALTER TABLE health_records RENAME COLUMN measured_at TO record_date"))
                    conn.commit()
                    print("  ✅ measured_at -> record_date 변경 완료")
                else:
                    print("  ℹ️  record_date 컬럼이 이미 존재합니다")
            except Exception as e:
                print(f"  ⚠️  컬럼명 변경 실패: {e}")

            # analysis_reports 테이블 컬럼명 변경
            print("\n  - analysis_reports 테이블 컬럼명 변경...")
            try:
                columns = [col["name"] for col in inspector.get_columns("analysis_reports")]
                if "generated_at" in columns and "report_date" not in columns:
                    conn.execute(text("ALTER TABLE analysis_reports RENAME COLUMN generated_at TO report_date"))
                    conn.commit()
                    print("  ✅ generated_at -> report_date 변경 완료")
                else:
                    print("  ℹ️  report_date 컬럼이 이미 존재합니다")
            except Exception as e:
                print(f"  ⚠️  컬럼명 변경 실패: {e}")

            # analysis_reports에 embedding_1536 컬럼 추가 (또는 embedding 리네임)
            print("\n  - analysis_reports 테이블에 embedding_1536 컬럼 추가...")
            try:
                columns = [
                    col["name"]
                    for col in inspector.get_columns("analysis_reports")
                ]

                # 기존 embedding 컬럼이 있으면 embedding_1536으로 리네임
                if "embedding" in columns and "embedding_1536" not in columns:
                    conn.execute(
                        text(
                            "ALTER TABLE analysis_reports RENAME COLUMN embedding TO embedding_1536"
                        )
                    )
                    conn.commit()
                    print("  ✅ embedding → embedding_1536 변경 완료")
                elif "embedding_1536" not in columns:
                    conn.execute(
                        text(
                            "ALTER TABLE analysis_reports ADD COLUMN embedding_1536 vector(1536)"
                        )
                    )
                    conn.commit()
                    print("  ✅ embedding_1536 컬럼 추가 완료")
                else:
                    print("  ℹ️  embedding_1536 컬럼이 이미 존재합니다")
            except Exception as e:
                print(f"  ⚠️  embedding_1536 컬럼 추가 실패: {e}")

            # analysis_reports에 embedding_1024 컬럼 추가
            print("\n  - analysis_reports 테이블에 embedding_1024 컬럼 추가...")
            try:
                columns = [
                    col["name"]
                    for col in inspector.get_columns("analysis_reports")
                ]
                if "embedding_1024" not in columns:
                    conn.execute(
                        text(
                            "ALTER TABLE analysis_reports ADD COLUMN embedding_1024 vector(1024)"
                        )
                    )
                    conn.commit()
                    print("  ✅ embedding_1024 컬럼 추가 완료")
                else:
                    print("  ℹ️  embedding_1024 컬럼이 이미 존재합니다")
            except Exception as e:
                print(f"  ⚠️  embedding_1024 컬럼 추가 실패: {e}")

            # weekly_plans 테이블 생성 (없으면)
            print("\n  - weekly_plans 테이블 생성...")
            try:
                if "weekly_plans" not in existing_tables:
                    from shared.db_models import WeeklyPlan

                    WeeklyPlan.__table__.create(bind=engine)
                    print("  ✅ weekly_plans 테이블 생성 완료")
                else:
                    print("  ℹ️  weekly_plans 테이블이 이미 존재합니다")
            except Exception as e:
                print(f"  ⚠️  weekly_plans 테이블 생성 실패: {e}")

            # user_goals 테이블 업데이트 (JSONB 컬럼 추가)
            print("\n  - user_goals 테이블 업데이트...")
            try:
                columns = [col["name"] for col in inspector.get_columns("user_goals")]
                if "goal_data" not in columns:
                    # 기존 데이터를 goal_data JSONB로 마이그레이션
                    conn.execute(
                        text("ALTER TABLE user_goals ADD COLUMN goal_data JSONB")
                    )
                    conn.execute(
                        text("ALTER TABLE user_goals ADD COLUMN is_active INTEGER DEFAULT 1")
                    )
                    conn.commit()
                    print("  ✅ user_goals 테이블 업데이트 완료")
                else:
                    print("  ℹ️  user_goals 테이블이 이미 업데이트되어 있습니다")
            except Exception as e:
                print(f"  ⚠️  user_goals 테이블 업데이트 실패: {e}")

    # 4. 인덱스 생성
    print("\n4️⃣  Vector 인덱스 생성...")
    with engine.connect() as conn:
        try:
            # HNSW 인덱스 for embedding_1536 (OpenAI)
            conn.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS idx_analysis_reports_embedding_1536_hnsw
                    ON analysis_reports USING hnsw (embedding_1536 vector_cosine_ops)
                    WITH (m = 16, ef_construction = 64)
                    """
                )
            )
            conn.commit()
            print("  ✅ HNSW 인덱스 생성 완료 (embedding_1536)")
        except Exception as e:
            print(f"  ⚠️  embedding_1536 인덱스 생성 실패: {e}")
            print("     (embedding 데이터가 아직 없을 수 있습니다)")

        try:
            # HNSW 인덱스 for embedding_1024 (Ollama bge-m3)
            conn.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS idx_analysis_reports_embedding_1024_hnsw
                    ON analysis_reports USING hnsw (embedding_1024 vector_cosine_ops)
                    WITH (m = 16, ef_construction = 64)
                    """
                )
            )
            conn.commit()
            print("  ✅ HNSW 인덱스 생성 완료 (embedding_1024)")
        except Exception as e:
            print(f"  ⚠️  embedding_1024 인덱스 생성 실패: {e}")
            print("     (embedding 데이터가 아직 없을 수 있습니다)")

    # 5. 테이블 확인
    print("\n5️⃣  최종 테이블 구조 확인...")
    inspector = inspect(engine)
    for table in ["users", "health_records", "analysis_reports", "user_goals", "weekly_plans"]:
        if table in inspector.get_table_names():
            columns = inspector.get_columns(table)
            print(f"\n  📋 {table}:")
            for col in columns:
                col_type = str(col["type"])
                print(f"    - {col['name']}: {col_type}")

    print("\n" + "=" * 60)
    print("✅ 마이그레이션 완료!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)
