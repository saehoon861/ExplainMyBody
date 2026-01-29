from sqlalchemy import Column, Integer, String, JSON, Boolean, Float
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
    # 기본 프로필
    gender = Column(String)  # male, female
    age = Column(Integer)
    height = Column(Float)
    
    # 목표 및 상태
    start_weight = Column(Float)
    target_weight = Column(Float)
    goal_type = Column(String)  # 감량, 증량, 유지, 재활
    activity_level = Column(String) # 활동량
    goal_description = Column(String) # 목표 상세
    
    # 의료 정보 (JSON으로 저장: ["고혈압", "당뇨"])
    medical_conditions = Column(JSON, default=[])
    medical_conditions_detail = Column(String, nullable=True)

    # 운동 선호 항목 (JSON으로 저장)
    preferred_exercises = Column(JSON, default=[])
    
    # 인바디 데이터 (JSON으로 전체 구조 저장)
    inbody_data = Column(JSON, nullable=True)
    
    # 시스템 필드
    is_active = Column(Boolean, default=True)
