"""
OCR 서비스
인바디 이미지에서 데이터 추출
"""

import sys
import os

# 기존 OCR 코드 경로 추가
# 추후에 각 기능의 파일 코드들을 정리할 때 삭제나 수정 필요 #fixme
sys.path.append(os.path.join(os.path.dirname(__file__), "../../scr/ocr"))

from typing import Dict, Any, Optional
from fastapi import UploadFile, HTTPException
import tempfile
import shutil


class OCRService:
    """OCR 처리 서비스"""
    
    def __init__(self):
        """OCR 엔진 초기화"""
        try:
            # 기존 OCR 코드 임포트
            from ocr_test import InBodyMatcher
            self.matcher = InBodyMatcher()
        except Exception as e:
            print(f"⚠️  OCR 엔진 초기화 실패: {e}")
            self.matcher = None
    
    async def extract_inbody_data(self, image_file: UploadFile) -> Dict[str, Any]:
        """
        인바디 이미지에서 데이터 추출
        
        Args:
            image_file: 업로드된 이미지 파일
            
        Returns:
            추출된 인바디 데이터
        """
        if not self.matcher:
            raise HTTPException(
                status_code=500,
                detail="OCR 엔진이 초기화되지 않았습니다."
            )
        
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            shutil.copyfileobj(image_file.file, tmp_file)
            tmp_path = tmp_file.name
        
        try:
            # OCR 실행
            result = self.matcher.extract_and_match(tmp_path)
            
            # 결과 변환 (None 값 제거)
            cleaned_result = {k: v for k, v in result.items() if v is not None}
            
            return cleaned_result
        
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"OCR 처리 중 오류 발생: {str(e)}"
            )
        
        finally:
            # 임시 파일 삭제
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    def validate_ocr_result(self, ocr_data: Dict[str, Any]) -> bool:
        """
        OCR 결과 검증
        필수 필드가 있는지 확인
        """
        required_fields = ["신장", "체중", "BMI"]
        return all(field in ocr_data for field in required_fields)
