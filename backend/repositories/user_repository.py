"""
User Repository
데이터베이스 CRUD 로직
"""

from sqlalchemy.orm import Session
from models.user import User
from schemas.user import UserCreate
from typing import Optional


class UserRepository:
    """사용자 데이터 접근 계층"""
    
    @staticmethod
    def create(db: Session, user_data: UserCreate) -> User:
        """사용자 생성"""
        db_user = User(
            username=user_data.username,
            email=user_data.email
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        """ID로 사용자 조회"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        """이메일로 사용자 조회"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100):
        """모든 사용자 조회 (페이지네이션)"""
        return db.query(User).offset(skip).limit(limit).all()
    
    @staticmethod
    def update(db: Session, user_id: int, **kwargs) -> Optional[User]:
        """사용자 정보 수정"""
        db_user = db.query(User).filter(User.id == user_id).first()
        if db_user:
            for key, value in kwargs.items():
                setattr(db_user, key, value)
            db.commit()
            db.refresh(db_user)
        return db_user
    
    @staticmethod
    def delete(db: Session, user_id: int) -> bool:
        """사용자 삭제"""
        db_user = db.query(User).filter(User.id == user_id).first()
        if db_user:
            db.delete(db_user)
            db.commit()
            return True
        return False
