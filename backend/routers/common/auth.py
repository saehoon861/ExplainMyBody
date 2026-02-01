"""
인증 라우터
/api/auth/*
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas.common import UserCreate, UserResponse, UserLogin, UserSignupRequest, EmailCheckRequest
from services.common.auth_service import AuthService

router = APIRouter()


@router.post("/check-email", status_code=200)
def check_email(email_data: EmailCheckRequest, db: Session = Depends(get_db)):
    """
    이메일 중복 확인
    
    - **email**: 확인할 이메일 주소
    - 사용 가능하면 200 OK, 이미 존재하면 409 Conflict 반환
    """
    #규민 수정 시작
    try:
        print(f"[DEBUG] Checking email: {email_data.email}")
        AuthService.check_email_availability(db, email_data.email)
        print(f"[DEBUG] Email available: {email_data.email}")
        return {"available": True, "message": "사용 가능한 이메일입니다."}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] check_email failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
   #규민 수정 끝

@router.post("/register", response_model=UserResponse, status_code=201)
def register(user_data: UserSignupRequest, db: Session = Depends(get_db)):
    """
    회원가입 (확장)
    - 사용자 기본 정보
    - 인바디 데이터 (선택)
    - 목표 및 건강 정보 (선택)
    """
    new_user = AuthService.register_extended(db, user_data)
    return new_user


@router.post("/login", response_model=UserResponse)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    로그인
    
    - **email**: 이메일 주소
    - **password**: 비밀번호
    """
    user = AuthService.login(db, login_data)
    return user


@router.get("/me", response_model=UserResponse)
def get_current_user(user_id: int, db: Session = Depends(get_db)):
    """
    현재 사용자 정보 조회
    
    - **user_id**: 사용자 ID (쿼리 파라미터)
    """
    user = AuthService.get_current_user(db, user_id)
    return user


@router.post("/logout", status_code=200)
def logout(user_id: int, db: Session = Depends(get_db)):
    """
    로그아웃
    
    - **user_id**: 사용자 ID (쿼리 파라미터)
    """
    AuthService.logout(db, user_id)
    return {"message": "로그아웃 완료"}
