"""
[단계별 분석 로직 (Analysis Stages)]

체형 분석 알고리즘의 핵심 비즈니스 로직(Core Business Logic)을 단계별로 구현한 모듈입니다.
Rule-based System의 각 Stage가 순차적으로 실행되며 데이터를 구체화합니다.
- Stage 1: 기초 분류 (BMI + Fat)
- Stage 2: 보정 로직 (Muscle Adjustment)
- Stage 3: 종합 분석 (Balance Analysis)
"""

from . import constants as Constants

class Stage1BodyTypeClassifier:
    """
    [Stage 1: 기초 체형 분류기]
    BMI 등급과 체지방률 등급을 결합하여, 1차적인 체형 카테고리를 도출합니다.
    조건 분기(Conditional Branching) 로직을 통해 '마른비만', '근육형 과체중' 같은 복합적인 케이스를 식별합니다.
    """
    
    @staticmethod
    def classify(bmi_cat, fat_cat, smm_cat=None):
        try:
            if bmi_cat == "정상":
                return Stage1BodyTypeClassifier._classify_normal(fat_cat)
            if bmi_cat == "저체중":
                return Stage1BodyTypeClassifier._classify_underweight(fat_cat)
            if bmi_cat == "과체중":
                return Stage1BodyTypeClassifier._classify_overweight(fat_cat)
            if bmi_cat == "비만1단계":
                return Stage1BodyTypeClassifier._classify_obese1(fat_cat, smm_cat)
            if bmi_cat == "비만2단계":
                return Stage1BodyTypeClassifier._classify_obese2(fat_cat, smm_cat)
            if bmi_cat == "고도비만":
                return Stage1BodyTypeClassifier._classify_severe_obese(fat_cat, smm_cat)
            return "알 수 없음"
        except (TypeError, AttributeError):
            return "알 수 없음"
    
    @staticmethod
    def _classify_normal(fat_cat):
        if fat_cat == "표준": return "표준형"
        elif fat_cat == "표준미만": return "마른형"
        else: return "마른비만형"
    
    @staticmethod
    def _classify_underweight(fat_cat):
        if fat_cat in ["과체중", "비만"]: return "마른비만형"
        return "마른형"
    
    @staticmethod
    def _classify_overweight(fat_cat):
        if fat_cat in ["과체중", "비만"]: return "비만형"
        return "근육형"
    
    @staticmethod
    def _classify_obese1(fat_cat, smm_cat):
        if fat_cat == "표준미만" and smm_cat in ["근육 매우 많음", "근육 많음", "근육 충분"]:
            return "근육형"
        return "비만형"
    
    @staticmethod
    def _classify_obese2(fat_cat, smm_cat):
        if fat_cat == "표준미만" and smm_cat in ["근육 매우 많음", "근육 많음"]:
            return "근육형"
        return "비만형"
    
    @staticmethod
    def _classify_severe_obese(fat_cat, smm_cat):
        if fat_cat == "표준미만" and smm_cat in ["근육 매우 많음", "근육 많음"]:
            return "근육형"
        return "고도비만형"


class Stage2MuscleAdjuster:
    """
    [Stage 2: 근육량 보정기]
    Stage 1의 결과(Basic Type)에 근육 발달도(Muscle Level) 정보를 반영하여 최종 체형 정보를 보정(Adjustment)합니다.
    Lookup Table(딕셔너리) 방식을 사용하여 상태 전이 로직을 효율적으로 관리합니다.
    """
    
    ADJUSTMENT_TABLE = {
        "마른형": {
            "근육 적음": "마른형",
            "근육 보통": "마른형",
            "근육 충분": "마른근육형",
            "근육 많음": "근육형",
            "근육 매우 많음": "근육형",
        },
        "표준형": {
            "근육 적음": "마른형",
            "근육 보통": "표준형",
            "근육 충분": "근육형",
            "근육 많음": "근육형",
            "근육 매우 많음": "근육형",
        },
        "근육형": {
            "근육 적음": "비만형",
            "근육 보통": "비만형",
            "근육 충분": "근육형",
            "근육 많음": "고근육체형",
            "근육 매우 많음": "고근육체형",
        },
        "비만형": {
            "근육 적음": "비만형",
            "근육 보통": "비만형",
            "근육 충분": "고근육체형",
            "근육 많음": "고근육체형",
            "근육 매우 많음": "고근육체형",
        },
        "고도비만형": {
            "근육 적음": "고도비만형",
            "근육 보통": "고도비만형",
            "근육 충분": "비만형",
            "근육 많음": "고근육체형",
            "근육 매우 많음": "고근육체형",
        },
        "마른비만형": {
            "근육 적음": "마른비만형",
            "근육 보통": "마른비만형",
            "근육 충분": "표준형",
            "근육 많음": "근육형",
            "근육 매우 많음": "고근육체형",
        }
    }
    
    @staticmethod
    def adjust(stage1_type, muscle_level):
        """
        [체형 보정 로직]
        1단계 분류 결과(BMI+체지방)를 근육량 수준에 따라 재조정합니다.
        
        Logic:
            ADJUSTMENT_TABLE[1단계_체형][근육_상태] -> 최종_체형
            
        Example:
            - 1단계가 '비만형'이어도, 근육이 '매우 많음'이면 -> '고근육체형'으로 변경
            - 1단계가 '표준형'인데, 근육이 '적음'이면 -> '마른형'으로 변경
            
        Args:
            stage1_type (str): Stage 1 분류 결과 (예: "비만형")
            muscle_level (str): 근육량 등급 (예: "근육 많음")
        """
        try:
            adjusted_type = Stage2MuscleAdjuster.ADJUSTMENT_TABLE.get(
                stage1_type, {}
            ).get(muscle_level, stage1_type)
            return adjusted_type if adjusted_type else stage1_type
        except (TypeError, AttributeError, KeyError):
            return stage1_type


