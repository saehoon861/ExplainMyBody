# app.py (FastAPI 버전)
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import os
import tempfile
import json
from pathlib import Path

from inbody_matcher import InBodyMatcher

app = FastAPI(title="InBody OCR API")

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
MAX_FILE_SIZE = 16 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.get("/")
async def root():
    """루트 경로"""
    return {
        "message": "InBody OCR API",
        "docs": "/docs",
        "health": "/api/health"
    }

@app.get("/api/health")
async def health_check():
    """서버 상태 확인"""
    return {
        "status": "healthy",
        "service": "InBody OCR API (FastAPI)"
    }


@app.post("/api/process")
async def process_inbody(
    image: UploadFile = File(...),
    auto_perspective: bool = Form(True),
    skew_threshold: float = Form(15.0)
):
    """InBody 이미지 처리 API"""
    
    # 파일 확장자 확인
    if not image.filename:
        raise HTTPException(400, "파일이 선택되지 않았습니다")
    
    ext = image.filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"허용되지 않는 파일 형식입니다. 허용: {', '.join(ALLOWED_EXTENSIONS)}")
    
    # 임시 파일 저장
    temp_path = os.path.join(UPLOAD_FOLDER, f"temp_{image.filename}")
    
    try:
        # 파일 저장
        with open(temp_path, "wb") as buffer:
            content = await image.read()
            buffer.write(content)
        
          # OCR 처리
        print(f"📸 파일 업로드: {image.filename}")
        print(f"💾 임시 저장: {temp_path}")
        print("🔍 OCR 처리 시작...")
        
        matcher = InBodyMatcher(
            auto_perspective=auto_perspective,
            skew_threshold=skew_threshold
        )
        
        results = matcher.extract_and_match(temp_path)
        
        if not results:
            raise HTTPException(400, "OCR 결과를 추출할 수 없습니다")
        
        # 구조화된 결과 생성
        structured = matcher.get_structured_results(results)
        
        # 통계 계산
        total_fields = len(results)
        detected_fields = sum(1 for v in results.values() if v is not None and v != "미검출")
        detection_rate = (detected_fields / total_fields * 100) if total_fields > 0 else 0
        
        return {
            "success": True,
            "data": {
                "raw": results,
                "structured": structured
            },
            "stats": {
                "total_fields": total_fields,
                "detected_fields": detected_fields,
                "detection_rate": round(detection_rate, 1)
            },
            "options": {
                "auto_perspective": auto_perspective,
                "skew_threshold": skew_threshold
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Error: {error_detail}")
        raise HTTPException(500, str(e))
    
    finally:
        # 임시 파일 삭제
        if os.path.exists(temp_path):
            os.unlink(temp_path)

@app.post("/api/health-records/ocr/extract")
async def extract_health_record(
    image: UploadFile = File(...),
    auto_perspective: bool = Form(True),
    skew_threshold: float = Form(15.0)
):
    """
    인바디 이미지 OCR 추출
    프론트엔드에서 사용하는 경로
    """
    print(f"\n{'='*60}")
    print(f"📍 엔드포인트: /api/health-records/ocr/extract")
    print(f"📸 파일명: {image.filename}")
    print(f"{'='*60}")
    
    # 기존 process_inbody 함수 재사용
    return await process_inbody(image, auto_perspective, skew_threshold)

    
@app.post("/api/save")
async def save_inbody(data: dict):
    """수정된 인바디 데이터 저장"""
    try:
        # Pydantic 검증 (models.py 필요)
        # from models import InBodyResult
        # validated_data = InBodyResult.from_dict(data)
        
        print("=" * 30)
        print("✅ 데이터 수신 완료")
        print(f"데이터: {data}")
        print("=" * 30)
        
        return {
            "success": True,
            "message": "인바디 데이터가 정상적으로 저장되었습니다."
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/download")
async def download_results(data: dict):
    """결과를 JSON 파일로 다운로드"""
    try:
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            temp_path = f.name
        
        return FileResponse(
            temp_path,
            media_type='application/json',
            filename='inbody_result.json'
        )
    except Exception as e:
        raise HTTPException(500, str(e))


if __name__ == '__main__':
    import uvicorn
    
    print("=" * 60)
    print("InBody OCR Web Server (FastAPI)")
    print("=" * 60)
    print(f"📁 업로드 폴더: {UPLOAD_FOLDER}")
    print(f"📏 최대 파일 크기: {MAX_FILE_SIZE // (1024*1024)}MB")
    print(f"📝 허용 확장자: {', '.join(ALLOWED_EXTENSIONS)}")
    print("=" * 60)
    print("\n서버 시작 중...")
    print("📖 API 문서: http://127.0.0.1:8000/docs")
    
    uvicorn.run(
        "app:app",  # ← 문자열로 변경!
        host="0.0.0.0",
        port=8000,
        reload=True
    )