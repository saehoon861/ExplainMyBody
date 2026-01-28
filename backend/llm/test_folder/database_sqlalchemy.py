"""
SQLAlchemy 기반 Database 클래스
기존 database.py와 동일한 인터페이스 제공
"""

import os
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from dotenv import load_dotenv

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError

from db_models import Base, User, UserGoal, HealthRecord, AnalysisReport

load_dotenv()


class DatabaseSQLAlchemy:
    """SQLAlchemy 기반 PostgreSQL 데이터베이스 관리 클래스"""

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
            self.connection_string = os.getenv(
                "DATABASE_URL",
                "postgresql://postgres:postgres@localhost:5432/explainmybody"
            )

        # SQLAlchemy Engine 생성
        self.engine = create_engine(
            self.connection_string,
            echo=False,  # SQL 로그 출력 (디버깅 시 True)
            pool_pre_ping=True,  # 연결 상태 확인
        )

        # Session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        # 데이터베이스 초기화
        self._init_database()

    @contextmanager
    def get_session(self) -> Session:
        """데이터베이스 세션 컨텍스트 매니저"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def _init_database(self):
        """데이터베이스 초기화 및 테이블 생성"""
        # pgvector extension 설치
        with self.engine.connect() as conn:
            try:
                conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                conn.commit()
                print("✅ pgvector extension 준비 완료")
            except Exception as e:
                print(f"⚠️  pgvector extension을 설치할 수 없습니다: {e}")

        # 모든 테이블 생성
        Base.metadata.create_all(self.engine)
        print("✅ PostgreSQL 데이터베이스 초기화 완료")

    # ================== User 관련 ==================

    def create_user(self, username: str, email: str) -> int:
        """새 사용자 생성"""
        with self.get_session() as session:
            user = User(username=username, email=email)
            session.add(user)
            session.flush()  # ID 생성을 위해 flush
            return user.id

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """이메일로 사용자 조회"""
        with self.get_session() as session:
            stmt = select(User).where(User.email == email)
            user = session.scalar(stmt)

            if user:
                return {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "created_at": user.created_at
                }
            return None

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """ID로 사용자 조회"""
        with self.get_session() as session:
            user = session.get(User, user_id)

            if user:
                return {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "created_at": user.created_at
                }
            return None

    # ================== Health Records 관련 ==================

    def save_health_record(
        self,
        user_id: int,
        measurements: Dict[str, Any],
        source: str = "manual",
        measured_at: Optional[str] = None
    ) -> int:
        """건강 기록 저장"""
        with self.get_session() as session:
            record = HealthRecord(
                user_id=user_id,
                source=source,
                measurements=measurements
            )

            if measured_at:
                from datetime import datetime
                record.measured_at = datetime.fromisoformat(measured_at)

            session.add(record)
            session.flush()
            return record.id

    def get_health_record(self, record_id: int) -> Optional[Dict]:
        """건강 기록 조회"""
        with self.get_session() as session:
            record = session.get(HealthRecord, record_id)

            if record:
                return {
                    "id": record.id,
                    "user_id": record.user_id,
                    "source": record.source,
                    "measured_at": record.measured_at,
                    "measurements": record.measurements,
                    "created_at": record.created_at
                }
            return None

    def get_user_health_records(self, user_id: int, limit: int = 10) -> List[Dict]:
        """사용자의 건강 기록 목록 조회"""
        with self.get_session() as session:
            stmt = (
                select(HealthRecord)
                .where(HealthRecord.user_id == user_id)
                .order_by(HealthRecord.measured_at.desc())
                .limit(limit)
            )
            records = session.scalars(stmt).all()

            return [
                {
                    "id": r.id,
                    "user_id": r.user_id,
                    "source": r.source,
                    "measured_at": r.measured_at,
                    "measurements": r.measurements,
                    "created_at": r.created_at
                }
                for r in records
            ]

    def search_health_records_by_measurement(
        self,
        user_id: int,
        key: str,
        value: Any
    ) -> List[Dict]:
        """JSONB 필드 내 특정 값으로 검색"""
        with self.get_session() as session:
            # JSONB 쿼리: measurements->>'key' = value
            stmt = (
                select(HealthRecord)
                .where(HealthRecord.user_id == user_id)
                .where(HealthRecord.measurements[key].astext == str(value))
                .order_by(HealthRecord.measured_at.desc())
            )
            records = session.scalars(stmt).all()

            return [
                {
                    "id": r.id,
                    "user_id": r.user_id,
                    "source": r.source,
                    "measured_at": r.measured_at,
                    "measurements": r.measurements,
                    "created_at": r.created_at
                }
                for r in records
            ]

    # ================== Analysis Reports 관련 ==================

    def save_analysis_report(
        self,
        user_id: int,
        record_id: int,
        llm_output: str,
        model_version: str
    ) -> int:
        """분석 리포트 저장"""
        with self.get_session() as session:
            report = AnalysisReport(
                user_id=user_id,
                record_id=record_id,
                llm_output=llm_output,
                model_version=model_version
            )
            session.add(report)
            session.flush()
            return report.id

    def get_analysis_report(self, report_id: int) -> Optional[Dict]:
        """분석 리포트 조회"""
        with self.get_session() as session:
            report = session.get(AnalysisReport, report_id)

            if report:
                return {
                    "id": report.id,
                    "user_id": report.user_id,
                    "record_id": report.record_id,
                    "llm_output": report.llm_output,
                    "model_version": report.model_version,
                    "generated_at": report.generated_at
                }
            return None

    def get_report_by_record_id(self, record_id: int) -> Optional[Dict]:
        """health_record_id로 리포트 조회"""
        with self.get_session() as session:
            stmt = (
                select(AnalysisReport)
                .where(AnalysisReport.record_id == record_id)
                .order_by(AnalysisReport.generated_at.desc())
                .limit(1)
            )
            report = session.scalar(stmt)

            if report:
                return {
                    "id": report.id,
                    "user_id": report.user_id,
                    "record_id": report.record_id,
                    "llm_output": report.llm_output,
                    "model_version": report.model_version,
                    "generated_at": report.generated_at
                }
            return None

    # ================== User Goals 관련 ==================

    def create_user_goal(self, user_id: int, goal_type: str) -> int:
        """사용자 목표 생성"""
        with self.get_session() as session:
            goal = UserGoal(user_id=user_id, goal_type=goal_type)
            session.add(goal)
            session.flush()
            return goal.id

    def get_active_user_goals(self, user_id: int) -> List[Dict]:
        """활성 사용자 목표 조회"""
        with self.get_session() as session:
            stmt = (
                select(UserGoal)
                .where(UserGoal.user_id == user_id)
                .where(UserGoal.ended_at.is_(None))
            )
            goals = session.scalars(stmt).all()

            return [
                {
                    "id": g.id,
                    "user_id": g.user_id,
                    "goal_type": g.goal_type,
                    "started_at": g.started_at,
                    "ended_at": g.ended_at
                }
                for g in goals
            ]

    # ================== 유틸리티 ==================

    def test_connection(self) -> bool:
        """데이터베이스 연결 테스트"""
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
                return True
        except Exception as e:
            print(f"❌ 데이터베이스 연결 실패: {e}")
            return False

    def get_user_statistics(self, user_id: int) -> Dict[str, int]:
        """사용자 통계 조회"""
        with self.get_session() as session:
            # 건강 기록 수
            record_count = session.scalar(
                select(func.count(HealthRecord.id))
                .where(HealthRecord.user_id == user_id)
            )

            # 분석 리포트 수
            report_count = session.scalar(
                select(func.count(AnalysisReport.id))
                .where(AnalysisReport.user_id == user_id)
            )

            return {
                "total_records": record_count,
                "total_reports": report_count
            }

    # ================== ORM 기능 (추가) ==================

    def get_user_with_records(self, user_id: int) -> Optional[User]:
        """
        Relationship을 활용한 사용자 + 건강 기록 조회
        ORM의 장점을 활용하는 예시
        """
        with self.get_session() as session:
            user = session.get(User, user_id)
            if user:
                # Lazy loading 방지 - eager load
                session.refresh(user)  # health_records 로드
                return user
            return None

    def get_user_latest_report(self, user_id: int) -> Optional[AnalysisReport]:
        """사용자의 최신 리포트 조회 (ORM 방식)"""
        with self.get_session() as session:
            stmt = (
                select(AnalysisReport)
                .where(AnalysisReport.user_id == user_id)
                .order_by(AnalysisReport.generated_at.desc())
                .limit(1)
            )
            return session.scalar(stmt)
