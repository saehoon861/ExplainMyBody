"""
SQLAlchemy 기반 데이터베이스 관리 (pgvector 지원)
"""

import os
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from contextlib import contextmanager

from sqlalchemy import create_engine, text, desc
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import JSONB
from dotenv import load_dotenv

from shared.db_models import Base, HealthRecord, InbodyAnalysisReport, WeeklyPlan

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

        # 마이그레이션 실행 (컬럼 추가)
        self._run_migrations()

        # 인덱스 생성 (pgvector용)
        self._create_vector_indexes()

    def _run_migrations(self):
        """데이터베이스 마이그레이션 실행 (컬럼 추가 등)"""
        with self.engine.connect() as conn:
            try:
                # Migration: Add refined_output column to inbody_analysis_reports
                conn.execute(
                    text(
                        """
                        ALTER TABLE inbody_analysis_reports
                        ADD COLUMN IF NOT EXISTS refined_output TEXT
                        """
                    )
                )
                conn.commit()
                print("✅ Migration: refined_output 컬럼 추가 (inbody_analysis_reports)")
            except Exception as e:
                print(f"⚠️  Migration 실패 (inbody_analysis_reports): {e}")

            try:
                # Migration: Add refined_output column to weekly_plans
                conn.execute(
                    text(
                        """
                        ALTER TABLE weekly_plans
                        ADD COLUMN IF NOT EXISTS refined_output TEXT
                        """
                    )
                )
                conn.commit()
                print("✅ Migration: refined_output 컬럼 추가 (weekly_plans)")
            except Exception as e:
                print(f"⚠️  Migration 실패 (weekly_plans): {e}")

    def _create_vector_indexes(self):
        """Vector 검색을 위한 인덱스 생성 (1536D + 1024D)"""
        with self.engine.connect() as conn:
            try:
                # HNSW 인덱스 생성 for embedding_1536 (OpenAI)
                conn.execute(
                    text(
                        """
                        CREATE INDEX IF NOT EXISTS idx_inbody_analysis_reports_embedding_1536_hnsw
                        ON inbody_analysis_reports USING hnsw (embedding_1536 vector_cosine_ops)
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
                        CREATE INDEX IF NOT EXISTS idx_inbody_analysis_reports_embedding_1024_hnsw
                        ON inbody_analysis_reports USING hnsw (embedding_1024 vector_cosine_ops)
                        WITH (m = 16, ef_construction = 64)
                        """
                    )
                )
                conn.commit()
                print("✅ pgvector HNSW 인덱스 생성 완료 (1024D)")
            except Exception as e:
                print(f"⚠️  Vector 인덱스 (1024D) 생성 실패: {e}")

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
        """인바디 분석 리포트 저장 (임베딩 포함)"""
        with self.get_session() as session:
            report = InbodyAnalysisReport(
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
        """인바디 분석 리포트에 임베딩 추가/업데이트"""
        with self.get_session() as session:
            report = (
                session.query(InbodyAnalysisReport)
                .filter(InbodyAnalysisReport.id == report_id)
                .first()
            )
            if report:
                if embedding_1536 is not None:
                    report.embedding_1536 = embedding_1536
                if embedding_1024 is not None:
                    report.embedding_1024 = embedding_1024
                return True
            return False

    def update_analysis_refined_output(
        self,
        report_id: int,
        refined_output: str,
    ) -> bool:
        """인바디 분석 리포트에 2차 정제 출력 업데이트"""
        with self.get_session() as session:
            report = (
                session.query(InbodyAnalysisReport)
                .filter(InbodyAnalysisReport.id == report_id)
                .first()
            )
            if report:
                report.refined_output = refined_output
                return True
            return False

    def get_analysis_report(self, report_id: int) -> Optional[Dict]:
        """인바디 분석 리포트 조회"""
        with self.get_session() as session:
            report = (
                session.query(InbodyAnalysisReport)
                .filter(InbodyAnalysisReport.id == report_id)
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
        """사용자의 인바디 분석 리포트 목록 조회"""
        with self.get_session() as session:
            reports = (
                session.query(InbodyAnalysisReport)
                .filter(InbodyAnalysisReport.user_id == user_id)
                .order_by(desc(InbodyAnalysisReport.report_date))
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
                embedding_col = InbodyAnalysisReport.embedding_1536
            elif embedding_dim == 1024:
                embedding_col = InbodyAnalysisReport.embedding_1024
            else:
                raise ValueError(f"지원하지 않는 임베딩 차원: {embedding_dim}")

            # pgvector의 cosine distance 사용 (1 - cosine similarity)
            # 후보를 더 많이 가져와서 reranking (top_k * 2)
            candidate_limit = top_k * 2 if rerank else top_k

            results = (
                session.query(
                    InbodyAnalysisReport,
                    embedding_col.cosine_distance(query_embedding).label("distance"),
                )
                .filter(
                    InbodyAnalysisReport.user_id == user_id,
                    embedding_col.isnot(None),
                )
                .order_by(text("distance"))
                .limit(candidate_limit)
                .all()
            )

            # 결과 변환
            candidates = [
                {
                    "id": r[0].id,
                    "user_id": r[0].user_id,
                    "record_id": r[0].record_id,
                    "report_date": r[0].report_date,
                    "llm_output": r[0].llm_output,
                    "model_version": r[0].model_version,
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

    def update_weekly_plan_refined_output(
        self,
        plan_id: int,
        refined_output: str,
    ) -> bool:
        """주간 계획에 2차 정제 출력 업데이트"""
        with self.get_session() as session:
            plan = (
                session.query(WeeklyPlan)
                .filter(WeeklyPlan.id == plan_id)
                .first()
            )
            if plan:
                plan.refined_output = refined_output
                return True
            return False
