"""
[기초 지표 평가 (Metric Evaluation)]

단일 측정 항목(Metric)에 대한 기본적인 등급 분류 로직을 담당하는 모듈입니다.
각 클래스는 Stateless하게 설계되어 있으며, 입력된 수치 데이터를
도메인 상수(constants.py)에 정의된 기준과 비교하여 범주형 데이터(Categorical Data)로 변환합니다.
"""

import math
from . import constants as Constants

class BMIClassifier:
    """
    [BMI 평가 유틸리티]
    신체질량지수(BMI) 수치를 입력받아 비만도 등급(저체중~고도비만)을 반환합니다.
    입력값에 대한 타입 검사 및 예외 처리를 포함하여 로직의 안정성을 보장합니다.
    """
    
    @staticmethod
    def classify(bmi):
        """BMI 값을 카테고리로 분류"""
        try:
            bmi = float(bmi)
            
            if not math.isfinite(bmi):
                return round(bmi, 1), "알 수 없음"
            
            if bmi < Constants.BMIThreshold.UNDERWEIGHT:
                category = "저체중"
            elif bmi < Constants.BMIThreshold.NORMAL:
                category = "정상"
            elif bmi < Constants.BMIThreshold.OVERWEIGHT:
                category = "과체중"
            elif bmi < Constants.BMIThreshold.OBESE_1:
                category = "비만1단계"
            elif bmi < Constants.BMIThreshold.OBESE_2:
                category = "비만2단계"
            else:
                category = "고도비만"
            
            return round(bmi, 1), category
            
        except (TypeError, ValueError):
            return 0.0, "알 수 없음"


class BodyFatClassifier:
    """
    [체지방률 평가 유틸리티]
    체지방률(Fat Rate) 수치를 입력받아 표준/경도비만/비만 등의 등급으로 분류합니다.
    """
    
    @staticmethod
    def classify(fat_rate):
        """체지방률을 카테고리로 분류"""
        try:
            fat_rate = float(fat_rate)
            
            if not math.isfinite(fat_rate):
                return "알 수 없음"
            
            if fat_rate < Constants.BodyFatThreshold.LOW:
                return "표준미만"
            elif fat_rate < Constants.BodyFatThreshold.NORMAL:
                return "표준"
            elif fat_rate < Constants.BodyFatThreshold.OVERWEIGHT:
                return "과체중"
            else:
                return "비만"
                
        except (TypeError, ValueError):
            return "알 수 없음"


class MuscleClassifier:
    """
    [골격근량 평가 유틸리티]
    SMM(골격근량)과 체중을 인자로 받아 '체중 대비 근육 비율'을 계산하고,
    이를 기반으로 근육 발달 수준을 평가합니다. (예: 근육 부족, 적정, 근육 많음)
    """
    
    @staticmethod
    def classify(smm, weight):
        """근육량/체중 비율로 근육 레벨 분류"""
        try:
            smm = float(smm)
            weight = float(weight)
            
            if weight == 0 or not math.isfinite(smm) or not math.isfinite(weight):
                return 0.0, "알 수 없음"
            
            ratio = smm / weight
            
            if not math.isfinite(ratio):
                return 0.0, "알 수 없음"
            
            if ratio >= Constants.MuscleRatioThreshold.VERY_HIGH:
                level = "근육 매우 많음"
            elif ratio >= Constants.MuscleRatioThreshold.HIGH:
                level = "근육 많음"
            elif ratio >= Constants.MuscleRatioThreshold.SUFFICIENT:
                level = "근육 충분"
            elif ratio >= Constants.MuscleRatioThreshold.NORMAL:
                level = "근육 보통"
            else:
                level = "근육 적음"
            
            return round(ratio, 3), level
            
        except (TypeError, ValueError, ZeroDivisionError):
            return 0.0, "알 수 없음"
