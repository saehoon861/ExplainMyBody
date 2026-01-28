"""
[통합 분석 파이프라인 (Facade)]

본 모듈은 Facade Pattern을 적용하여 전체 체형 분석 프로세스를 캡슐화한 진입점(Entry Point)입니다.
복잡한 서브 시스템(Metrics, Stages, Segmental) 간의 의존성을 숨기고,
단일 인터페이스(analyze_full_pipeline)를 통해 일관된 분석 및 결과 생성을 오케스트레이션(Orchestration)합니다.
"""

import traceback
from . import constants
from .models import BodyCompositionData
from .metrics import BMIClassifier, BodyFatClassifier, MuscleClassifier
from .stages import Stage1BodyTypeClassifier, Stage2MuscleAdjuster, Stage3BalanceAnalyzer
from .segmental import DataNormalizer

class BodyCompositionAnalyzer:
    """
    [분석 파이프라인 Controller]
    체성분 분석의 전체 라이프사이클을 관리하는 메인 컨트롤러 클래스입니다.
    - Input Validation 및 객체 변환
    - Stage 1 -> 2 -> 3 순차 실행 제어
    - 예외 처리(Exception Handling) 및 Fallback 메커니즘 제공
    - 최종 Output Dictionary 구성
    """
    
    def __init__(self, margin=constants.ValidationLimits.DEFAULT_MARGIN):
        self.margin = margin
    
    def _convert_input_to_object(self, input_data: dict) -> BodyCompositionData:
        """입력 데이터 객체 변환"""
        if isinstance(input_data, dict):
            return BodyCompositionData.from_dict(input_data)
        return input_data

    def analyze_full_pipeline(self, raw_input):
        """전체 체성분 분석 파이프라인 실행"""
        try:
            # 0. 입력 데이터 변환
            data = self._convert_input_to_object(raw_input)
            
            # 데이터 추출
            bmi = data.bmi
            fat_rate = data.fat_rate
            smm = data.smm
            weight = data.weight_kg
            muscle_seg_raw = data.muscle_seg
            fat_seg_raw = data.fat_seg
            
            # 1. 신체 정보 분류
            bmi_value, bmi_cat = BMIClassifier.classify(bmi)
            fat_cat = BodyFatClassifier.classify(fat_rate)
            smm_ratio, muscle_level = MuscleClassifier.classify(smm, weight)

            # 2. 체형 분류 및 보정 (Stage 1 & 2)
            stage1_type = Stage1BodyTypeClassifier.classify(bmi_cat, fat_cat, muscle_level)
            stage2_type = Stage2MuscleAdjuster.adjust(stage1_type, muscle_level)
            
            stage12_result = {
                "bmi": bmi_value,
                "bmi_category": bmi_cat,
                "fat_category": fat_cat,
                "smm_ratio": smm_ratio,
                "muscle_level": muscle_level,
                "stage1_type": stage1_type,
                "stage2_type": stage2_type
            }

            # 3. 데이터 정규화 및 균형 분석 (Stage 3)
            muscle_seg_normalized = DataNormalizer.normalize_muscle_segment(
                muscle_seg_raw, smm, self.margin
            )
            
            fat_seg_normalized = None
            if fat_seg_raw is not None:
                total_fat_kg = data.get_total_fat()
                fat_seg_normalized = DataNormalizer.normalize_fat_segment(
                    fat_seg_raw, total_fat_kg, self.margin
                )
            
            stage3_type = Stage3BalanceAnalyzer.classify(muscle_seg_normalized, fat_seg_normalized)
            
            # 4. 최종 결과 반환
            return {
                "stage2": stage2_type,
                "stage3": stage3_type
            }
            
        except Exception as e:
            print(f"[ERROR] 분석 파이프라인 실행 중 오류 발생: {e}")
            traceback.print_exc()
            
            return {
                "stage2": "알 수 없음",
                "stage3": "알 수 없음"
            }
