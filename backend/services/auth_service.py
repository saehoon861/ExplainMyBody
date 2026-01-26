"""
인증 서비스
로그인/회원가입 비즈니스 로직
"""

from sqlalchemy.orm import Session
from repositories.user_repository import UserRepository
from schemas.user import UserCreate, UserLogin
from fastapi import HTTPException, status
from typing import Optional


class AuthService:
    """인증 관련 비즈니스 로직"""
    
    @staticmethod
    def register(db: Session, user_data: UserCreate):
        """회원가입"""
        # 이메일 중복 확인
        existing_user = UserRepository.get_by_email(db, user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 등록된 이메일입니다."
            )
        
        # 사용자 생성
        new_user = UserRepository.create(db, user_data)
        return new_user
    
    @staticmethod
    def login(db: Session, login_data: UserLogin):
        """로그인 (간단한 버전, 추후 JWT 토큰 등 추가 가능)"""
        user = UserRepository.get_by_email(db, login_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 올바르지 않습니다."
            )
        
        # TODO: 비밀번호 검증 로직 추가
        # 현재는 간단하게 사용자 존재 여부만 확인
        
        return user
    
    @staticmethod
    def get_current_user(db: Session, user_id: int):
        """현재 사용자 정보 조회"""
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )
        return user
