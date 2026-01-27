"""
SQLAlchemy 기반 데이터베이스 관리 (pgvector 지원)
"""

import os
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from contextlib import contextmanager

from sqlalchemy import create_engine, text, func, desc
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import JSONB
from dotenv import load_dotenv

from shared.db_models import Base, User, HealthRecord, AnalysisReport, UserGoal, WeeklyPlan

load_dotenv()


class Database:
    """SQLAlchemy 기반 PostgreSQL 데이터베이스 관리 (pgvector 지원)"""

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
                "postgresql://postgres:postgres@localhost:5432/explainmybody",
            )

        # SQLAlchemy 엔진 생성
        self.engine = create_engine(
            self.connection_string,
            echo=False,  # SQL 로깅 (개발 시 True로 변경 가능)
            pool_pre_ping=True,  # 연결 유효성 검사
        )

        # 세션 팩토리
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
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
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
                print("✅ pgvector extension 활성화 완료")
            except Exception as e:
                print(f"⚠️  pgvector extension 설치 실패: {e}")

        # 모든 테이블 생성 (없으면 생성)
        Base.metadata.create_all(bind=self.engine)
        print("✅ SQLAlchemy 데이터베이스 초기화 완료")

        # 인덱스 생성 (pgvector용)
        self._create_vector_indexes()

    def _create_vector_indexes(self):
        """Vector 검색을 위한 인덱스 생성 (1536D + 1024D)"""
        with self.engine.connect() as conn:
            try:
                # HNSW 인덱스 생성 for embedding_1536 (OpenAI)
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
                print("✅ pgvector HNSW 인덱스 생성 완료 (1536D)")
            except Exception as e:
                print(f"⚠️  Vector 인덱스 (1536D) 생성 실패: {e}")

            try:
                # HNSW 인덱스 생성 for embedding_1024 (Ollama bge-m3)
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
                print("✅ pgvector HNSW 인덱스 생성 완료 (1024D)")
            except Exception as e:
                print(f"⚠️  Vector 인덱스 (1024D) 생성 실패: {e}")

    # ================== User 관련 ==================

    def create_user(self, username: str, email: str) -> int:
        """새 사용자 생성"""
        with self.get_session() as session:
            user = User(username=username, email=email)
            session.add(user)
            session.flush()
            return user.id

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """이메일로 사용자 조회"""
        with self.get_session() as session:
            user = session.query(User).filter(User.email == email).first()
            if user:
                return {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "created_at": user.created_at,
                }
            return None

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """ID로 사용자 조회"""
        with self.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                return {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "created_at": user.created_at,
                }
            return None

    # ================== Health Records 관련 ==================

    def save_health_record(
        self,
        user_id: int,
        measurements: Dict[str, Any],
        source: str = "manual",
        measured_at: Optional[datetime] = None,
    ) -> int:
        """건강 기록 저장"""
        with self.get_session() as session:
            record = HealthRecord(
                user_id=user_id,
                measurements=measurements,
                source=source,
                record_date=measured_at or datetime.utcnow(),
            )
            session.add(record)
            session.flush()
            return record.id

    def get_health_record(self, record_id: int) -> Optional[Dict]:
        """건강 기록 조회"""
        with self.get_session() as session:
            record = (
                session.query(HealthRecord).filter(HealthRecord.id == record_id).first()
            )
            if record:
                return {
                    "id": record.id,
                    "user_id": record.user_id,
                    "record_date": record.record_date,
                    "measurements": record.measurements,
                    "source": record.source,
                }
            return None

    def get_user_health_records(self, user_id: int, limit: int = 10) -> List[Dict]:
        """사용자의 건강 기록 목록 조회"""
        with self.get_session() as session:
            records = (
                session.query(HealthRecord)
                .filter(HealthRecord.user_id == user_id)
                .order_by(desc(HealthRecord.record_date))
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": r.id,
                    "user_id": r.user_id,
                    "record_date": r.record_date,
                    "measurements": r.measurements,
                    "source": r.source,
                }
                for r in records
            ]

    def search_health_records_by_measurement(
        self, user_id: int, key: str, value: Any
    ) -> List[Dict]:
        """JSONB 필드 내 특정 값으로 검색"""
        with self.get_session() as session:
            records = (
                session.query(HealthRecord)
                .filter(
                    HealthRecord.user_id == user_id,
                    HealthRecord.measurements[key].astext == str(value),
                )
                .order_by(desc(HealthRecord.record_date))
                .all()
            )
            return [
                {
                    "id": r.id,
                    "user_id": r.user_id,
                    "record_date": r.record_date,
                    "measurements": r.measurements,
                    "source": r.source,
                }
                for r in records
            ]

    # ================== Analysis Reports 관련 ==================

    def save_analysis_report(
        self,
        user_id: int,
        record_id: int,
        llm_output: str,
        model_version: str,
        embedding_1536: Optional[List[float]] = None,
        embedding_1024: Optional[List[float]] = None,
    ) -> int:
        """분석 리포트 저장 (임베딩 포함)"""
        with self.get_session() as session:
            report = AnalysisReport(
                user_id=user_id,
                record_id=record_id,
                llm_output=llm_output,
                model_version=model_version,
                embedding_1536=embedding_1536,
                embedding_1024=embedding_1024,
            )
            session.add(report)
            session.flush()
            return report.id

    def update_analysis_embedding(
        self,
        report_id: int,
        embedding_1536: Optional[List[float]] = None,
        embedding_1024: Optional[List[float]] = None,
    ) -> bool:
        """분석 리포트에 임베딩 추가/업데이트"""
        with self.get_session() as session:
            report = (
                session.query(AnalysisReport)
                .filter(AnalysisReport.id == report_id)
                .first()
            )
            if report:
                if embedding_1536 is not None:
                    report.embedding_1536 = embedding_1536
                if embedding_1024 is not None:
                    report.embedding_1024 = embedding_1024
                return True
            return False

    def get_analysis_report(self, report_id: int) -> Optional[Dict]:
        """분석 리포트 조회"""
        with self.get_session() as session:
            report = (
                session.query(AnalysisReport)
                .filter(AnalysisReport.id == report_id)
                .first()
            )
            if report:
                return {
                    "id": report.id,
                    "user_id": report.user_id,
                    "record_id": report.record_id,
                    "report_date": report.report_date,
                    "llm_output": report.llm_output,
                    "model_version": report.model_version,
                    "embedding_1536": report.embedding_1536,
                    "embedding_1024": report.embedding_1024,
                }
            return None

    def get_report_by_record_id(self, record_id: int) -> Optional[Dict]:
        """health_record_id로 리포트 조회"""
        with self.get_session() as session:
            report = (
                session.query(AnalysisReport)
                .filter(AnalysisReport.record_id == record_id)
                .order_by(desc(AnalysisReport.report_date))
                .first()
            )
            if report:
                return {
                    "id": report.id,
                    "user_id": report.user_id,
                    "record_id": report.record_id,
                    "report_date": report.report_date,
                    "llm_output": report.llm_output,
                    "model_version": report.model_version,
                    "embedding_1536": report.embedding_1536,
                    "embedding_1024": report.embedding_1024,
                }
            return None

    def get_user_analysis_reports(
        self, user_id: int, limit: int = 10
    ) -> List[Dict]:
        """사용자의 분석 리포트 목록 조회"""
        with self.get_session() as session:
            reports = (
                session.query(AnalysisReport)
                .filter(AnalysisReport.user_id == user_id)
                .order_by(desc(AnalysisReport.report_date))
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": r.id,
                    "user_id": r.user_id,
                    "record_id": r.record_id,
                    "report_date": r.report_date,
                    "llm_output": r.llm_output,
                    "model_version": r.model_version,
                    "has_embedding_1536": r.embedding_1536 is not None,
                    "has_embedding_1024": r.embedding_1024 is not None,
                }
                for r in reports
            ]

    def search_similar_analyses(
        self,
        user_id: int,
        query_embedding: List[float],
        top_k: int = 6,
        embedding_dim: int = 1536,
        rerank: bool = True,
    ) -> List[Dict]:
        """
        Vector 유사도 검색 + Reranking (pgvector)

        Args:
            user_id: 사용자 ID
            query_embedding: 쿼리 임베딩 벡터
            top_k: 반환할 결과 수
            embedding_dim: 임베딩 차원 (1536 or 1024)
            rerank: 시간 가중치 reranking 적용 여부

        Returns:
            유사도 + 시간 가중치가 반영된 분석 리포트 리스트
        """
        from datetime import datetime
        import math

        with self.get_session() as session:
            # 임베딩 차원에 따라 컬럼 선택
            if embedding_dim == 1536:
                embedding_col = AnalysisReport.embedding_1536
            elif embedding_dim == 1024:
                embedding_col = AnalysisReport.embedding_1024
            else:
                raise ValueError(f"지원하지 않는 임베딩 차원: {embedding_dim}")

            # pgvector의 cosine distance 사용 (1 - cosine similarity)
            # 후보를 더 많이 가져와서 reranking (top_k * 2)
            candidate_limit = top_k * 2 if rerank else top_k

            results = (
                session.query(
                    AnalysisReport,
                    embedding_col.cosine_distance(query_embedding).label("distance"),
                )
                .filter(
                    AnalysisReport.user_id == user_id,
                    embedding_col.isnot(None),
                )
                .order_by(text("distance"))
                .limit(candidate_limit)
                .all()
            )

            # 결과 변환
            candidates = [
                {
                    "id": r.AnalysisReport.id,
                    "user_id": r.AnalysisReport.user_id,
                    "record_id": r.AnalysisReport.record_id,
                    "report_date": r.AnalysisReport.report_date,
                    "llm_output": r.AnalysisReport.llm_output,
                    "model_version": r.AnalysisReport.model_version,
                    "similarity": 1 - r.distance,  # cosine similarity로 변환
                }
                for r in results
            ]

            # Reranking: 유사도 + 시간 가중치
            if rerank and candidates:
                now = datetime.utcnow()

                for candidate in candidates:
                    # 시간 가중치 계산 (최신일수록 높은 점수)
                    days_ago = (now - candidate["report_date"]).days
                    # ln(days_ago + 1) - 자연로그로 시간 decay
                    time_decay = 1 / (1 + math.log(days_ago + 1))

                    # 최종 점수 = 유사도 * 0.7 + 시간 가중치 * 0.3
                    candidate["rerank_score"] = (
                        candidate["similarity"] * 0.7 + time_decay * 0.3
                    )
                    candidate["time_weight"] = time_decay
                    candidate["days_ago"] = days_ago

                # Rerank score로 재정렬
                candidates.sort(key=lambda x: x["rerank_score"], reverse=True)

            # top_k만 반환
            return candidates[:top_k]

    # ================== User Goals 관련 ==================

    def create_user_goal(self, user_id: int, goal_data: Dict[str, Any]) -> int:
        """사용자 목표 생성"""
        with self.get_session() as session:
            goal = UserGoal(user_id=user_id, goal_data=goal_data, is_active=1)
            session.add(goal)
            session.flush()
            return goal.id

    def get_active_user_goals(self, user_id: int) -> List[Dict]:
        """활성 사용자 목표 조회"""
        with self.get_session() as session:
            goals = (
                session.query(UserGoal)
                .filter(UserGoal.user_id == user_id, UserGoal.is_active == 1)
                .all()
            )
            return [
                {
                    "id": g.id,
                    "user_id": g.user_id,
                    "goal_data": g.goal_data,
                    "created_at": g.created_at,
                    "is_active": g.is_active,
                }
                for g in goals
            ]

    # ================== Weekly Plans 관련 ==================

    def save_weekly_plan(
        self,
        user_id: int,
        week_number: int,
        start_date: date,
        end_date: date,
        plan_data: Dict[str, Any],
        model_version: str,
    ) -> int:
        """주간 계획 저장"""
        with self.get_session() as session:
            plan = WeeklyPlan(
                user_id=user_id,
                week_number=week_number,
                start_date=start_date,
                end_date=end_date,
                plan_data=plan_data,
                model_version=model_version,
            )
            session.add(plan)
            session.flush()
            return plan.id

    def get_weekly_plan(self, plan_id: int) -> Optional[Dict]:
        """주간 계획 조회"""
        with self.get_session() as session:
            plan = session.query(WeeklyPlan).filter(WeeklyPlan.id == plan_id).first()
            if plan:
                return {
                    "id": plan.id,
                    "user_id": plan.user_id,
                    "week_number": plan.week_number,
                    "start_date": plan.start_date,
                    "end_date": plan.end_date,
                    "plan_data": plan.plan_data,
                    "model_version": plan.model_version,
                    "created_at": plan.created_at,
                }
            return None

    def get_user_weekly_plans(self, user_id: int, limit: int = 10) -> List[Dict]:
        """사용자의 주간 계획 목록 조회"""
        with self.get_session() as session:
            plans = (
                session.query(WeeklyPlan)
                .filter(WeeklyPlan.user_id == user_id)
                .order_by(desc(WeeklyPlan.start_date))
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": p.id,
                    "user_id": p.user_id,
                    "week_number": p.week_number,
                    "start_date": p.start_date,
                    "end_date": p.end_date,
                    "plan_data": p.plan_data,
                    "model_version": p.model_version,
                    "created_at": p.created_at,
                }
                for p in plans
            ]

    # ================== 유틸리티 ==================

    def test_connection(self) -> bool:
        """데이터베이스 연결 테스트"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                return True
        except Exception as e:
            print(f"❌ 데이터베이스 연결 실패: {e}")
            return False

    def get_user_statistics(self, user_id: int) -> Dict[str, int]:
        """사용자 통계 조회"""
        with self.get_session() as session:
            record_count = (
                session.query(func.count(HealthRecord.id))
                .filter(HealthRecord.user_id == user_id)
                .scalar()
            )

            report_count = (
                session.query(func.count(AnalysisReport.id))
                .filter(AnalysisReport.user_id == user_id)
                .scalar()
            )

            plan_count = (
                session.query(func.count(WeeklyPlan.id))
                .filter(WeeklyPlan.user_id == user_id)
                .scalar()
            )

            return {
                "total_records": record_count or 0,
                "total_reports": report_count or 0,
                "total_plans": plan_count or 0,
            }
