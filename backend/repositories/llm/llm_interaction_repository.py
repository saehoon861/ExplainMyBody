from sqlalchemy.orm import Session
from typing import List
from models.llm_interaction import LLMInteraction
from schemas.llm import LLMInteractionCreate


class LLMInteractionRepository:
    @staticmethod
    def create(db: Session, user_id: int, interaction: LLMInteractionCreate) -> LLMInteraction:
        db_interaction = LLMInteraction(
            **interaction.model_dump(),
            user_id=user_id
        )
        db.add(db_interaction)
        db.commit()
        db.refresh(db_interaction)
        return db_interaction

    @staticmethod
    def get_by_id(db: Session, interaction_id: int) -> LLMInteraction | None:
        return db.query(LLMInteraction).filter(LLMInteraction.id == interaction_id).first()

    @staticmethod
    def get_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[LLMInteraction]:
        return db.query(LLMInteraction).filter(LLMInteraction.user_id == user_id).order_by(LLMInteraction.created_at.desc()).offset(skip).limit(limit).all()
