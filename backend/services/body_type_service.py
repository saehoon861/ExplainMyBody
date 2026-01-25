"""
체형 분류 서비스
rule_based_bodytype 로직 통합
"""

import sys
import os

# 기존 체형 분류 코드 경로 추가
# 추후에 각 기능의 파일 코드들을 정리할 때 삭제나 수정 필요 #fixme
sys.path.append(os.path.join(os.path.dirname(__file__), "../../rule_based_bodytype"))

from typing import Dict, Any, Optional


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
    
    def classify_body_type(self, measurements: Dict[str, Any]) -> Optional[str]:
        """
        인바디 데이터를 기반으로 체형 분류
        
        Args:
            measurements: 인바디 측정 데이터
            
        Returns:
            체형 분류 결과 (예: "근육형", "비만형" 등)
        """
        if not self.analyzer:
            print("⚠️  체형 분석기를 사용할 수 없습니다.")
            return None
        
        try:
            # 측정 데이터를 분석기 입력 형식으로 변환
            user_data = self._convert_to_analyzer_format(measurements)
            
            # 체형 분석 실행
            analysis_result = self.analyzer.analyze_full_pipeline(user_data)
            
            # 결과에서 체형 정보 추출
            if analysis_result and "stage2_근육보정체형" in analysis_result:
                return analysis_result["stage2_근육보정체형"]
            
            return None
        
        except Exception as e:
            print(f"⚠️  체형 분류 중 오류 발생: {e}")
            return None
    
    def _convert_to_analyzer_format(self, measurements: Dict[str, Any]) -> Dict[str, Any]:
        """
        인바디 측정 데이터를 분석기 입력 형식으로 변환
        
        Args:
            measurements: 원본 측정 데이터
            
        Returns:
            분석기 입력 형식의 데이터
        """
        # 기본값 설정
        # 사용자가 값을 하나라도 입력하지 않았을 때는 아예 체형 분석 로직이 실행되면 안됨.

        user_data = {
            "sex": measurements.get("성별", "남성"),
            "age": int(measurements.get("연령", 25)),
            "height_cm": float(measurements.get("신장", 170)),
            "weight_kg": float(measurements.get("체중", 70)),
            "bmi": float(measurements.get("BMI", 23.0)),
            "fat_rate": float(measurements.get("체지방률", 15.0)),
            "smm": float(measurements.get("골격근량", 30.0)),
        }
        
        # 부위별 근육량 (선택적)
        muscle_seg = {}
        fat_seg = {}
        
        # 부위별 데이터가 있으면 추가
        if "왼쪽팔 근육" in measurements:
            # 부위별 데이터 매핑 로직
            pass
        
        if muscle_seg:
            user_data["muscle_seg"] = muscle_seg
        if fat_seg:
            user_data["fat_seg"] = fat_seg
        
        return user_data
    
    def get_full_analysis(self, measurements: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        전체 체형 분석 결과 반환
        
        Args:
            measurements: 인바디 측정 데이터
            
        Returns:
            전체 분석 결과
        """
        if not self.analyzer:
            return None
        
        try:
            user_data = self._convert_to_analyzer_format(measurements)
            return self.analyzer.analyze_full_pipeline(user_data)
        except Exception as e:
            print(f"⚠️  체형 분석 중 오류 발생: {e}")
            return None
