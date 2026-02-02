"""
OCR 서비스
인바디 이미지에서 데이터 추출 및 Pydantic 검증

OCR 처리 흐름:
1. 이미지 업로드 → 임시 파일 저장
2. InBodyMatcher로 OCR 수행 → raw 결과 (Dict[str, str])
3. get_structured_results()로 구조화 → 중첩 딕셔너리
4. _convert_types()로 타입 변환 → 숫자/정수 변환
5. InBodyData Pydantic 모델로 검증

팀원 코드 출처: backend_temp/inbody_matcher.py → backend/services/ocr/inbody_matcher.py로 이동
"""

import os
import tempfile
import shutil
from typing import Dict, Any, Optional, Union, BinaryIO

from pydantic import ValidationError

from schemas.inbody import InBodyData
from exceptions import (
    OCREngineNotInitializedError,
    OCRExtractionFailedError,
    OCRProcessingError
)


class OCRService:
    """
    OCR 처리 서비스
    
    팀원 코드(backend_temp)의 InBodyMatcher 클래스를 사용하여
    인바디 이미지에서 데이터를 추출하고 Pydantic 스키마로 검증합니다.
    """
    
    def __init__(self):
        """
        OCR 엔진 초기화
        
        InBodyMatcher 클래스 import 및 인스턴스 생성
        - auto_perspective: 자동 원근 변환 (기울어진 문서 보정)
        - skew_threshold: 기울기 임계값 (기본 15.0)
        """
        try:
            # 팀원 코드: backend_temp/inbody_matcher.py → backend/services/ocr/inbody_matcher.py
            from services.ocr.inbody_matcher import InBodyMatcher
            
            self.matcher = InBodyMatcher(
                auto_perspective=True,
                skew_threshold=15.0
            )
            print("✅ OCR 엔진 (InBodyMatcher) 초기화 완료")
            
        except ImportError as e:
            print(f"⚠️ InBodyMatcher import 실패: {e}")
            print("   PaddleOCR 및 관련 의존성이 설치되어 있는지 확인하세요.")
            self.matcher = None
            
        except Exception as e:
            print(f"⚠️ OCR 엔진 초기화 실패: {e}")
            self.matcher = None
    
    async def extract_inbody_data(self, image_file: BinaryIO, filename: str = "image.jpg") -> dict:
        """
        인바디 이미지에서 데이터 추출 (OCR만 수행, 검증 없음)
        
        처리 흐름:
        1. 업로드된 이미지를 임시 파일로 저장
        2. InBodyMatcher.extract_and_match()로 OCR 수행
           - 팀원 코드: 이미지에서 텍스트 추출 및 키-값 매칭
           - 반환값: Dict[str, Optional[str]] (모든 값이 문자열)
        3. InBodyMatcher.get_structured_results()로 구조화
           - 팀원 코드: flat dict → 중첩 dict 변환
           - 반환값: {"기본정보": {...}, "체성분": {...}, ...}
        4. _convert_types()로 타입 변환
           - 문자열 → float/int 변환
        5. ⚠️ Pydantic 검증 없이 dict 그대로 반환
           - 프론트엔드에서 사용자가 수정할 수 있도록 원시 데이터 제공
        
        Args:
            image_file: 업로드된 인바디 이미지 (BinaryIO - 파일 객체)
            filename: 파일명 (기본값: "image.jpg")
            
        Returns:
            dict: OCR로 추출된 원시 데이터 (검증 없음)
            - 빈 값(None)이 있을 수 있음
            - 이상치 값이 있을 수 있음
            - 프론트엔드에서 사용자가 검증/수정 필요
            
        Raises:
            OCREngineNotInitializedError: OCR 엔진 미초기화
            OCRExtractionFailedError: OCR 결과 추출 실패
            OCRProcessingError: OCR 처리 중 오류 발생
        """
        # OCR 엔진 확인
        if not self.matcher:
            raise OCREngineNotInitializedError(
                "OCR 엔진이 초기화되지 않았습니다. 서버 로그를 확인하세요."
            )
        
        # Step 1: 임시 파일로 저장
        # 팀원 코드(InBodyMatcher)가 파일 경로를 받으므로 임시 파일 생성 필요
        tmp_path = None
        try:
            # 파일 확장자 추출 (없으면 .jpg 사용)
            file_ext = os.path.splitext(filename)[1] or ".jpg"
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
                shutil.copyfileobj(image_file, tmp_file)
                tmp_path = tmp_file.name
            
            print(f"📁 임시 파일 저장: {tmp_path}")
            
            # Step 2: OCR 수행
            # 팀원 함수: InBodyMatcher.extract_and_match(image_path: str) -> Dict[str, Optional[str]]
            raw_result = self.matcher.extract_and_match(tmp_path)
            
            if not raw_result:
                raise OCRExtractionFailedError(
                    "OCR 결과를 추출할 수 없습니다. 이미지를 확인해주세요."
                )
            
            # Step 3: 구조화
            # 팀원 함수: InBodyMatcher.get_structured_results(results: Dict) -> Dict
            # 팀원 코드의 키 이름과 우리 스키마의 키 이름 매핑:
            #   - 팀원: "왼쪽팔 근육" → 우리: 부위별근육분석.왼쪽팔
            #   - 팀원: "왼쪽팔 체지방" → 우리: 부위별체지방분석.왼쪽팔
            structured_result = self.matcher.get_structured_results(raw_result)
            
            # Step 4: 타입 변환 (생략)
            # 프론트엔드에서 .replace() 등을 사용하므로 문자열 그대로 반환 (Pydantic 검증 시 자동 변환됨)
            # mapped_result = self._convert_types(structured_result)
            
            print(f"✅ OCR 추출 완료 (검증 없음)")
            print(f"⚠️ 프론트엔드에서 사용자 검증 필요")
            
            # Step 5: 검증 없이 dict 그대로 반환
            return structured_result
        
        except (OCREngineNotInitializedError, OCRExtractionFailedError):
            # 커스텀 예외는 그대로 전달
            raise
        
        except Exception as e:
            raise OCRProcessingError(
                f"OCR 처리 중 오류 발생: {str(e)}"
            )
        
        finally:
            # 임시 파일 삭제
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                    print(f"🗑️ 임시 파일 삭제: {tmp_path}")
                except Exception as e:
                    print(f"⚠️ 임시 파일 삭제 실패: {e}")
    
    def _convert_types(self, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        OCR 결과의 문자열 값을 Pydantic 스키마에 맞는 타입으로 변환
        
        팀원 코드(InBodyMatcher)는 모든 값을 문자열로 반환하지만,
        우리의 InBodyData 스키마는 숫자 타입을 기대합니다.
        
        타입 변환 규칙:
        - 기본정보.신장: str → float (예: "170" → 170.0)
        - 기본정보.연령: str → int (예: "30" → 30)
        - 기본정보.성별: str → str (변환 없음)
        - 체성분.*: str → float
        - 체중관리.*: str → float
        - 비만분석.내장지방레벨: str → int
        - 비만분석.비만도: str → int
        - 연구항목.기초대사량: str → int
        - 연구항목.권장섭취열량: str → int
        - 부위별*분석.*: str → str (변환 없음, "표준", "표준이상" 등)
        
        Args:
            structured_data: InBodyMatcher.get_structured_results() 반환값
            
        Returns:
            타입 변환된 딕셔너리 (InBodyData 생성자에 전달 가능)
        """
        result = {}
        
        # 기본정보 (신장: float, 연령: int, 성별: str)
        if "기본정보" in structured_data:
            info = structured_data["기본정보"]
            result["기본정보"] = {
                "신장": self._to_float(info.get("신장")),
                "연령": self._to_int(info.get("연령")),
                "성별": info.get("성별")  # 문자열 유지
            }
        
        # 체성분 (전부 float)
        if "체성분" in structured_data:
            comp = structured_data["체성분"]
            result["체성분"] = {
                "체수분": self._to_float(comp.get("체수분")),
                "단백질": self._to_float(comp.get("단백질")),
                "무기질": self._to_float(comp.get("무기질")),
                "체지방": self._to_float(comp.get("체지방")),
            }
        
        # 체중관리 (전부 float)
        if "체중관리" in structured_data:
            weight = structured_data["체중관리"]
            result["체중관리"] = {
                "체중": self._to_float(weight.get("체중")),
                "골격근량": self._to_float(weight.get("골격근량")),
                "체지방량": self._to_float(weight.get("체지방량")),
                "적정체중": self._to_float(weight.get("적정체중")),
                "체중조절": self._to_float(weight.get("체중조절")),
                "지방조절": self._to_float(weight.get("지방조절")),
                "근육조절": self._to_float(weight.get("근육조절")),
            }
        
        # 비만분석 (BMI, 체지방률, 복부지방률: float / 내장지방레벨, 비만도: int)
        if "비만분석" in structured_data:
            obesity = structured_data["비만분석"]
            result["비만분석"] = {
                "BMI": self._to_float(obesity.get("BMI")),
                "체지방률": self._to_float(obesity.get("체지방률")),
                "복부지방률": self._to_float(obesity.get("복부지방률")),
                "내장지방레벨": self._to_int(obesity.get("내장지방레벨")),
                "비만도": self._to_int(obesity.get("비만도")),
            }
        
        # 연구항목 (제지방량: float / 기초대사량, 권장섭취열량: int)
        if "연구항목" in structured_data:
            research = structured_data["연구항목"]
            result["연구항목"] = {
                "제지방량": self._to_float(research.get("제지방량")),
                "기초대사량": self._to_int(research.get("기초대사량")),
                "권장섭취열량": self._to_int(research.get("권장섭취열량")),
            }
        
        # 부위별근육분석 (전부 str - "표준", "표준이상", "표준이하")
        # 팀원 코드 키: "왼쪽팔 근육" → 우리 스키마: 부위별근육분석.왼쪽팔
        if "부위별근육분석" in structured_data:
            result["부위별근육분석"] = structured_data["부위별근육분석"].copy()
        
        # 부위별체지방분석 (전부 str)
        # 팀원 코드 키: "왼쪽팔 체지방" → 우리 스키마: 부위별체지방분석.왼쪽팔
        if "부위별체지방분석" in structured_data:
            result["부위별체지방분석"] = structured_data["부위별체지방분석"].copy()
        
        return result
    
    def _to_float(self, value: Optional[str]) -> Optional[float]:
        """
        문자열을 float로 변환
        
        팀원 코드는 숫자를 문자열로 반환 (예: "77.7")
        None, "미검출", 빈 문자열은 None 반환
        
        Args:
            value: 변환할 문자열 값
            
        Returns:
            변환된 float 또는 None
        """
        if value is None or value == "" or value == "미검출":
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _to_int(self, value: Optional[str]) -> Optional[int]:
        """
        문자열을 int로 변환
        
        팀원 코드는 숫자를 문자열로 반환 (예: "30")
        소수점이 있으면 float로 변환 후 int로 캐스팅
        
        Args:
            value: 변환할 문자열 값
            
        Returns:
            변환된 int 또는 None
        """
        if value is None or value == "" or value == "미검출":
            return None
        try:
            # "30.0" 같은 경우도 처리
            return int(float(value))
        except (ValueError, TypeError):
            return None
