"""
InBody OCR Web Application - FastAPI Backend
"""

import os
import sys
import json
import tempfile
import traceback
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, ConfigDict
import cv2
import numpy as np
from sqlalchemy.orm import Session
from passlib.context import CryptContext

# DB & Models
from database import engine, get_db
import models

# DB 초기화 (테이블 생성)
models.Base.metadata.create_all(bind=engine)

# 비밀번호 해싱 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# InBody 매처 클래스
try:
    from inbody_matcher import InBodyMatcher
except ImportError:
    print("⚠️ inbody_matcher.py 파일을 찾을 수 없습니다.")
    sys.exit(1)

# Pydantic 모델 (Request Schemas)
class InBodyResult(BaseModel):
    pass # 실제 사용시 구체화 필요, 현재는 Dict로 처리중

class UserSignup(BaseModel):
    email: EmailStr
    password: str
    gender: str
    age: int
    height: float
    startWeight: float
    targetWeight: float
    goalType: str
    activityLevel: str
    goal: str
    preferredExercises: list[str] = []
    medicalConditions: list[str] = []
    medicalConditionsDetail: Optional[str] = None
    inbodyData: Optional[dict] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserGoalUpdate(BaseModel):
    start_weight: Optional[float] = None
    target_weight: Optional[float] = None
    goal_type: Optional[str] = None
    goal_description: Optional[str] = None

class UserRecordUpdate(BaseModel):
    date: str  # YYYY-MM-DD
    food: Optional[list] = None
    exercise: Optional[list] = None

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    is_active: bool
    # 상세 프로필 정보 추가
    gender: Optional[str] = None
    age: Optional[int] = None
    height: Optional[float] = None
    start_weight: Optional[float] = None
    target_weight: Optional[float] = None
    goal_type: Optional[str] = None
    activity_level: Optional[str] = None
    goal_description: Optional[str] = None
    inbody_data: Optional[Dict[str, Any]] = None
    daily_records: Optional[Dict[str, Any]] = None

app = FastAPI(title="InBody OCR API", description="InBody 인쇄물 OCR 분석 API")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 설정
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'bmp'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# 업로드 폴더 생성
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 모델 로딩
print("⏳ InBodyMatcher 모델 로딩 중... (약 2~3초 소요)")
try:
    matcher = InBodyMatcher(auto_perspective=True, skew_threshold=15.0)
    print("✅ InBodyMatcher 모델 로딩 완료")
except Exception as e:
    print(f"❌ 모델 로딩 실패: {e}")
    sys.exit(1)


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_password_hash(password):
    return pwd_context.hash(password)

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "InBody OCR API (FastAPI)"}
@app.post("/api/login", response_model=UserResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    # 1. 이메일로 사용자 조회
    user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
    
    # 2. 비밀번호 검증
    if not pwd_context.verify(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
    
    # 3. 사용자 정보 반환 (UserResponse 모델에 맞춰 자동 변환됨)
    print(f"✅ 로그인 성공: {user.email}")
    return user

@app.post("/api/signup", response_model=UserResponse)
async def signup(user: UserSignup, db: Session = Depends(get_db)):
    # [백엔드 -> 데이터베이스 저장 시작]
    # 1. 프론트엔드에서 보낸 JSON 데이터가 UserSignup 파이던틱 모델로 수신됨
    print(f"DEBUG: Signup request for email: {user.email}")
    print(f"DEBUG: Password length: {len(user.password)}")
    
    # 이메일 중복 체크 (DB 조회)
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")
    
    # 2. 보안을 위해 비밀번호 해싱
    hashed_password = get_password_hash(user.password)
    
    # 3. SQLAlchemy ORM 모델 객체 생성 (데이터 매핑)
    # 수신된 데이터를 DB 테이블 구조에 맞게 하나씩 연결(매핑)합니다.
    new_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        gender=user.gender,
        age=user.age,
        height=user.height,
        start_weight=user.startWeight,
        target_weight=user.targetWeight,
        goal_type=user.goalType,
        activity_level=user.activityLevel,
        goal_description=user.goal,
        preferred_exercises=user.preferredExercises,
        medical_conditions=user.medicalConditions,
        medical_conditions_detail=user.medicalConditionsDetail,
        inbody_data=user.inbodyData
    )
    
    try:
        # 4. 데이터베이스 세션에 추가 및 확정(Commit)
        # 이 시점에 SQLite 데이터베이스 파일(explainmybody.db)에 실제 데이터가 기록됩니다.
        db.add(new_user)
        db.commit()
        db.refresh(new_user) # 저장된 객체 정보를 다시 읽어옴 (생성된 ID 등 확인용)
        print(f"✅ 새 사용자 등록 성공: {new_user.email} (ID: {new_user.id})")
        return new_user
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"회원가입 중 오류 발생: {str(e)}")

