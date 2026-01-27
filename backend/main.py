"""
FastAPI 메인 애플리케이션
ExplainMyBody 백엔드 서버
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database import init_db
from routers import auth, users, health_records, analysis, goals


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시 데이터베이스 초기화 (빠름)
    print("🚀 ExplainMyBody 백엔드 서버 시작 중...")
    init_db()
    print("✅ 데이터베이스 초기화 완료")
    #fixme : OCR 모델과 LLM 엔진을 로드해야 한다면 lifespan() 안에 넣어주는 것이 좋다.
    # 서버 시작 시 무거운 AI 모델 로드 (딱 한 번만 실행) 해주기 때문.
    # 예시: ocr_model = load_ocr_model() 
    #       llm_engine = load_llm_engine() 

    # 💡 한 가지 조언 (AI OCR 연동 관련)
    # 현재 lifespan에서 init_db()만 하고 있는데, 
    # 나중에 ExplainMyBody의 핵심인 OCR 모델이나 LLM 엔진을 로드해야 한다면 
    # 해당 모델들을 lifespan() 안에 넣어주는 것이 좋습니다.
    # OCR 엔진 백그라운드 로딩 시작 (비동기)
    print("🔄 OCR 엔진 로딩 중... (백그라운드)")
    
    async def load_ocr_engine():
        """OCR 엔진을 백그라운드에서 로드"""
        from services.ocr_service import OCRService
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
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router, prefix="/api/auth", tags=["인증"])
app.include_router(users.router, prefix="/api/users", tags=["사용자"])
app.include_router(health_records.router, prefix="/api/health-records", tags=["건강 기록"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["분석"])
app.include_router(goals.router, prefix="/api/goals", tags=["목표"])


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
        db = next(get_db())
        db.execute("SELECT 1")
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
