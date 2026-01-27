"""
[데이터 모델 (Data Model)]

본 모듈은 체성분 분석 도메인에서 사용되는 데이터 구조(Data Structure)를 정의합니다.
DTO(Data Transfer Object) 역할을 수행하며, 외부 입력(Dictionary/JSON)과 내부 비즈니스 로직 간의
데이터 인터페이스를 통일하여 타입 안정성을 보장합니다.
"""

import math

class BodyCompositionData:
    """
    [체성분 데이터 객체]
    사용자 기본 정보(Basic Info)와 측정 데이터(Composition Data)를 캡슐화한 모델 클래스입니다.
    - 주요 역할: 데이터 유효성 검증, 타입 변환, 데이터 접근 추상화
    - from_dict() 메서드를 통해 외부 Dictionary 데이터를 안전하게 객체로 매핑(Mapping)합니다.
    """
    
    def __init__(self):
        self.sex = None
        self.age = None
        self.height_cm = None
        self.weight_kg = None
        self.bmi = None
        self.fat_rate = None
        self.smm = None
        self.muscle_seg = None
        self.fat_seg = None
    
    @classmethod
    def from_dict(cls, data_dict):
        """딕셔너리를 BodyCompositionData 객체로 변환
        
        Args:
            data_dict: 체성분 데이터가 담긴 딕셔너리
            
        Returns:
            BodyCompositionData: 변환된 객체
        """
        obj = cls()
        
        # 기본 정보 설정
        if all(k in data_dict for k in ["sex", "age", "height_cm", "weight_kg"]):
            obj.set_basic_info(
                sex=data_dict["sex"],
                age=data_dict["age"],
                height_cm=data_dict["height_cm"],
                weight_kg=data_dict["weight_kg"]
            )
        
        # 체성분 정보 설정
        if all(k in data_dict for k in ["bmi", "fat_rate", "smm"]):
            obj.set_composition(
                bmi=data_dict["bmi"],
                fat_rate=data_dict["fat_rate"],
                smm=data_dict["smm"]
            )
        
        # 부위별 데이터 설정
        if "muscle_seg" in data_dict:
            obj.set_segmental_data(
                muscle_seg=data_dict.get("muscle_seg"),
                fat_seg=data_dict.get("fat_seg")
            )
        
        return obj
    
    def set_basic_info(self, sex, age, height_cm, weight_kg):
        """기본 정보 설정"""
        self.sex = sex
        self.age = age
        self.height_cm = height_cm
        self.weight_kg = weight_kg
        return self
    
    def set_composition(self, bmi, fat_rate, smm):
        """체성분 정보 설정"""
        self.bmi = bmi
        self.fat_rate = fat_rate
        self.smm = smm
        return self
    
    def set_segmental_data(self, muscle_seg, fat_seg=None):
        """부위별 데이터 설정"""
        self.muscle_seg = muscle_seg
        self.fat_seg = fat_seg
        return self
    
    def get_total_fat(self):
        """총 체지방량 계산"""
        try:
            total_fat = self.weight_kg * self.fat_rate / 100.0
            if not math.isfinite(total_fat) or total_fat < 0:
                return 0.0
            return total_fat
        except (TypeError, ZeroDivisionError):
            return 0.0
