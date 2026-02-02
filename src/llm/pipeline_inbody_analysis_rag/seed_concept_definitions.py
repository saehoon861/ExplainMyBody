"""
Seed Concept Dictionary
- 기존 Graph DB의 21개 concept 관계를 Seed로 사용
- concept_type: Seed (초기 입력) / Outcome (위험) / Intervention (처방)
- Rule-based Extractor가 InBody 측정값에서 Seed를 추출
- Graph Expansion Retriever가 Seed → Risk → Intervention을 자동 확장
"""

from typing import Dict, List, Tuple


# ==================== Seed Concept 정의 ====================

SEED_CONCEPTS: Dict[str, Dict[str, any]] = {
    # === 근육 관련 Seed ===
    "skeletal_muscle_low": {
        "name_ko": "골격근량 부족",
        "concept_type": "Seed",
        "description": "골격근량이 표준 범위 이하",
        "extraction_rule": {
            "field": "골격근량",
            "condition": lambda measurements: (
                measurements.근육조절 and measurements.근육조절 > 0
            ) or (
                "부족" in str(measurements.근육_부위별등급.values()) or
                "표준미만" in str(measurements.근육_부위별등급.values())
            )
        }
    },
    "skeletal_muscle_normal": {
        "name_ko": "골격근량 정상",
        "concept_type": "Seed",
        "description": "골격근량이 표준 범위 내",
        "extraction_rule": {
            "field": "골격근량",
            "condition": lambda measurements: (
                not (measurements.근육조절 and measurements.근육조절 > 0) and
                "표준" in str(measurements.근육_부위별등급.values())
            )
        }
    },
    "muscle_imbalance": {
        "name_ko": "부위별 근육 불균형",
        "concept_type": "Seed",
        "description": "부위별 근육 발달 불균형",
        "extraction_rule": {
            "field": "근육_부위별등급",
            "condition": lambda measurements: len(set(measurements.근육_부위별등급.values())) > 2
        }
    },

    # === 지방 관련 Seed ===
    "body_fat_high": {
        "name_ko": "체지방률 과다",
        "concept_type": "Seed",
        "description": "체지방률이 정상 범위 초과",
        "extraction_rule": {
            "field": "체지방률",
            "condition": lambda measurements: (
                (measurements.성별 == "남성" and measurements.체지방률 > 25) or
                (measurements.성별 == "여성" and measurements.체지방률 > 30)
            )
        }
    },
    "body_fat_normal": {
        "name_ko": "체지방률 정상",
        "concept_type": "Seed",
        "description": "체지방률이 정상 범위 내",
        "extraction_rule": {
            "field": "체지방률",
            "condition": lambda measurements: (
                (measurements.성별 == "남성" and 10 <= measurements.체지방률 <= 25) or
                (measurements.성별 == "여성" and 20 <= measurements.체지방률 <= 30)
            )
        }
    },
    "visceral_fat_high": {
        "name_ko": "내장지방 과다",
        "concept_type": "Seed",
        "description": "내장지방 레벨이 위험 수준",
        "extraction_rule": {
            "field": "내장지방레벨",
            "condition": lambda measurements: (
                measurements.내장지방레벨 and measurements.내장지방레벨 > 10
            )
        }
    },
    "visceral_fat_normal": {
        "name_ko": "내장지방 정상",
        "concept_type": "Seed",
        "description": "내장지방 레벨이 정상 범위",
        "extraction_rule": {
            "field": "내장지방레벨",
            "condition": lambda measurements: (
                measurements.내장지방레벨 and measurements.내장지방레벨 <= 10
            )
        }
    },
    "abdominal_obesity": {
        "name_ko": "복부비만",
        "concept_type": "Seed",
        "description": "복부지방률이 높음",
        "extraction_rule": {
            "field": "복부지방률",
            "condition": lambda measurements: (
                measurements.복부지방률 and measurements.복부지방률 > 0.90
            )
        }
    },

    # === BMI 관련 Seed ===
    "bmi_overweight": {
        "name_ko": "과체중",
        "concept_type": "Seed",
        "description": "BMI 25 이상",
        "extraction_rule": {
            "field": "BMI",
            "condition": lambda measurements: measurements.BMI >= 25
        }
    },
    "bmi_normal": {
        "name_ko": "정상 체중",
        "concept_type": "Seed",
        "description": "BMI 18.5-25",
        "extraction_rule": {
            "field": "BMI",
            "condition": lambda measurements: 18.5 <= measurements.BMI < 25
        }
    },
    "bmi_underweight": {
        "name_ko": "저체중",
        "concept_type": "Seed",
        "description": "BMI 18.5 미만",
        "extraction_rule": {
            "field": "BMI",
            "condition": lambda measurements: measurements.BMI < 18.5
        }
    },

    # === 연령 관련 Seed ===
    "age_sarcopenia_risk": {
        "name_ko": "근감소증 연령 위험군",
        "concept_type": "Seed",
        "description": "근감소증 위험 연령대 (40세 이상)",
        "extraction_rule": {
            "field": "나이",
            "condition": lambda measurements: measurements.나이 >= 40
        }
    },
    "age_metabolic_risk": {
        "name_ko": "대사질환 연령 위험군",
        "concept_type": "Seed",
        "description": "대사질환 위험 연령대 (35세 이상)",
        "extraction_rule": {
            "field": "나이",
            "condition": lambda measurements: measurements.나이 >= 35
        }
    },

    # === 체형 분류 기반 Seed ===
    "body_type_sarcopenic_obesity": {
        "name_ko": "근감소성 비만",
        "concept_type": "Seed",
        "description": "근육 부족 + 체지방 과다",
        "extraction_rule": {
            "field": "복합",
            "condition": lambda measurements: (
                (measurements.근육조절 and measurements.근육조절 > 0) and
                (measurements.지방조절 and measurements.지방조절 < 0)
            )
        }
    },
    "body_type_skinny_fat": {
        "name_ko": "마른 비만",
        "concept_type": "Seed",
        "description": "정상 체중이지만 근육 부족",
        "extraction_rule": {
            "field": "복합",
            "condition": lambda measurements: (
                18.5 <= measurements.BMI < 25 and
                (measurements.근육조절 and measurements.근육조절 > 0)
            )
        }
    }
}


