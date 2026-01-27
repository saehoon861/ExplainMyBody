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
        # TODO: 팀원의 OCR 코드 통합 시 활성화
        # try:
        #     from ocr_test import InBodyMatcher
        #     self.matcher = InBodyMatcher()
        # except Exception as e:
        #     print(f"⚠️  OCR 엔진 초기화 실패: {e}")
        #     self.matcher = None
        
        # 임시: OCR 엔진 없이 샘플 데이터 사용
        self.matcher = None
        print("⚠️  OCR 엔진 미사용 - 샘플 데이터 모드")
    
    async def extract_inbody_data(self, image_file: UploadFile) -> InBodyData:
        """
        인바디 이미지에서 데이터 추출 및 Pydantic 모델 변환
        
        현재는 OCR 엔진 없이 샘플 데이터를 반환합니다.
        팀원의 OCR 코드 통합 후 실제 OCR 로직으로 교체 예정
        
        Args:
            image_file: 업로드된 이미지 파일
            
        Returns:
            InBodyData: 검증된 인바디 데이터 Pydantic 모델
            
        Raises:
            HTTPException: OCR 실패 또는 필수 필드 누락 시 - 이거는 진행 안함. #fixme

        """
        # 임시: 샘플 데이터 반환 (OCR 엔진 없이 API 로직 검증용)
        try:
            sample_data = {
                "기본정보": {
                    "신장": 170,
                    "연령": 30,
                    "성별": "남성"
                },
                "체성분": {
                    "체수분": 41.7,
                    "단백질": 11.4,
                    "무기질": 3.99,
                    "체지방": 20.6
                },
                "체중관리": {
                    "체중": 77.7,
                    "골격근량": 32.5,
                    "체지방량": 20.6,
                    "적정체중": 67.2,
                    "체중조절": None,  # null 값 - 사용자 검증 필요
                    "지방조절": -10.5,
                    "근육조절": 0.0
                },
                "비만분석": {
                    "BMI": 26.9,
                    "체지방률": 26.5,
                    "복부지방률": 0.93,
                    "내장지방레벨": 8,
                    "비만도": 122
                },
                "연구항목": {
                    "제지방량": 57.1,
                    "기초대사량": 1603,
                    "권장섭취열량": 2267
                },
                "부위별근육분석": {
                    "왼쪽팔": "표준",
                    "오른쪽팔": "표준",
                    "복부": "표준",
                    "왼쪽하체": "표준",
                    "오른쪽하체": "표준"
                },
                "부위별체지방분석": {
                    "왼쪽팔": "표준이상",
                    "오른쪽팔": "표준이상",
                    "복부": "표준이상",
                    "왼쪽하체": "표준이상",
                    "오른쪽하체": "표준이상"
                }
            }
            
            # Pydantic 모델로 변환 (자동 검증)
            inbody_data = InBodyData(**sample_data)
            
            print(f"✅ 샘플 데이터 생성 완료")
            print(f"⚠️  null 필드: {inbody_data.get_null_fields()}")
            
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
        
        # TODO: 팀원의 OCR 코드 통합 시 아래 코드 활성화
        # if not self.matcher:
        #     raise HTTPException(
        #         status_code=500,
        #         detail="OCR 엔진이 초기화되지 않았습니다."
        #     )
        # 
        # # 임시 파일로 저장
        # with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
        #     shutil.copyfileobj(image_file.file, tmp_file)
        #     tmp_path = tmp_file.name
        # 
        # try:
        #     # OCR 실행 (Dict 반환)
        #     raw_result = self.matcher.extract_and_match(tmp_path)
        #     
        #     # OCR 결과의 키 이름을 Pydantic 필드명으로 매핑
        #     mapped_result = self._map_ocr_keys(raw_result)
        #     
        #     # Pydantic 모델로 변환 (자동 검증)
        #     inbody_data = InBodyData(**mapped_result)
        #     
        #     return inbody_data
        # 
        # except ValidationError as e:
        #     raise HTTPException(
        #         status_code=422,
        #         detail={
        #             "message": "OCR 추출 데이터 검증 실패",
        #             "errors": e.errors()
        #         }
        #     )
        # 
        # except Exception as e:
        #     raise HTTPException(
        #         status_code=500,
        #         detail=f"OCR 처리 중 오류 발생: {str(e)}"
        #     )
        # 
        # finally:
        #     # 임시 파일 삭제
        #     if os.path.exists(tmp_path):
        #         os.remove(tmp_path)
    
    def _map_ocr_keys(self, ocr_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        OCR 결과의 키 이름을 Pydantic 스키마에 맞게 변환
        
        팀원이 작성한 OCR 코드의 출력 형식에 맞춰 수정 필요
        
        Args:
            ocr_result: extract_and_match의 원본 반환값
            
        Returns:
            Pydantic 스키마에 맞게 매핑된 딕셔너리
        """
        # TODO: 팀원의 OCR 코드 출력 형식에 맞춰 매핑 로직 작성
        # 예시:
        # - OCR 출력이 flat한 구조라면 중첩 구조로 변환
        # - 키 이름 정규화 (공백 → 언더스코어 등)
        
        mapped = {
            "기본정보": {},
            "체성분": {},
            "체중관리": {},
            "비만분석": {},
            "연구항목": {},
            "부위별근육분석": {},
            "부위별체지방분석": {}
        }
        
        # OCR 결과를 적절한 섹션에 매핑
        for key, value in ocr_result.items():
            if value is None:
                continue
            
            # TODO: 키 이름에 따라 적절한 섹션에 할당
            # 예: "신장" → mapped["기본정보"]["신장"] = value
            
        return mapped

