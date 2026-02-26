from sqlalchemy.orm import Session
from typing import List
from models.human_feedback import HumanFeedback
from schemas.llm import HumanFeedbackCreate


class HumanFeedbackRepository:
    @staticmethod
    def create(db: Session, user_id: int, feedback: HumanFeedbackCreate) -> HumanFeedback:
        db_feedback = HumanFeedback(
            **feedback.model_dump(),
            user_id=user_id
        )
        db.add(db_feedback)
        db.commit()
        db.refresh(db_feedback)
        return db_feedback

    @staticmethod
    def get_by_llm_interaction(db: Session, llm_interaction_id: int) -> List[HumanFeedback]:
        return db.query(HumanFeedback).filter(HumanFeedback.llm_interaction_id == llm_interaction_id).order_by(HumanFeedback.created_at.asc()).all()