# ==================== Outcome Concepts (Graph에서 자동 확장됨) ====================

OUTCOME_CONCEPTS: Dict[str, Dict[str, any]] = {
    # Seed와 연결된 논문에서 자동으로 찾아짐
    # Graph Expansion Retriever가 SQL로 추출
    "metabolic_syndrome_risk": {
        "name_ko": "대사증후군 위험",
        "concept_type": "Outcome",
        "description": "비만, 고혈압, 고혈당 등 대사증후군 위험"
    },
    "cardiovascular_disease_risk": {
        "name_ko": "심혈관 질환 위험",
        "concept_type": "Outcome",
        "description": "심장 및 혈관 질환 위험 증가"
    },
    "type2_diabetes_risk": {
        "name_ko": "제2형 당뇨병 위험",
        "concept_type": "Outcome",
        "description": "인슐린 저항성 및 당뇨병 위험"
    },
    "sarcopenia_risk": {
        "name_ko": "근감소증 위험",
        "concept_type": "Outcome",
        "description": "근육량 감소 및 근력 저하"
    },
    "osteoporosis_risk": {
        "name_ko": "골다공증 위험",
        "concept_type": "Outcome",
        "description": "골밀도 감소 및 골절 위험"
    },
    "functional_decline_risk": {
        "name_ko": "기능 저하 위험",
        "concept_type": "Outcome",
        "description": "일상생활 수행 능력 저하"
    }
}


# ==================== Intervention Concepts (Graph에서 자동 확장됨) ====================

