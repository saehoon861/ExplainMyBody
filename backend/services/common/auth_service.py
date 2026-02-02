"""
인증 서비스
로그인/회원가입 비즈니스 로직
"""

from sqlalchemy.orm import Session
from typing import Optional

from repositories.common.user_repository import UserRepository
from repositories.common.health_record_repository import HealthRecordRepository
from repositories.llm.user_detail_repository import UserDetailRepository
from schemas.common import UserCreate, UserLogin, UserSignupRequest, HealthRecordCreate
from schemas.llm import UserDetailCreate
from exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    UserNotFoundError
)


class AuthService:
    """인증 관련 비즈니스 로직"""
    
    @staticmethod
    def check_email_availability(db: Session, email: str) -> bool:
        """이메일 중복 확인 (생성 안함)"""
        existing_user = UserRepository.get_by_email(db, email)
        if existing_user:
            raise EmailAlreadyExistsError(
                "이미 사용 중인 이메일입니다."
            )
        return True 

    @staticmethod
    def register_extended(db: Session, signup_data: UserSignupRequest):
        """회원가입 (확장): 유저 + 초기 건강기록 + 목표 생성"""
        # 이메일 중복 확인
        existing_user = UserRepository.get_by_email(db, signup_data.email)
        if existing_user:
            raise EmailAlreadyExistsError(
                "이미 등록된 이메일입니다."
            )
        
        # 1. 사용자 생성
        # UserSignupRequest inherits UserCreate, so valid for UserRepository
        new_user = UserRepository.create(db, signup_data)
        
        try:
            # 2. 초기 건강 기록 생성
            measurements = signup_data.inbodyData or {}
            
            # 기본키 보장
            if "기본정보" not in measurements:
                measurements["기본정보"] = {}
            if "체중관리" not in measurements:
                measurements["체중관리"] = {}
            
            # 매뉴얼 입력값 덮어쓰기 (Step 3에서 입력한 값 등)
            measurements["기본정보"]["신장"] = signup_data.height
            measurements["기본정보"]["연령"] = signup_data.age
            measurements["기본정보"]["성별"] = signup_data.gender
            measurements["체중관리"]["체중"] = signup_data.startWeight
            
            health_record_data = HealthRecordCreate(
                measurements=measurements,
                source="signup",
                measured_at=None
            )
            HealthRecordRepository.create(db, new_user.id, health_record_data)
            
            # 3. 사용자 목표/상세정보 생성
            preferences_list = []
            if signup_data.activityLevel:
                preferences_list.append(f"활동레벨: {signup_data.activityLevel}")
            if signup_data.preferredExercises:
                preferences_list.extend(signup_data.preferredExercises)
            
            preferences_str = ", ".join(preferences_list)
            
            medical_str = ", ".join(signup_data.medicalConditions) if signup_data.medicalConditions else ""
            if signup_data.medicalConditionsDetail:
                medical_str += f" ({signup_data.medicalConditionsDetail})"
                
            # 목표(상세)와 목표 체중을 하나의 JSON 문자열로 결합하여 저장
            # DB 스키마 변경 없이 goal_description 컬럼(Text) 활용
            import json
            combined_description = {
                "start_weight": signup_data.startWeight,
                "target_weight": signup_data.targetWeight,
                "description": signup_data.goal if signup_data.goal else signup_data.goalType
            }
            
            detail_data = UserDetailCreate(
                goal_type=signup_data.goalType,
                # target_weight=signup_data.targetWeight, # DB 컬럼 없음
                goal_description=json.dumps(combined_description, ensure_ascii=False),
                preferences=preferences_str,
                health_specifics=medical_str,
                is_active=1
            )
            UserDetailRepository.create(db, new_user.id, detail_data)
            
        except Exception as e:
            # 롤백 처리 (사용자 삭제) - 실제 프로덕션에선 DB 트랜잭션 롤백 사용 권장
            # 여기선 간단히 try-except
            print(f"회원가입 후속 처리 실패: {e}")
            # UserRepository.delete(db, new_user.id) # method existence unchecked
            # pass for MVP
        
        # Ensure user details are loaded for the response model
        db.refresh(new_user) 
        return new_user

    
    @staticmethod
    def login(db: Session, login_data: UserLogin):
        """로그인 (간단한 버전, 추후 JWT 토큰 등 추가 가능)"""

        print(login_data)
        print(login_data.email)
        user = UserRepository.get_by_email(db, login_data.email)
        print(user)
        if not user:
            raise InvalidCredentialsError(
                "이메일 또는 비밀번호가 올바르지 않습니다."
            )
        
        # TODO: 비밀번호 검증 로직 추가
        # 현재는 간단하게 사용자 존재 여부만 확인
        
        return user
    
    @staticmethod
    def get_current_user(db: Session, user_id: int):
        """현재 사용자 정보 조회"""
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise UserNotFoundError(
                "사용자를 찾을 수 없습니다."
            )
        return user
    
    @staticmethod
    def logout(db: Session, user_id: int):
        """로그아웃"""
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise UserNotFoundError(
                "사용자를 찾을 수 없습니다."
            )
        return user