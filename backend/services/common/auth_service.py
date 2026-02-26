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
from schemas.inbody import InBodyData
from schemas.body_type import BodyTypeAnalysisInput
from services.ocr.body_type_service import BodyTypeService
from pydantic import ValidationError
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
            # Determine effective starting weight (Priority: OCR > Manual)
            effective_start_weight = signup_data.startWeight
            
            if signup_data.inbodyData:
                measurements = signup_data.inbodyData
                
                # 기본키 보장 및 필드 추출
                if "기본정보" not in measurements: measurements["기본정보"] = {}
                if "체중관리" not in measurements: measurements["체중관리"] = {}
                
                ocr_weight = measurements["체중관리"].get("체중")
                if ocr_weight:
                    try:
                        # OCR 데이터(또는 수정된 인바디 테이블 값)가 있으면 목표 시작체중으로 우선 사용
                        effective_start_weight = float(str(ocr_weight).replace('kg', '').strip())
                    except:
                        pass
                else:
                    # OCR에 체중이 없으면 매뉴얼 입력값으로 보완
                    measurements["체중관리"]["체중"] = signup_data.startWeight

                # 신장, 연령, 성별도 OCR 데이터 우선, 없으면 매뉴얼 입력값으로 보안
                if not measurements["기본정보"].get("신장"): measurements["기본정보"]["신장"] = signup_data.height
                if not measurements["기본정보"].get("연령"): measurements["기본정보"]["연령"] = signup_data.age
                if not measurements["기본정보"].get("성별"): measurements["기본정보"]["성별"] = signup_data.gender
                
                # 체형 분석 수행 (inbodyData가 있을 경우)
                body_type1 = None
                body_type2 = None
                
                try:
                    # InBodyData로 검증
                    validated_inbody_data = InBodyData(**signup_data.inbodyData)
                    
                    # InBodyData에서 체형 분석에 필요한 필드만 추출하여 입력 생성
                    body_type_service = BodyTypeService()
                    body_type_input = BodyTypeAnalysisInput.from_inbody_data(
                        inbody=validated_inbody_data,
                        muscle_seg=validated_inbody_data.부위별근육분석.model_dump(),
                        fat_seg=validated_inbody_data.부위별체지방분석.model_dump()
                    )
                    
                    # 체형 분석 실행 (stage2, stage3 결과 반환)
                    body_type_result = body_type_service.get_full_analysis(body_type_input)
                    
                    if body_type_result:
                        body_type1 = body_type_result.stage2  # 1차 체형 분류
                        body_type2 = body_type_result.stage3  # 2차 체형 분류
                        print(f"✅ 회원가입 체형 분석 완료: {body_type1}, {body_type2}")
                        
                        # measurements에 체형 분석 결과 추가
                        measurements["body_type1"] = body_type1
                        measurements["body_type2"] = body_type2
                
                except ValidationError as e:
                    # 체형 분석 필수 필드 누락 → 체형 분석 없이 진행
                    print(f"⚠️ 체형 분석 필수 필드 누락, 인바디 데이터만 저장: {e}")
                
                except Exception as e:
                    # 체형 분석 실패 → 체형 분석 없이 진행
                    print(f"⚠️ 체형 분석 실패, 인바디 데이터만 저장: {e}")
                
                health_record_data = HealthRecordCreate(
                    measurements=measurements,
                    source="signup",
                    measured_at=None
                )
                health_record = HealthRecordRepository.create(db, new_user.id, health_record_data)
            
            # # body_type 별도 컬럼에도 저장 (조회 편의용)
            # if body_type1 is not None or body_type2 is not None:
            #     health_record.body_type1 = body_type1
            #     health_record.body_type2 = body_type2
            #     db.commit()
            #     db.refresh(health_record)
            
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
                "start_weight": effective_start_weight,
                "target_weight": signup_data.targetWeight,
                "description": signup_data.goal if signup_data.goal else signup_data.goalType
            }
            
            detail_data = UserDetailCreate(
                goal_type=signup_data.goalType,
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