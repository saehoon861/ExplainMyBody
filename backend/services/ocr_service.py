"""
OCR 서비스
인바디 이미지에서 데이터 추출 및 Pydantic 검증
"""

import sys
import os

# 기존 OCR 코드 경로 추가
# 추후에 각 기능의 파일 코드들을 정리할 때 삭제나 수정 필요 #fixme
sys.path.append(os.path.join(os.path.dirname(__file__), "../../src/OCR"))

from typing import Dict, Any
from fastapi import UploadFile, HTTPException
from pydantic import ValidationError
import tempfile
import shutil

from schemas.inbody import InBodyData


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
    
    async def extract_inbody_data(self, image_file: UploadFile) -> InBodyData:
        """
        인바디 이미지에서 데이터 추출 및 Pydantic 모델 변환
        
        Args:
            image_file: 업로드된 이미지 파일
            
        Returns:
            InBodyData: 검증된 인바디 데이터 Pydantic 모델
            
        Raises:
            HTTPException: OCR 실패 또는 필수 필드 누락 시
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
            # OCR 실행 (Dict 반환)
            # TODO: 팀원이 작성한 OCR 코드가 여기서 실행됨
            raw_result = self.matcher.extract_and_match(tmp_path)
            
            # OCR 결과의 키 이름을 Pydantic 필드명으로 매핑
            mapped_result = self._map_ocr_keys(raw_result)
            
            # Pydantic 모델로 변환 (자동 검증)
            inbody_data = InBodyData(**mapped_result)
            
            return inbody_data
        
        except ValidationError as e:
            # 필수 필드 누락 또는 타입 오류
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "OCR 추출 데이터 검증 실패",
                    "errors": e.errors()
                }
            )
        
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"OCR 처리 중 오류 발생: {str(e)}"
            )
        
        finally:
            # 임시 파일 삭제
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    def _map_ocr_keys(self, ocr_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        OCR 결과의 키 이름을 Pydantic 스키마에 맞게 변환
        
        팀원이 작성한 OCR 코드의 출력 형식에 맞춰 수정 필요
        
        예시 매핑:
        - "왼쪽팔 근육" → "왼쪽팔_근육"
        - "오른쪽팔 근육" → "오른쪽팔_근육"
        - 공백을 언더스코어로 변경
        
        Args:
            ocr_result: extract_and_match의 원본 반환값
            
        Returns:
            Pydantic 스키마에 맞게 매핑된 딕셔너리
        """
        mapped = {}
        
        for key, value in ocr_result.items():
            # None 값은 제외 (선택적 필드)
            if value is None:
                continue
            
            # 공백을 언더스코어로 변경
            new_key = key.replace(" ", "_")
            
            # TODO: 팀원의 OCR 코드 출력 형식에 맞춰 추가 매핑 로직 작성
            # 예: "왼쪽팔 근육" → "왼쪽팔_근육"
            # 예: "오른쪽하체 근육" → "오른쪽하체_근육"
            
            mapped[new_key] = value
        
        return mapped

