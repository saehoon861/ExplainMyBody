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
    
    _matcher = None
    
    def __init__(self):
        """OCR 엔진 초기화 (최초 1회만)"""
        # 이미 초기화되었으면 스킵
        if OCRService._matcher is not None:
            return
        
        try:
            print("🔄 OCRService 초기화 중...")
            
            # 기존 OCR 코드 임포트
            from inbody_matcher import InBodyMatcher
            
            # InBodyMatcher 초기화 (PaddleOCR 포함)
            OCRService._matcher = InBodyMatcher(
                auto_perspective=True,
                skew_threshold=15.0
            )
            
            print("✅ OCRService 초기화 완료")
            
        except ImportError as e:
            print(f"❌ inbody_matcher.py 임포트 실패: {e}")
            raise Exception(f"OCR 모듈을 찾을 수 없습니다: {e}")
        
        except Exception as e:
            print(f"❌ OCR 엔진 초기화 실패: {e}")
            import traceback
            traceback.print_exc()
            raise Exception(f"OCR 엔진 초기화 실패: {e}")
    
    @property
    def matcher(self):
        """InBodyMatcher 인스턴스 반환"""
        if OCRService._matcher is None:
            raise Exception("OCR 엔진이 초기화되지 않았습니다.")
        return OCRService._matcher
    
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
        """
        # 구조화된 결과 사용
        structured_result = self.matcher.get_structured_results(ocr_result)
        
        mapped = {
            # 기본 정보
            "신장": self._safe_float(ocr_result.get("신장")),
            "연령": self._safe_int(ocr_result.get("연령")),
            "성별": ocr_result.get("성별"),
            
            # 체성분
            "체수분": self._safe_float(ocr_result.get("체수분")),
            "단백질": self._safe_float(ocr_result.get("단백질")),
            "무기질": self._safe_float(ocr_result.get("무기질")),
            "체지방": self._safe_float(ocr_result.get("체지방")),
            
            # 체중 관리
            "체중": self._safe_float(ocr_result.get("체중")),
            "골격근량": self._safe_float(ocr_result.get("골격근량")),
            "체지방량": self._safe_float(ocr_result.get("체지방량")),
            "적정체중": self._safe_float(ocr_result.get("적정체중")),
            "체중조절": self._safe_float(ocr_result.get("체중조절")),
            "지방조절": self._safe_float(ocr_result.get("지방조절")),
            "근육조절": self._safe_float(ocr_result.get("근육조절")),
            
            # 비만 분석
            "BMI": self._safe_float(ocr_result.get("BMI")),
            "체지방률": self._safe_float(ocr_result.get("체지방률")),
            "복부지방률": self._safe_float(ocr_result.get("복부지방률")),
            "내장지방레벨": self._safe_int(ocr_result.get("내장지방레벨")),
            "비만도": self._safe_int(ocr_result.get("비만도")),
            
            # 연구 항목
            "제지방량": self._safe_float(ocr_result.get("제지방량")),
            "기초대사량": self._safe_int(ocr_result.get("기초대사량")),
            "권장섭취열량": self._safe_int(ocr_result.get("권장섭취열량")),
            
            # 부위별 근육 분석 (공백 → 언더스코어)
            "왼쪽팔_근육": ocr_result.get("왼쪽팔 근육"),
            "오른쪽팔_근육": ocr_result.get("오른쪽팔 근육"),
            "복부_근육": ocr_result.get("복부 근육"),
            "왼쪽하체_근육": ocr_result.get("왼쪽하체 근육"),
            "오른쪽하체_근육": ocr_result.get("오른쪽하체 근육"),
            
            # 부위별 체지방 분석
            "왼쪽팔_체지방": ocr_result.get("왼쪽팔 체지방"),
            "오른쪽팔_체지방": ocr_result.get("오른쪽팔 체지방"),
            "복부_체지방": ocr_result.get("복부 체지방"),
            "왼쪽하체_체지방": ocr_result.get("왼쪽하체 체지방"),
            "오른쪽하체_체지방": ocr_result.get("오른쪽하체 체지방"),
        }
        
        # None 값 제거
        mapped = {k: v for k, v in mapped.items() if v is not None}
        
        return mapped
    
    def _safe_float(self, value: Any) -> Optional[float]:
        """안전한 float 변환"""
        if value is None or value == "미검출":
            return None
        try:
            if isinstance(value, str):
                value = value.replace("+", "").replace(" ", "")
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _safe_int(self, value: Any) -> Optional[int]:
        """안전한 int 변환"""
        if value is None or value == "미검출":
            return None
        try:
            if isinstance(value, str):
                value = value.replace("+", "").replace(" ", "")
            return int(float(value))
        except (ValueError, TypeError):
            return None
