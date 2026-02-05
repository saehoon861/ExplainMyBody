"""
체형 분류 서비스
rule_based_bodytype 로직 통합
"""

from typing import Dict, Any, Optional
from schemas.body_type import BodyTypeAnalysisInput, BodyTypeAnalysisOutput
from core.rule_based_bodytype.body_analysis.pipeline import BodyCompositionAnalyzer


class BodyTypeService:
    """체형 분류 서비스"""
    
    def __init__(self):
        """체형 분석기 초기화"""
        try:
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
            print(f"🔍 [BodyTypeService] Analyzer input data: {user_data}")
            
            # 체형 분석 실행
            analysis_result = self.analyzer.analyze_full_pipeline(user_data)
            print(f"🔍 [BodyTypeService] Analysis result: {analysis_result}")
            
            # 수정: stage2_근육보정체형 → stage2
            if analysis_result and "stage2" in analysis_result:
                return analysis_result["stage2"]
            
            return None
        
        except Exception as e:
            print(f"⚠️  체형 분류 중 오류 발생: {e}")
            return None
    
    def _convert_to_analyzer_format(self, input_data: BodyTypeAnalysisInput) -> Dict[str, Any]:
        # 기존에 구상해두었던 input data의 변수명과, 데이터 형식을 확정지을 때의 변수명이 달라
        # 이 함수를 통해 변수명을 통일해주는 과정이 필요해 추가함.
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
            "muscle_seg": input_data.muscle_seg.model_dump(),
            "fat_seg": input_data.fat_seg.model_dump()
        }
        
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
            print(f"🔍 [BodyTypeService] get_full_analysis called with input: {input_data}")
            user_data = self._convert_to_analyzer_format(input_data)
            print(f"🔍 [BodyTypeService] Converted input for analyzer: {user_data}")
            
            result = self.analyzer.analyze_full_pipeline(user_data)
            print(f"🔍 [BodyTypeService] Full analysis pipeline result: {result}")
            
            if result and "stage2" in result and "stage3" in result:
                return BodyTypeAnalysisOutput(**result)
            
            return None
        except Exception as e:
            print(f"⚠️  체형 분석 중 오류 발생: {e}")
            return None
