"""
체형 분류 서비스
rule_based_bodytype 로직 통합
"""

import sys
import os

# 기존 체형 분류 코드 경로 추가
# 추후에 각 기능의 파일 코드들을 정리할 때 삭제나 수정 필요 #fixme
# backend/services/ocr/ → backend/ → ExplainMyBody/ → src/rule_based_bodytype
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../src/rule_based_bodytype"))

from typing import Dict, Any, Optional
from schemas.body_type import BodyTypeAnalysisInput, BodyTypeAnalysisOutput


class BodyTypeService:
    """체형 분류 서비스"""
    
    def __init__(self):
        """체형 분석기 초기화"""
        try:
            from body_analysis.pipeline import BodyCompositionAnalyzer
            self.analyzer = BodyCompositionAnalyzer(margin=0.10)
        except Exception as e:
            print(f"⚠️  체형 분석기 초기화 실패: {e}")
            self.analyzer = None
    
    def classify_body_type(self, input_data: BodyTypeAnalysisInput) -> Optional[str]:
        """
        인바디 데이터를 기반으로 체형 분류
        
        Args:
            input_data: BodyTypeAnalysisInput (Pydantic 검증 완료)
            
        Returns:
            근육 보정 체형 (stage2) - 예: "비만형", "표준형", "근육형"
            분석 실패 시 None
        """
        if not self.analyzer:
            print("⚠️  체형 분석기를 사용할 수 없습니다.")
            return None
        
        try:
            # Pydantic 모델을 분석기 입력 형식으로 변환
            user_data = self._convert_to_analyzer_format(input_data)
            
            # 체형 분석 실행
            analysis_result = self.analyzer.analyze_full_pipeline(user_data)
            
            # 수정: stage2_근육보정체형 → stage2
            if analysis_result and "stage2" in analysis_result:
                return analysis_result["stage2"]
            
            return None
        
        except Exception as e:
            print(f"⚠️  체형 분류 중 오류 발생: {e}")
            return None
    
    def _convert_to_analyzer_format(self, input_data: BodyTypeAnalysisInput) -> Dict[str, Any]:
        """
        Pydantic 검증된 데이터를 분석기 입력 형식으로 변환
        
        Args:
            input_data: BodyTypeAnalysisInput Pydantic 모델 (이미 검증됨)
            
        Returns:
            분석기 입력 형식의 데이터
        """
        # 기본값 없이 Pydantic 모델에서 직접 가져옴
        user_data = {
            "sex": input_data.성별,
            "age": input_data.연령,
            "height_cm": input_data.신장,
            "weight_kg": input_data.체중,
            "bmi": input_data.BMI,
            "fat_rate": input_data.체지방률,
            "smm": input_data.골격근량,
        }
        
        # 부위별 데이터가 있으면 추가 (선택적)
        if input_data.muscle_seg:
            user_data["muscle_seg"] = input_data.muscle_seg.model_dump()
        if input_data.fat_seg:
            user_data["fat_seg"] = input_data.fat_seg.model_dump()
        
        return user_data
    
    def get_full_analysis(self, input_data: BodyTypeAnalysisInput) -> Optional[BodyTypeAnalysisOutput]:
        """
        전체 체형 분석 결과 반환
        
        Args:
            input_data: BodyTypeAnalysisInput (Pydantic 검증 완료)
            
        Returns:
            BodyTypeAnalysisOutput: {'stage2': str, 'stage3': str}
            분석 실패 시 None
        """
        if not self.analyzer:
            return None
        
        try:
            user_data = self._convert_to_analyzer_format(input_data)
            result = self.analyzer.analyze_full_pipeline(user_data)
            
            if result and "stage2" in result and "stage3" in result:
                return BodyTypeAnalysisOutput(**result)
            
            return None
        except Exception as e:
            print(f"⚠️  체형 분석 중 오류 발생: {e}")
            return None
