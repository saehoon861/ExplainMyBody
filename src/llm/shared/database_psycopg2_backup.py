"""
Database Schema and Connection Management
PostgreSQL를 사용한 데이터베이스 관리 (pgvector 지원 준비)
"""

import psycopg2
import psycopg2.extras
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()


class Database:
    """PostgreSQL 데이터베이스 관리 클래스"""

    def __init__(self, connection_string: Optional[str] = None):
        """
        Args:
            connection_string: PostgreSQL 연결 문자열
                예: "postgresql://user:password@localhost:5432/dbname"
                None인 경우 환경변수에서 읽음
        """
        if connection_string:
            self.connection_string = connection_string
        else:
            # 환경변수에서 연결 정보 읽기
            self.connection_string = os.getenv(
                "DATABASE_URL",
                "postgresql://postgres:postgres@localhost:5432/explainmybody"
            )

        self._init_database()

    @contextmanager
    def get_connection(self):
        """데이터베이스 연결 컨텍스트 매니저"""
        conn = psycopg2.connect(self.connection_string)
        conn.set_session(autocommit=False)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _init_database(self):
        """데이터베이스 초기화 및 테이블 생성"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # pgvector extension 설치 (있으면 무시)
            try:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
                print("✅ pgvector extension 준비 완료")
            except Exception as e:
                print(f"⚠️  pgvector extension을 설치할 수 없습니다: {e}")
                print("   (나중에 pgvector가 필요할 때 수동으로 설치하세요)")

            # 1. users 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 2. user_goals 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_goals (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    goal_type VARCHAR(255),
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ended_at TIMESTAMP
                )
            """)

            # 3. health_records 테이블 (JSONB 사용)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS health_records (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    source VARCHAR(100) DEFAULT 'manual',
                    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    measurements JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 4. analysis_reports 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_reports (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    record_id INTEGER NOT NULL REFERENCES health_records(id) ON DELETE CASCADE,
                    llm_output TEXT NOT NULL,
                    model_version VARCHAR(100),
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 인덱스 생성
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_health_records_user_measured
                ON health_records(user_id, measured_at DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_health_records_user
                ON health_records(user_id)
            """)

            # JSONB 필드에 GIN 인덱스 생성 (검색 성능 향상)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_health_records_measurements_gin
                ON health_records USING GIN (measurements)
            """)

            print("✅ PostgreSQL 데이터베이스 초기화 완료")

    # ================== User 관련 ==================

    def create_user(self, username: str, email: str) -> int:
        """새 사용자 생성"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, email) VALUES (%s, %s) RETURNING id",
                (username, email)
            )
            user_id = cursor.fetchone()[0]
            return user_id

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """이메일로 사용자 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """ID로 사용자 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # ================== Health Records 관련 ==================

    def save_health_record(
        self,
        user_id: int,
        measurements: Dict[str, Any],
        source: str = "manual",
        measured_at: Optional[str] = None
    ) -> int:
        """건강 기록 저장"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # JSONB로 저장
            measurements_json = json.dumps(measurements, ensure_ascii=False)

            if measured_at:
                cursor.execute(
                    """INSERT INTO health_records
                       (user_id, source, measured_at, measurements)
                       VALUES (%s, %s, %s, %s::jsonb)
                       RETURNING id""",
                    (user_id, source, measured_at, measurements_json)
                )
            else:
                cursor.execute(
                    """INSERT INTO health_records
                       (user_id, source, measurements)
                       VALUES (%s, %s, %s::jsonb)
                       RETURNING id""",
                    (user_id, source, measurements_json)
                )

            record_id = cursor.fetchone()[0]
            return record_id

    def get_health_record(self, record_id: int) -> Optional[Dict]:
        """건강 기록 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("SELECT * FROM health_records WHERE id = %s", (record_id,))
            row = cursor.fetchone()

            if row:
                record = dict(row)
                # JSONB는 이미 Python dict로 변환됨
                return record
            return None

    def get_user_health_records(self, user_id: int, limit: int = 10) -> List[Dict]:
        """사용자의 건강 기록 목록 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(
                """SELECT * FROM health_records
                   WHERE user_id = %s
                   ORDER BY measured_at DESC
                   LIMIT %s""",
                (user_id, limit)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def search_health_records_by_measurement(
        self,
        user_id: int,
        key: str,
        value: Any
    ) -> List[Dict]:
        """JSONB 필드 내 특정 값으로 검색 (PostgreSQL JSONB 기능 활용)

        예: search_health_records_by_measurement(1, 'stage2_근육보정체형', '근육형')
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(
                """SELECT * FROM health_records
                   WHERE user_id = %s
                   AND measurements->>%s = %s
                   ORDER BY measured_at DESC""",
                (user_id, key, str(value))
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    # ================== Analysis Reports 관련 ==================

    def save_analysis_report(
        self,
        user_id: int,
        record_id: int,
        llm_output: str,
        model_version: str
    ) -> int:
        """분석 리포트 저장"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO analysis_reports
                   (user_id, record_id, llm_output, model_version)
                   VALUES (%s, %s, %s, %s)
                   RETURNING id""",
                (user_id, record_id, llm_output, model_version)
            )
            report_id = cursor.fetchone()[0]
            return report_id

    def get_analysis_report(self, report_id: int) -> Optional[Dict]:
        """분석 리포트 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("SELECT * FROM analysis_reports WHERE id = %s", (report_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_report_by_record_id(self, record_id: int) -> Optional[Dict]:
        """health_record_id로 리포트 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(
                """SELECT * FROM analysis_reports
                   WHERE record_id = %s
                   ORDER BY generated_at DESC
                   LIMIT 1""",
                (record_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    # ================== User Goals 관련 ==================

    def create_user_goal(self, user_id: int, goal_type: str) -> int:
        """사용자 목표 생성"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO user_goals (user_id, goal_type) VALUES (%s, %s) RETURNING id",
                (user_id, goal_type)
            )
            goal_id = cursor.fetchone()[0]
            return goal_id

    def get_active_user_goals(self, user_id: int) -> List[Dict]:
        """활성 사용자 목표 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(
                "SELECT * FROM user_goals WHERE user_id = %s AND ended_at IS NULL",
                (user_id,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    # ================== 유틸리티 ==================

    def test_connection(self) -> bool:
        """데이터베이스 연결 테스트"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            print(f"❌ 데이터베이스 연결 실패: {e}")
            return False

    def get_user_statistics(self, user_id: int) -> Dict[str, int]:
        """사용자 통계 조회"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 건강 기록 수
            cursor.execute(
                "SELECT COUNT(*) FROM health_records WHERE user_id = %s",
                (user_id,)
            )
            record_count = cursor.fetchone()[0]

            # 분석 리포트 수
            cursor.execute(
                "SELECT COUNT(*) FROM analysis_reports WHERE user_id = %s",
                (user_id,)
            )
            report_count = cursor.fetchone()[0]

            return {
                "total_records": record_count,
                "total_reports": report_count
            }