@app.post("/api/process")
async def process_inbody(
    file: UploadFile = File(...),
    auto_perspective: bool = Form(True),
    skew_threshold: float = Form(15.0)
):
    """InBody 이미지 처리 API (메모리 최적화)"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="파일이 선택되지 않았습니다")
    
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="이미지 파일을 읽을 수 없습니다.")

        matcher.auto_perspective = auto_perspective
        matcher.skew_threshold = skew_threshold
        
        # 서버 환경에서는 병렬 처리(스레딩) 오버헤드가 클 수 있으므로 순차 처리로 변경
        import time
        start_time = time.time()
        results = matcher.extract_and_match(img)
        end_time = time.time()
        print(f"⏱️ OCR 처리 시간: {end_time - start_time:.2f}초")
        
        if not results:
            raise HTTPException(status_code=400, detail="OCR 결과를 추출할 수 없습니다")
        
        structured = matcher.get_structured_results(results)
        
        total_fields = len(results)
        detected_fields = sum(1 for v in results.values() if v is not None and v != "미검출")
        # detection_rate = (detected_fields / total_fields * 100) if total_fields > 0 else 0
        
        return {
            "success": True,
            "data": {
                "raw": results,
                "structured": structured
            }
        }
    except Exception as e:
        # print(f"Error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/save")
async def save_inbody(data: Dict[str, Any]):
    # 데이터 저장 로직 보강 필요 (현재는 검증만)
    return {"success": True, "message": "데이터 수신 됨 (DB 저장 로직 필요)"}

@app.post("/api/download")
async def download_results(data: Dict[str, Any], background_tasks: BackgroundTasks):
    if not data:
        raise HTTPException(status_code=400, detail="데이터가 없습니다")
    
    try:
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
        json.dump(data, tmp, ensure_ascii=False, indent=2)
        tmp.close()
        temp_path = tmp.name
        
        background_tasks.add_task(os.unlink, temp_path)
        
        return FileResponse(temp_path, media_type='application/json', filename='inbody_result.json')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/debug/users")
async def get_all_users(db: Session = Depends(get_db)):
    """
    [연결 확인 도구] 
    디버그용: 모든 가입 사용자 목록 조회
    이 주소로 접속하면 DB에 데이터가 실제로 잘 쌓였는지 JSON 형태로 직접 확인할 수 있습니다.
    """
    users = db.query(models.User).all()
    return {
        "count": len(users),
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "gender": u.gender,
                "age": u.age,
                "height": u.height,
                "goal_type": u.goal_type,
                "medical_conditions": u.medical_conditions,
                "preferred_exercises": u.preferred_exercises,
                "has_inbody": u.inbody_data is not None
            } for u in users
        ]
    }

@app.put("/api/users/{user_id}/goal", response_model=UserResponse)
async def update_user_goal(user_id: int, goal_data: UserGoalUpdate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    # 업데이트할 필드가 있으면 업데이트
    if goal_data.start_weight is not None:
        user.start_weight = goal_data.start_weight
    if goal_data.target_weight is not None:
        user.target_weight = goal_data.target_weight
    if goal_data.goal_type is not None:
        user.goal_type = goal_data.goal_type
    if goal_data.goal_description is not None:
        user.goal_description = goal_data.goal_description
    
    try:
        db.commit()
        db.refresh(user)
        print(f"✅ 사용자 목표 수정 성공: {user.email}")
        return user
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"목표 수정 중 오류 발생: {str(e)}")

@app.post("/api/users/{user_id}/records", response_model=UserResponse)
async def update_user_records(user_id: int, record_data: UserRecordUpdate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    # daily_records JSON 구조: {"2026-01-29": {"food": [], "exercise": []}}
    current_records = user.daily_records or {}
    date_key = record_data.date
    
    if date_key not in current_records:
        current_records[date_key] = {"food": [], "exercise": []}
    
    if record_data.food is not None:
        current_records[date_key]["food"] = record_data.food
    if record_data.exercise is not None:
        current_records[date_key]["exercise"] = record_data.exercise
        
    user.daily_records = current_records
    
    try:
        db.commit()
        db.refresh(user)
        print(f"✅ 사용자 일일 기록 업데이트 성공: {user.email} (날짜: {date_key})")
        return user
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"기록 업데이트 중 오류 발생: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)