INTERVENTION_CONCEPTS: Dict[str, Dict[str, any]] = {
    # Seed와 연결된 논문에서 자동으로 찾아짐
    "resistance_training": {
        "name_ko": "저항성 운동",
        "concept_type": "Intervention",
        "description": "근력 운동 및 웨이트 트레이닝"
    },
    "aerobic_exercise": {
        "name_ko": "유산소 운동",
        "concept_type": "Intervention",
        "description": "유산소 운동 및 심폐 지구력 훈련"
    },
    "high_protein_diet": {
        "name_ko": "고단백 식이",
        "concept_type": "Intervention",
        "description": "단백질 섭취 증가"
    },
    "caloric_restriction": {
        "name_ko": "칼로리 제한",
        "concept_type": "Intervention",
        "description": "열량 섭취 감소"
    },
    "combined_exercise": {
        "name_ko": "복합 운동",
        "concept_type": "Intervention",
        "description": "저항성 + 유산소 운동 결합"
    },
    "nutritional_supplementation": {
        "name_ko": "영양 보충",
        "concept_type": "Intervention",
        "description": "비타민, 미네랄 등 영양소 보충"
    }
}


# ==================== Helper Functions ====================

def get_seed_name_ko(seed_id: str) -> str:
    """Seed ID의 한글 이름 반환"""
    return SEED_CONCEPTS.get(seed_id, {}).get("name_ko", seed_id)


def get_all_seed_ids() -> List[str]:
    """모든 Seed ID 리스트 반환"""
    return list(SEED_CONCEPTS.keys())


def format_seed_tag(text: str, seed_id: str) -> str:
    """
    자연어 텍스트에 seed tag 추가

    예: "근육 상태: 부족" → "근육 상태: 부족 (seed: skeletal_muscle_low)"

    이렇게 하면 Rule-based Extractor가 직접 파싱 가능
    """
    if not seed_id or seed_id not in SEED_CONCEPTS:
        return text

    return f"{text} (seed: {seed_id})"


def get_seed_categories() -> Dict[str, List[str]]:
    """Seed를 카테고리별로 그룹화"""
    categories = {
        "근육": [],
        "지방": [],
        "체중": [],
        "연령": [],
        "체형": []
    }

    for seed_id, info in SEED_CONCEPTS.items():
        if "muscle" in seed_id or "skeletal" in seed_id:
            categories["근육"].append(seed_id)
        elif "fat" in seed_id or "visceral" in seed_id or "obesity" in seed_id:
            categories["지방"].append(seed_id)
        elif "bmi" in seed_id:
            categories["체중"].append(seed_id)
        elif "age" in seed_id:
            categories["연령"].append(seed_id)
        elif "body_type" in seed_id:
            categories["체형"].append(seed_id)

    return categories


# ==================== 기존 21개 관계와 매핑 ====================

# 기존 Graph DB의 concept_id → Seed mapping
# (실제 paper_concept_relations 테이블의 concept_id에 맞춰 조정 필요)

LEGACY_CONCEPT_TO_SEED_MAPPING: Dict[str, str] = {
    # 기존 concept_id → 새로운 seed_id
    "muscle_hypertrophy": "skeletal_muscle_low",  # 근비대 → 근육 부족 seed
    "resistance_training": "skeletal_muscle_low",
    "sarcopenia_risk": "age_sarcopenia_risk",
    "visceral_fat": "visceral_fat_high",
    "fat_loss": "body_fat_high",
    "body_fat_percentage": "body_fat_high",
    "abdominal_obesity_risk": "abdominal_obesity",
    "overweight": "bmi_overweight",
    "underweight": "bmi_underweight",
    "metabolic_syndrome_risk": "age_metabolic_risk",
    # ... 나머지 21개 매핑
}


def map_legacy_concept_to_seed(legacy_concept_id: str) -> str:
    """기존 concept_id를 새로운 seed_id로 변환"""
    return LEGACY_CONCEPT_TO_SEED_MAPPING.get(legacy_concept_id, legacy_concept_id)
