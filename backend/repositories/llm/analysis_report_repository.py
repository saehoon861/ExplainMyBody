"""
InbodyAnalysisReport Repository (구 AnalysisReport Repository)
"""

from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import desc, text
from models.analysis_report import InbodyAnalysisReport
from schemas.llm import AnalysisReportCreate


class AnalysisReportRepository:
    """분석 리포트 데이터 접근 계층"""
    
    @staticmethod
    def create(db: Session, user_id: int, report_data: AnalysisReportCreate) -> InbodyAnalysisReport:
        """분석 리포트 생성"""
        db_report = InbodyAnalysisReport(
            user_id=user_id,
            record_id=report_data.record_id,
            llm_output=report_data.llm_output,
            model_version=report_data.model_version,
            analysis_type=report_data.analysis_type,
            embedding_1536=report_data.embedding_1536 if hasattr(report_data, 'embedding_1536') else None
        )
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
        return db_report
    
    @staticmethod
    def get_by_id(db: Session, report_id: int) -> Optional[InbodyAnalysisReport]:
        """ID로 리포트 조회"""
        return db.query(InbodyAnalysisReport).filter(InbodyAnalysisReport.id == report_id).first()
    
    @staticmethod
    def get_by_record_id(db: Session, record_id: int) -> Optional[InbodyAnalysisReport]:
        """건강 기록 ID로 리포트 조회 (가장 최신)"""
        return db.query(InbodyAnalysisReport)\
            .filter(InbodyAnalysisReport.record_id == record_id)\
            .order_by(desc(InbodyAnalysisReport.generated_at))\
            .first()

    @staticmethod
    def get_by_record_id_and_type(
        db: Session,
        record_id: int,
        analysis_type: str
    ) -> Optional[InbodyAnalysisReport]:
        """건강 기록 ID와 분석 타입으로 리포트 조회 (가장 최신)"""
        return db.query(InbodyAnalysisReport)\
            .filter(
                InbodyAnalysisReport.record_id == record_id,
                InbodyAnalysisReport.analysis_type == analysis_type
            )\
            .order_by(desc(InbodyAnalysisReport.generated_at))\
            .first()
    
    @staticmethod
    def get_by_user(db: Session, user_id: int, limit: int = 10) -> List[InbodyAnalysisReport]:
        """사용자의 리포트 목록 조회"""
        return db.query(InbodyAnalysisReport)\
            .filter(InbodyAnalysisReport.user_id == user_id)\
            .order_by(desc(InbodyAnalysisReport.generated_at))\
            .limit(limit)\
            .all()
    
    @staticmethod
    def delete(db: Session, report_id: int) -> bool:
        """리포트 삭제"""
        db_report = db.query(InbodyAnalysisReport).filter(InbodyAnalysisReport.id == report_id).first()
        if db_report:
            db.delete(db_report)
            db.commit()
            return True
        return False
    
    @staticmethod
    def update_embedding(
        db: Session,
        report_id: int,
        embedding_1536: Optional[List[float]] = None,
        embedding_1024: Optional[List[float]] = None
    ) -> bool:
        """분석 리포트 임베딩 업데이트"""
        db_report = db.query(InbodyAnalysisReport)\
            .filter(InbodyAnalysisReport.id == report_id)\
            .first()
        
        if db_report:
            if embedding_1536 is not None:
                db_report.embedding_1536 = embedding_1536
            if embedding_1024 is not None:
                db_report.embedding_1024 = embedding_1024
            db.commit()
            db.refresh(db_report)
            return True
        return False
    
    @staticmethod
    def search_similar_reports(
        db: Session,
        user_id: int,
        query_embedding: List[float],
        top_k: int = 6,
        embedding_dim: int = 1536,
        rerank: bool = True
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
        
        # 임베딩 차원에 따라 컬럼 선택
        if embedding_dim == 1536:
            embedding_col = InbodyAnalysisReport.embedding_1536
        elif embedding_dim == 1024:
            embedding_col = InbodyAnalysisReport.embedding_1024
        else:
            raise ValueError(f"지원하지 않는 임베딩 차원: {embedding_dim}")
        
        # pgvector의 cosine distance 사용
        candidate_limit = top_k * 2 if rerank else top_k
        
        results = db.query(
            InbodyAnalysisReport,
            embedding_col.cosine_distance(query_embedding).label("distance")
        ).filter(
            InbodyAnalysisReport.user_id == user_id,
            embedding_col.isnot(None)
        ).order_by(
            text("distance")
        ).limit(candidate_limit).all()
        
        # 결과 변환
        candidates = [
            {
                "id": r[0].id,
                "user_id": r[0].user_id,
                "record_id": r[0].record_id,
                "generated_at": r[0].generated_at,
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
                # 시간 가중치 계산
                days_ago = (now - candidate["generated_at"]).days
                time_decay = 1 / (1 + math.log(days_ago + 1))
                
                # 최종 점수 = 유사도 * 0.7 + 시간 가중치 * 0.3
                candidate["rerank_score"] = candidate["similarity"] * 0.7 + time_decay * 0.3
                candidate["time_weight"] = time_decay
                candidate["days_ago"] = days_ago
            
            # Rerank score로 재정렬
            candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
        
        # top_k만 반환
        return candidates[:top_k]
