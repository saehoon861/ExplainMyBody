"""
[부위별 상세 분석 (Segmental Analysis)]

신체 5부위(좌/우 팔, 좌/우 다리, 몸통)의 개별 발달도를 분석하는 모듈입니다.
Input Data를 전체 총량(Total Mass) 대비 비율(Relative Ratio)로 변환하고,
이를 다시 표준화된 등급(Normalized Grade)으로 매핑하는 정규화 로직을 포함합니다.
"""

import math
from . import constants as Constants

class SegmentalAnalyzer:
    """
    [분석기 Base Class]
    부위별 분석 클래스들의 공통 로직을 정의한 부모 클래스입니다.
    데이터 타입 검증(Type Validation), 비율 계산, 임계값 비교 등의 유틸리티 메서드를 제공합니다.
    """
    
    @staticmethod
    def is_numeric_data(seg_data):
        """데이터가 숫자 형식인지 확인"""
        try:
            if not isinstance(seg_data, dict):
                return False
            return all(isinstance(v, (int, float)) for v in seg_data.values())
        except (TypeError, AttributeError):
            return False
    
    @staticmethod
    def classify_part_level(value, reference, margin):
        """
        [개별 부위 발달도 분류 로직]
        특정 부위의 측정값(value)이 기준값(reference) 대비 어느 정도 수준인지 판단합니다.
        
        Args:
            value (float): 해당 부위의 실제 측정값 (예: 왼팔 근육량 3.1kg)
            reference (float): 비교할 기준값 (예: 팔 근육량 평균치 2.8kg)
            margin (float): 허용 오차 범위 비율 (예: 0.1은 ±10%를 의미)
            
        Returns:
            str: '표준이상', '표준', '표준미만' 중 하나
            
        Logic:
            1. 기준값(reference)을 중심으로 ±margin 만큼의 '정상 범위'를 설정합니다.
               - 상한선(Upper) = 기준값 * (1 + margin)
               - 하한선(Lower) = 기준값 * (1 - margin)
            2. 측정값(value)이 상한선보다 크면 -> '표준이상' (ABOVE)
            3. 측정값(value)이 하한선보다 작으면 -> '표준미만' (BELOW)
            4. 그 사이(정상 범위)에 있으면 -> '표준' (NORMAL)
        """
        try:
            value = float(value)
            reference = float(reference)
            margin = float(margin)
            
            if not all(math.isfinite(x) for x in [value, reference, margin]):
                return Constants.BodyPartLevel.NORMAL
            
            if reference == 0:
                return Constants.BodyPartLevel.NORMAL
            
            upper_threshold = reference * (1 + margin)
            lower_threshold = reference * (1 - margin)
            
            if value >= upper_threshold:
                return Constants.BodyPartLevel.ABOVE
            elif value <= lower_threshold:
                return Constants.BodyPartLevel.BELOW
            else:
                return Constants.BodyPartLevel.NORMAL
                
        except (TypeError, ValueError, ZeroDivisionError):
            return Constants.BodyPartLevel.NORMAL
    
    @staticmethod
    def calculate_development_ratio(parts, total):
        """
        [부위별 발달 비율 계산]
        각 부위의 절대 측정값(Absolute Value)을 전체 총량(Total)으로 나누어
        '전체 대비 비율(Ratio)'을 계산합니다.
        
        Args:
            parts (dict): 부위별 측정값 딕셔너리 (Key: 부위명, Value: 측정값)
            total (float): 전체 총량 (예: 총 골격근량 SMM)
            
        Returns:
            dict: {부위명: 비율} 형태의 딕셔너리 (예: {'왼팔': 0.08, ...})
            
        Example:
            왼팔 근육 3kg / 전체 근육 30kg = 0.1 (10%)
        """
        try:
            total = float(total)
            
            if total == 0 or not math.isfinite(total):
                return {k: 0.0 for k in parts.keys()}
            
            ratios = {}
            for key, value in parts.items():
                try:
                    value = float(value)
                    ratio = value / total if math.isfinite(value) else 0.0
                    ratios[key] = ratio
                except (TypeError, ValueError, ZeroDivisionError):
                    ratios[key] = 0.0
            
            return ratios
            
        except (TypeError, ValueError):
            return {k: 0.0 for k in parts.keys()}


