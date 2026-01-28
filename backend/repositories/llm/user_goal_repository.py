"""
UserGoal Repository
사용자 목표 데이터 접근 계층
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc
from models.user_goal import UserGoal
from schemas.llm import UserGoalCreate
from typing import Optional, List


class UserGoalRepository:
    """사용자 목표 데이터 접근 계층"""
    
    @staticmethod
    def create(db: Session, user_id: int, goal_data: UserGoalCreate) -> UserGoal:
        """사용자 목표 생성"""
        db_goal = UserGoal(
            user_id=user_id,
            goal_type=goal_data.goal_type,
            goal_description=goal_data.goal_description
        )
        db.add(db_goal)
        db.commit()
        db.refresh(db_goal)
        return db_goal
    
    @staticmethod
    def get_by_id(db: Session, goal_id: int) -> Optional[UserGoal]:
        """ID로 목표 조회"""
        return db.query(UserGoal).filter(UserGoal.id == goal_id).first()
    
    @staticmethod
    def get_active_goals(db: Session, user_id: int) -> List[UserGoal]:
        """사용자의 활성 목표 조회 (ended_at이 NULL)"""
        return db.query(UserGoal)\
            .filter(UserGoal.user_id == user_id, UserGoal.ended_at.is_(None))\
            .order_by(desc(UserGoal.started_at))\
            .all()
    
    @staticmethod
    def get_all_goals(db: Session, user_id: int) -> List[UserGoal]:
        """사용자의 모든 목표 조회"""
        return db.query(UserGoal)\
            .filter(UserGoal.user_id == user_id)\
            .order_by(desc(UserGoal.started_at))\
            .all()
    
    @staticmethod
    def update(db: Session, goal_id: int, **kwargs) -> Optional[UserGoal]:
        """목표 수정"""
        db_goal = db.query(UserGoal).filter(UserGoal.id == goal_id).first()
        if db_goal:
            for key, value in kwargs.items():
                setattr(db_goal, key, value)
            db.commit()
            db.refresh(db_goal)
        return db_goal
    
    @staticmethod
    def delete(db: Session, goal_id: int) -> bool:
        """목표 삭제"""
        db_goal = db.query(UserGoal).filter(UserGoal.id == goal_id).first()
        if db_goal:
            db.delete(db_goal)
            db.commit()
            return True
        return False