class Stage3BalanceAnalyzer:
    """
    [Stage 3: 상하체 밸런스 분석기]
    부위별 근육/체지방 분포 데이터를 집계(Aggregation)하여 상/하체 발달 우위를 판단합니다.
    정규화된 부위별 데이터를 기반으로 불균형 패턴을 감지하는 로직을 수행합니다.
    """
    
    @staticmethod
    def analyze_distribution(seg_data):
        """
        [상/하체 발달 분포 분석]
        부위별 등급 데이터를 분석하여, 상체나 하체 중 특별히 발달한(표준이상) 곳이 있는지 확인합니다.
        
        Logic:
            1. 상체(양팔) 중 '표준이상'인 개수 카운트 (0~2개)
            2. 하체(양다리) 중 '표준이상'인 개수 카운트 (0~2개)
            3. 하체가 2개(양쪽 다 발달)이고 상체는 2개 미만이면 -> '하체' 우세
            4. 상체가 2개(양쪽 다 발달)이고 하체는 2개 미만이면 -> '상체' 우세
            5. 그 외의 경우(둘 다 발달하거나, 둘 다 평범하면) -> '균형'
        """
        try:
            arm_high_count = Stage3BalanceAnalyzer._count_high_arms(seg_data)
            leg_high_count = Stage3BalanceAnalyzer._count_high_legs(seg_data)
            
            if leg_high_count >= 2 and arm_high_count < 2:
                return "하체"
            elif arm_high_count >= 2 and leg_high_count < 2:
                return "상체"
            else:
                return "균형"
        except (TypeError, KeyError, AttributeError):
            return "균형"
    
    @staticmethod
    def _count_high_arms(seg_data):
        try:
            count = 0
            if seg_data.get(Constants.BodyPartKeys.RIGHT_ARM) == Constants.BodyPartLevel.ABOVE:
                count += 1
            if seg_data.get(Constants.BodyPartKeys.LEFT_ARM) == Constants.BodyPartLevel.ABOVE:
                count += 1
            return count
        except (TypeError, AttributeError):
            return 0
    
    @staticmethod
    def _count_high_legs(seg_data):
        try:
            count = 0
            if seg_data.get(Constants.BodyPartKeys.RIGHT_LEG) == Constants.BodyPartLevel.ABOVE:
                count += 1
            if seg_data.get(Constants.BodyPartKeys.LEFT_LEG) == Constants.BodyPartLevel.ABOVE:
                count += 1
            return count
        except (TypeError, AttributeError):
            return 0
    
    @staticmethod
    def classify(muscle_seg, fat_seg=None):
        try:
            muscle_dist = Stage3BalanceAnalyzer.analyze_distribution(muscle_seg)
            if fat_seg is None:
                return Stage3BalanceAnalyzer._classify_by_muscle_only(muscle_dist)
            fat_dist = Stage3BalanceAnalyzer.analyze_distribution(fat_seg)
            return Stage3BalanceAnalyzer._classify_with_fat(muscle_dist, fat_dist)
        except (TypeError, AttributeError):
            return "표준형"
    
    @staticmethod
    def _classify_by_muscle_only(muscle_dist):
        if muscle_dist == "하체": return "하체발달형"
        elif muscle_dist == "상체": return "상체발달형"
        else: return "표준형"
    
    @staticmethod
    def _classify_with_fat(muscle_dist, fat_dist):
        if fat_dist == "하체": return "하체비만형"
        elif fat_dist == "상체": return "상체비만형"
        
        if muscle_dist == "하체": return "하체발달형"
        elif muscle_dist == "상체": return "상체발달형"
        else: return "표준형"
