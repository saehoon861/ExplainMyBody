"""
HealthRecord Repository
건강 기록 데이터 접근 계층
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc
from models.health_record import HealthRecord
from schemas.health_record import HealthRecordCreate
from typing import Optional, List
from datetime import datetime


class HealthRecordRepository:
    """건강 기록 데이터 접근 계층"""
    
    @staticmethod
    def create(db: Session, user_id: int, record_data: HealthRecordCreate) -> HealthRecord:
        """건강 기록 생성"""
        db_record = HealthRecord(
            user_id=user_id,
            measurements=record_data.measurements,
            source=record_data.source,
            measured_at=record_data.measured_at or datetime.now()
        )
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        return db_record
    
    @staticmethod
    def get_by_id(db: Session, record_id: int) -> Optional[HealthRecord]:
        """ID로 건강 기록 조회"""
        return db.query(HealthRecord).filter(HealthRecord.id == record_id).first()
    
    @staticmethod
    def get_by_user(db: Session, user_id: int, limit: int = 10) -> List[HealthRecord]:
        """사용자의 건강 기록 목록 조회 (최신순)"""
        return db.query(HealthRecord)\
            .filter(HealthRecord.user_id == user_id)\
            .order_by(desc(HealthRecord.measured_at))\
            .limit(limit)\
            .all()
    
    @staticmethod
    def get_latest(db: Session, user_id: int) -> Optional[HealthRecord]:
        """사용자의 가장 최신 건강 기록 조회"""
        return db.query(HealthRecord)\
            .filter(HealthRecord.user_id == user_id)\
            .order_by(desc(HealthRecord.measured_at))\
            .first()
    
    @staticmethod
    def update(db: Session, record_id: int, **kwargs) -> Optional[HealthRecord]:
        """건강 기록 수정"""
        db_record = db.query(HealthRecord).filter(HealthRecord.id == record_id).first()
        if db_record:
            for key, value in kwargs.items():
                setattr(db_record, key, value)
            db.commit()
            db.refresh(db_record)
        return db_record
    
    @staticmethod
    def delete(db: Session, record_id: int) -> bool:
        """건강 기록 삭제"""
        db_record = db.query(HealthRecord).filter(HealthRecord.id == record_id).first()
        if db_record:
            db.delete(db_record)
            db.commit()
            return True
        return False
    
    @staticmethod
    def search_by_body_type(db: Session, user_id: int, body_type: str) -> List[HealthRecord]:
        """체형 타입으로 검색 (stage2 기준)"""
        return db.query(HealthRecord)\
            .filter(HealthRecord.user_id == user_id, HealthRecord.body_type1 == body_type)\
            .order_by(desc(HealthRecord.measured_at))\
            .all()
