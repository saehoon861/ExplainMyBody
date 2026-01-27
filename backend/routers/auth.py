"""
인증 라우터
/api/auth/*
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas.common import UserCreate, UserResponse, UserLogin
from services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    회원가입
    
    - **username**: 사용자 이름
    - **email**: 이메일 주소
    """
    new_user = AuthService.register(db, user_data)
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
