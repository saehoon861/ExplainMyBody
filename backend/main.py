"""
FastAPI 메인 애플리케이션
ExplainMyBody 백엔드 서버
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database import init_db
from routers.common import auth_router, users_router
from routers.ocr import health_records_router
from routers.llm import analysis_router, details_router as detail_router, weekly_plans_router
# from routers import chatbot_router



@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시 데이터베이스 초기화 (빠름)
    print("🚀 ExplainMyBody 백엔드 서버 시작 중...")
    init_db()
    print("✅ 데이터베이스 초기화 완료")
    
    # OCR 엔진 백그라운드 로딩 시작 (비동기)
    print("🔄 OCR 엔진 로딩 중... (백그라운드)")
    
    async def load_ocr_engine():
        """OCR 엔진을 백그라운드에서 로드"""
        from services.ocr.ocr_service import OCRService
        from app_state import AppState
        
        AppState.ocr_service = OCRService()
        print("✅ OCR 엔진 로딩 완료")
    
    # 백그라운드 태스크로 OCR 로딩 (서버 시작 차단 안 함)
    import asyncio
    asyncio.create_task(load_ocr_engine())
    
    print("✅ 서버 시작 완료 (OCR은 백그라운드에서 로딩 중)")

    yield
    
    # 종료 시 정리 작업
    print("👋 서버 종료 중...")

#규민 수정 외부 접속을 위한
origins = [
    "https://garlic-declare-detective-executives.trycloudflare.com", # 프론트엔드 터널 주소
    "http://localhost:5173", # 로컬 테스트용
]
# FastAPI 앱 생성
app = FastAPI(
    title="ExplainMyBody API",
    description="인바디 분석 및 건강 관리 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정 (프론트엔드 연결)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # origins 리스트 사용 (localhost + 터널 주소)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth_router, prefix="/api/auth", tags=["인증"])
app.include_router(users_router, prefix="/api/users", tags=["사용자"])
app.include_router(health_records_router, prefix="/api/health-records", tags=["건강 기록"])
app.include_router(analysis_router, prefix="/api/analysis", tags=["분석"])
app.include_router(detail_router, prefix="/api/details", tags=["목표 및 상세 정보"])
app.include_router(weekly_plans_router, prefix="/api/weekly-plans", tags=["주간 계획"])
# app.include_router(chatbot_router, prefix="/api/chatbot", tags=["챗봇"])


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "ExplainMyBody API 서버",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/api/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    from database import get_db
    
    try:
        from sqlalchemy import text
        db = next(get_db())
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # 개발 모드에서만 사용
    )
