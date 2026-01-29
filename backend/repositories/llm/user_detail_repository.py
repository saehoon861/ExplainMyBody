"""
UserDetail Repository (구 UserGoal Repository)
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from models.user_detail import UserDetail
from schemas.llm import UserDetailCreate


class UserDetailRepository:
    """사용자 목표/상세정보 Repository"""
    
    @staticmethod
    def create(db: Session, user_id: int, detail_data: UserDetailCreate) -> UserDetail:
        """새 사용자 상세정보 생성"""
        db_detail = UserDetail(
            user_id=user_id,
            goal_type=detail_data.goal_type,
            goal_description=detail_data.goal_description,
            preferences=detail_data.preferences,
            health_specifics=detail_data.health_specifics,
            is_active=detail_data.is_active if detail_data.is_active is not None else 1
        )
        db.add(db_detail)
        db.commit()
        db.refresh(db_detail)
        return db_detail
    
    @staticmethod
    def get_by_id(db: Session, detail_id: int) -> Optional[UserDetail]:
        """ID로 상세정보 조회"""
        return db.query(UserDetail).filter(UserDetail.id == detail_id).first()
    
    @staticmethod
    def get_active_details(db: Session, user_id: int) -> List[UserDetail]:
        """사용자의 활성 상세정보 조회"""
        return db.query(UserDetail)\
            .filter(UserDetail.user_id == user_id, UserDetail.is_active == 1, UserDetail.ended_at.is_(None))\
            .order_by(desc(UserDetail.started_at))\
            .all()
    
    @staticmethod
    def get_all_details(db: Session, user_id: int) -> List[UserDetail]:
        """사용자의 모든 상세정보 조회"""
        return db.query(UserDetail)\
            .filter(UserDetail.user_id == user_id)\
            .order_by(desc(UserDetail.started_at))\
            .all()
    
    @staticmethod
    def update(db: Session, detail_id: int, **kwargs) -> Optional[UserDetail]:
        """상세정보 업데이트"""
        db_detail = db.query(UserDetail).filter(UserDetail.id == detail_id).first()
        if not db_detail:
            return None
        
        for key, value in kwargs.items():
            if hasattr(db_detail, key) and value is not None:
                setattr(db_detail, key, value)
        
        db.commit()
        db.refresh(db_detail)
        return db_detail
    
    @staticmethod
    def delete(db: Session, detail_id: int) -> bool:
        """상세정보 삭제"""
        db_detail = db.query(UserDetail).filter(UserDetail.id == detail_id).first()
        if not db_detail:
            return False
        
        db.delete(db_detail)
        db.commit()
        return True
