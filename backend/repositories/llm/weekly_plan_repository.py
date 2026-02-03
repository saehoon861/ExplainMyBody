"""
WeeklyPlan Repository
주간 계획 데이터 접근 계층
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from models.weekly_plan import WeeklyPlan
from schemas.llm import WeeklyPlanCreate, WeeklyPlanUpdate
from typing import Optional, List
from datetime import date


class WeeklyPlanRepository:
    """주간 계획 데이터 접근 계층"""
    
    @staticmethod
    def create(db: Session, user_id: int, plan_data: WeeklyPlanCreate) -> WeeklyPlan:
        """주간 계획 생성"""
        db_plan = WeeklyPlan(
            user_id=user_id,
            week_number=plan_data.week_number,
            start_date=plan_data.start_date,
            end_date=plan_data.end_date,
            plan_data=plan_data.plan_data,
            model_version=plan_data.model_version
        )
        db.add(db_plan)
        db.commit()
        db.refresh(db_plan)
        return db_plan
    
    @staticmethod
    def get_by_id(db: Session, plan_id: int) -> Optional[WeeklyPlan]:
        """ID로 주간 계획 조회"""
        return db.query(WeeklyPlan).filter(WeeklyPlan.id == plan_id).first()
    
    @staticmethod
    def get_by_user(db: Session, user_id: int, limit: int = 10) -> List[WeeklyPlan]:
        """사용자의 주간 계획 목록 조회"""
        return db.query(WeeklyPlan)\
            .filter(WeeklyPlan.user_id == user_id)\
            .order_by(desc(WeeklyPlan.created_at))\
            .limit(limit)\
            .all()
    
    @staticmethod
    def get_by_week(db: Session, user_id: int, week_number: int) -> Optional[WeeklyPlan]:
        """특정 주차의 계획 조회 (가장 최신)"""
        return db.query(WeeklyPlan)\
            .filter(
                and_(
                    WeeklyPlan.user_id == user_id,
                    WeeklyPlan.week_number == week_number
                )
            )\
            .order_by(desc(WeeklyPlan.created_at))\
            .first()
    
    @staticmethod
    def get_latest(db: Session, user_id: int) -> Optional[WeeklyPlan]:
        """사용자의 가장 최근 주간 계획 조회 (주차 무관)"""
        return db.query(WeeklyPlan)\
            .filter(WeeklyPlan.user_id == user_id)\
            .order_by(desc(WeeklyPlan.created_at))\
            .first()
    
    @staticmethod
    def update(db: Session, plan_id: int, **kwargs) -> Optional[WeeklyPlan]:
        """주간 계획 수정"""
        db_plan = db.query(WeeklyPlan).filter(WeeklyPlan.id == plan_id).first()
        if db_plan:
            for key, value in kwargs.items():
                if hasattr(db_plan, key) and value is not None:
                    setattr(db_plan, key, value)
            db.commit()
            db.refresh(db_plan)
            return db_plan
        return None
    
    @staticmethod
    def delete(db: Session, plan_id: int) -> bool:
        """주간 계획 삭제"""
        db_plan = db.query(WeeklyPlan).filter(WeeklyPlan.id == plan_id).first()
        if db_plan:
            db.delete(db_plan)
            db.commit()
            return True
        return False