class MuscleSegmentalAnalyzer(SegmentalAnalyzer):
    """
    [근육 부위별 분석기]
    부위별 근육량 데이터를 분석하여 신체 부위별 근육 발달 밸런스를 평가합니다.
    상대적 비율 계산 로직을 오버라이딩하거나 확장하여 사용합니다.
    """
    
    @staticmethod
    def classify(parts, total_smm, margin=Constants.ValidationLimits.DEFAULT_MARGIN):
        """부위별 근육 분류"""
        try:
            # 발달도 비율 계산
            dev = MuscleSegmentalAnalyzer.calculate_development_ratio(parts, total_smm)
            
            # 기준값 계산
            arm_ref = MuscleSegmentalAnalyzer._calculate_arm_reference(dev)
            leg_ref = MuscleSegmentalAnalyzer._calculate_leg_reference(dev)
            trunk_ref = MuscleSegmentalAnalyzer._calculate_trunk_reference(arm_ref, leg_ref)
            
            # 부위별 분류 실행
            # 각 부위의 비율(dev)을 해당 부위의 기준값(ref)과 비교하여 등급(Level)을 매깁니다.
            # Constants.BodyPartLevel.ABOVE/NORMAL/BELOW 상수를 반환합니다.
            return {
                Constants.BodyPartKeys.LEFT_ARM: SegmentalAnalyzer.classify_part_level(
                    dev.get(Constants.BodyPartKeys.LEFT_ARM, 0), arm_ref, margin
                ),
                Constants.BodyPartKeys.RIGHT_ARM: SegmentalAnalyzer.classify_part_level(
                    dev.get(Constants.BodyPartKeys.RIGHT_ARM, 0), arm_ref, margin
                ),
                Constants.BodyPartKeys.TRUNK: SegmentalAnalyzer.classify_part_level(
                    dev.get(Constants.BodyPartKeys.TRUNK, 0), trunk_ref, margin
                ),
                Constants.BodyPartKeys.LEFT_LEG: SegmentalAnalyzer.classify_part_level(
                    dev.get(Constants.BodyPartKeys.LEFT_LEG, 0), leg_ref, margin
                ),
                Constants.BodyPartKeys.RIGHT_LEG: SegmentalAnalyzer.classify_part_level(
                    dev.get(Constants.BodyPartKeys.RIGHT_LEG, 0), leg_ref, margin
                ),
            }
            
        except (TypeError, KeyError, AttributeError):
            return MuscleSegmentalAnalyzer._get_default_classification()
    
    @staticmethod
    def _calculate_arm_reference(dev):
        """팔 기준값 계산"""
        try:
            left = dev.get(Constants.BodyPartKeys.LEFT_ARM, 0)
            right = dev.get(Constants.BodyPartKeys.RIGHT_ARM, 0)
            avg = (left + right) / 2.0
            return avg if math.isfinite(avg) else 0.0
        except (TypeError, ZeroDivisionError):
            return 0.0
    
    @staticmethod
    def _calculate_leg_reference(dev):
        """다리 기준값 계산"""
        try:
            left = dev.get(Constants.BodyPartKeys.LEFT_LEG, 0)
            right = dev.get(Constants.BodyPartKeys.RIGHT_LEG, 0)
            avg = (left + right) / 2.0
            return avg if math.isfinite(avg) else 0.0
        except (TypeError, ZeroDivisionError):
            return 0.0
    
    @staticmethod
    def _calculate_trunk_reference(arm_ref, leg_ref):
        """몸통 기준값 계산 (팔과 다리의 중간값)"""
        try:
            avg = (arm_ref + leg_ref) / 2.0
            return avg if math.isfinite(avg) else 0.0
        except (TypeError, ZeroDivisionError):
            return 0.0
    
    @staticmethod
    def _get_default_classification():
        """기본 분류값 반환"""
        return {
            Constants.BodyPartKeys.LEFT_ARM: Constants.BodyPartLevel.NORMAL,
            Constants.BodyPartKeys.RIGHT_ARM: Constants.BodyPartLevel.NORMAL,
            Constants.BodyPartKeys.TRUNK: Constants.BodyPartLevel.NORMAL,
            Constants.BodyPartKeys.LEFT_LEG: Constants.BodyPartLevel.NORMAL,
            Constants.BodyPartKeys.RIGHT_LEG: Constants.BodyPartLevel.NORMAL,
        }


