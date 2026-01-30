from pydantic import BaseModel, EmailStr

class EmailCheckRequest(BaseModel):
    """이메일 중복 확인 요청 스키마"""
    email: EmailStr
