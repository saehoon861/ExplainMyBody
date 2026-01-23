"""
[도메인 상수 및 임계값 정의]

본 모듈은 체형 분석 비즈니스 로직에서 기준이 되는 임계값(Threshold)과 상수(Constant)들을 관리합니다.
비즈니스 규칙 변경 시 이곳의 값만 수정하면 시스템 전반에 반영되도록 설계되었습니다.
"""

class BMIThreshold:
    """
    [BMI 분류 임계값]
    BMI(체질량지수) 구간별 분류 기준입니다. 
    WHO 또는 대한비만학회 기준을 따르며, 각 구간의 상한/하한 경계값을 정의합니다. #fixme
    
    Usage:
        - value < UNDERWEIGHT: 저체중
        - UNDERWEIGHT <= value < NORMAL: 정상
        - ... (구간별 상한선으로 사용됨)
    """
    UNDERWEIGHT = 18.5
    NORMAL = 23.0
    OVERWEIGHT = 24.9
    OBESE_1 = 29.9
    OBESE_2 = 34.9


class BodyFatThreshold:
    """
    [체지방률 분류 임계값]
    체지방률(Fat Percentage)에 따른 비만도 분류 기준입니다.
    성별/연령별 기준을 일반화하여 시스템에서 사용하는 표준 임계값을 정의합니다.
    
    Usage:
        - value < LOW: 표준미만
        - LOW <= value < NORMAL: 표준
        - NORMAL <= value < OVERWEIGHT: 과체중
        - value >= OVERWEIGHT: 비만
    """
    LOW = 10.0
    NORMAL = 20.0
    OVERWEIGHT = 24.0


class MuscleRatioThreshold:
    """
    [골격근량 비율 임계값]
    체중 대비 골격근량(SMM) 비율을 기준으로 근육 발달 수준을 5단계로 분류하기 위한 임계값입니다.
    단순 절대량이 아닌 체중 대비 비율(Relative Ratio)을 사용하여 체격에 따른 편차를 보정합니다.
    
    Calculation:
        Ratio = 골격근량(SMM) / 체중(Weight)
    
    Usage:
        - Ratio >= VERY_HIGH: 근육 매우 많음
        - Ratio >= HIGH: 근육 많음
        - ... (내림차순 비교)
    """
    VERY_HIGH = 0.55
    HIGH = 0.50
    SUFFICIENT = 0.45
    NORMAL = 0.40


class ValidationLimits:
    """
    [데이터 유효성 검증 범위]
    입력 데이터의 무결성을 보장하기 위한 유효 범위(Valid Range) 정의입니다.
    비정상적인 이상치(Outlier)나 오입력 데이터를 필터링하는 데 사용됩니다.
    """
    MIN_WEIGHT = 1.0
    MAX_WEIGHT = 500.0
    MIN_BMI = 10.0
    MAX_BMI = 100.0
    MIN_FAT_RATE = 0.0
    MAX_FAT_RATE = 100.0
    MIN_MUSCLE = 0.0
    DEFAULT_MARGIN = 0.10


class BodyPartLevel:
    """
    [부위별 발달 등급 열거형]
    부위별 분석 결과(Segmental Analysis)의 표준화된 등급을 정의하는 상수 집합입니다.
    
    Usage:
        - ABOVE: 측정값이 (기준값 + 오차범위)보다 클 때 ('표준이상')
        - BELOW: 측정값이 (기준값 - 오차범위)보다 작을 때 ('표준미만')
        - NORMAL: 그 사이 구간일 때 ('표준')
    """
    ABOVE = "표준이상"
    NORMAL = "표준"
    BELOW = "표준미만"


class BodyPartKeys:
    """
    [부위 식별 키]
    데이터 딕셔너리 접근 시 Key Error를 방지하고 일관된 Key 네이밍을 보장하기 위한 상수입니다.
    모든 부위별 데이터 접근은 이 Key 상수를 통해 이루어져야 합니다.
    
    Mapping:
        - LEFT_ARM, RIGHT_ARM -> 상체 그룹
        - LEFT_LEG, RIGHT_LEG -> 하체 그룹
        - TRUNK -> 몸통 (코어)
    """
    LEFT_ARM = "왼팔"
    RIGHT_ARM = "오른팔"
    TRUNK = "몸통"
    LEFT_LEG = "왼다리"
    RIGHT_LEG = "오른다리"