class FatSegmentalAnalyzer(SegmentalAnalyzer):
    """
    [체지방 부위별 분석기]
    부위별 체지방 데이터를 분석하여 지방 분포의 집중도를 평가합니다.
    (예: 복부 비만 여부, 하체 비만 여부 판단 등)
    """
    
    @staticmethod
    def classify(fat_parts, total_fat, margin=Constants.ValidationLimits.DEFAULT_MARGIN):
        """부위별 체지방 분류"""
        try:
            # 발달도 비율 계산
            dev = FatSegmentalAnalyzer.calculate_development_ratio(fat_parts, total_fat)
            
            # 기준값 계산
            arm_ref = FatSegmentalAnalyzer._calculate_arm_reference(dev)
            leg_ref = FatSegmentalAnalyzer._calculate_leg_reference(dev)
            trunk_ref = FatSegmentalAnalyzer._calculate_trunk_reference(dev)
            
            # 부위별 분류
            return {
                Constants.BodyPartKeys.LEFT_ARM: SegmentalAnalyzer.classify_part_level(
                    dev.get(Constants.BodyPartKeys.LEFT_ARM, 0), arm_ref, margin
                ),
                Constants.BodyPartKeys.RIGHT_ARM: SegmentalAnalyzer.classify_part_level(
                    dev.get(Constants.BodyPartKeys.RIGHT_ARM, 0), arm_ref, margin
                ),
                Constants.BodyPartKeys.TRUNK: SegmentalAnalyzer.classify_part_level(
                    dev.get(Constants.BodyPartKeys.TRUNK, 0), trunk_ref, margin
                ),
                Constants.BodyPartKeys.LEFT_LEG: SegmentalAnalyzer.classify_part_level(
                    dev.get(Constants.BodyPartKeys.LEFT_LEG, 0), leg_ref, margin
                ),
                Constants.BodyPartKeys.RIGHT_LEG: SegmentalAnalyzer.classify_part_level(
                    dev.get(Constants.BodyPartKeys.RIGHT_LEG, 0), leg_ref, margin
                ),
            }
            
        except (TypeError, KeyError, AttributeError):
            return FatSegmentalAnalyzer._get_default_classification()
    
    @staticmethod
    def _calculate_arm_reference(dev):
        """팔 기준값 계산"""
        try:
            left = dev.get(Constants.BodyPartKeys.LEFT_ARM, 0)
            right = dev.get(Constants.BodyPartKeys.RIGHT_ARM, 0)
            avg = (left + right) / 2.0
            return avg if math.isfinite(avg) else 0.0
        except (TypeError, ZeroDivisionError):
            return 0.0
    
    @staticmethod
    def _calculate_leg_reference(dev):
        """다리 기준값 계산"""
        try:
            left = dev.get(Constants.BodyPartKeys.LEFT_LEG, 0)
            right = dev.get(Constants.BodyPartKeys.RIGHT_LEG, 0)
            avg = (left + right) / 2.0
            return avg if math.isfinite(avg) else 0.0
        except (TypeError, ZeroDivisionError):
            return 0.0
    
    @staticmethod
    def _calculate_trunk_reference(dev):
        """몸통 기준값 계산 (체지방은 자기 자신 기준)"""
        try:
            trunk = dev.get(Constants.BodyPartKeys.TRUNK, 0)
            return trunk if math.isfinite(trunk) else 0.0
        except TypeError:
            return 0.0
    
    @staticmethod
    def _get_default_classification():
        """기본 분류값 반환"""
        return {
            Constants.BodyPartKeys.LEFT_ARM: Constants.BodyPartLevel.NORMAL,
            Constants.BodyPartKeys.RIGHT_ARM: Constants.BodyPartLevel.NORMAL,
            Constants.BodyPartKeys.TRUNK: Constants.BodyPartLevel.NORMAL,
            Constants.BodyPartKeys.LEFT_LEG: Constants.BodyPartLevel.NORMAL,
            Constants.BodyPartKeys.RIGHT_LEG: Constants.BodyPartLevel.NORMAL,
        }


class DataNormalizer:
    """
    [데이터 정규화 (Normalization)]
    다양한 수치형(Numeric) 분석 결과를 일관된 범주형(Categorical) 데이터로 변환하는 클래스입니다.
    API 응답이나 UI 표시를 위해 내부 연산 결과를 '표준화된 포맷'으로 가공하는 역할을 합니다.
    """
    
    @staticmethod
    def normalize_muscle_segment(muscle_input, total_smm, margin=Constants.ValidationLimits.DEFAULT_MARGIN):
        """근육 데이터 정규화 (숫자 → 표준/표준이상/표준미만)"""
        try:
            # 이미 텍스트 형태인 경우 그대로 반환
            if not SegmentalAnalyzer.is_numeric_data(muscle_input):
                return muscle_input
            
            # 숫자 형태인 경우 분류 수행
            return MuscleSegmentalAnalyzer.classify(muscle_input, total_smm, margin)
            
        except (TypeError, AttributeError):
            return muscle_input
    
    @staticmethod
    def normalize_fat_segment(fat_input, total_fat, margin=Constants.ValidationLimits.DEFAULT_MARGIN):
        """체지방 데이터 정규화 (숫자 → 표준/표준이상/표준미만)"""
        try:
            # 이미 텍스트 형태인 경우 그대로 반환
            if not SegmentalAnalyzer.is_numeric_data(fat_input):
                return fat_input
            
            # 숫자 형태인 경우 분류 수행
            return FatSegmentalAnalyzer.classify(fat_input, total_fat, margin)
            
        except (TypeError, AttributeError):
            return fat_input
