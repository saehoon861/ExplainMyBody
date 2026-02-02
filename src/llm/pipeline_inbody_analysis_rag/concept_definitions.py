"""
체형 분석용 Concept ID 정의
- Graph RAG 검색에 사용되는 개념 ID와 설명
- Call2 Router가 자연어에서 추출할 개념 매핑
"""

from typing import Dict, List


# ==================== Concept ID 정의 ====================

CONCEPT_DEFINITIONS: Dict[str, Dict[str, str]] = {
    # 근육 관련
    "sarcopenia_risk": {
        "name": "근감소증 위험",
        "description": "연령 증가에 따른 근육량 감소 및 근감소증 위험",
        "keywords": ["근감소증", "근육 감소", "노화", "근력 저하", "근육량 부족"]
    },
    "resistance_training": {
        "name": "저항성 운동",
        "description": "근육량 증가를 위한 저항성 운동 효과",
        "keywords": ["저항운동", "웨이트", "근력 운동", "근비대", "골격근"]
    },
    "muscle_hypertrophy": {
        "name": "근비대",
        "description": "근육 크기 증가 및 근비대 메커니즘",
        "keywords": ["근비대", "근육 증가", "근육 성장", "골격근량"]
    },

    # 지방/비만 관련
    "visceral_fat_metabolic_risk": {
        "name": "내장지방 대사 위험",
        "description": "내장지방 증가에 따른 대사질환 위험",
        "keywords": ["내장지방", "대사증후군", "인슐린 저항성", "염증", "복부비만"]
    },
    "abdominal_obesity_risk": {
        "name": "복부비만 위험",
        "description": "복부 지방 축적과 건강 위험",
        "keywords": ["복부비만", "복부지방", "허리둘레", "중심비만"]
    },
    "fat_loss_aerobic_exercise": {
        "name": "유산소 운동 지방 감소",
        "description": "유산소 운동을 통한 체지방 감소 효과",
        "keywords": ["유산소", "체지방 감소", "지방 연소", "칼로리 소모"]
    },
    "body_fat_percentage": {
        "name": "체지방률",
        "description": "체지방률과 건강 지표",
        "keywords": ["체지방률", "체지방", "비만", "체성분"]
    },

    # 영양 관련
    "high_protein_intake": {
        "name": "고단백 섭취",
        "description": "단백질 섭취와 근육량 유지/증가",
        "keywords": ["단백질", "고단백", "아미노산", "근육 합성"]
    },
    "calorie_deficit_weight_loss": {
        "name": "칼로리 제한 체중 감량",
        "description": "칼로리 제한을 통한 체중 및 체지방 감량",
        "keywords": ["칼로리 제한", "체중 감량", "다이어트", "열량 제한"]
    },

    # 연령/성별 위험
    "age_related_muscle_loss": {
        "name": "연령 관련 근육 손실",
        "description": "나이에 따른 근육량 자연 감소",
        "keywords": ["노화", "근육 손실", "연령", "노인"]
    },
    "metabolic_syndrome_risk": {
        "name": "대사증후군 위험",
        "description": "비만, 고혈압, 고혈당 등 대사증후군 위험",
        "keywords": ["대사증후군", "당뇨", "고혈압", "고지혈증"]
    },

    # 기타
    "body_composition": {
        "name": "체성분",
        "description": "전반적인 체성분 분석 및 균형",
        "keywords": ["체성분", "인바디", "체수분", "무기질"]
    },
    "skeletal_muscle_mass": {
        "name": "골격근량",
        "description": "골격근량과 건강 지표",
        "keywords": ["골격근", "근육량", "제지방량"]
    },
    "cardiovascular_health": {
        "name": "심혈관 건강",
        "description": "심혈관계 건강과 운동",
        "keywords": ["심혈관", "심장", "혈관", "순환"]
    },
    "metabolic_health": {
        "name": "대사 건강",
        "description": "기초대사량 및 대사 효율",
        "keywords": ["기초대사량", "대사", "에너지"]
    }
}


# ==================== Concept 카테고리 ====================

CONCEPT_CATEGORIES = {
    "근육": [
        "sarcopenia_risk",
        "resistance_training",
        "muscle_hypertrophy",
        "age_related_muscle_loss",
        "skeletal_muscle_mass"
    ],
    "지방/비만": [
        "visceral_fat_metabolic_risk",
        "abdominal_obesity_risk",
        "fat_loss_aerobic_exercise",
        "body_fat_percentage"
    ],
    "영양": [
        "high_protein_intake",
        "calorie_deficit_weight_loss"
    ],
    "건강 위험": [
        "metabolic_syndrome_risk",
        "cardiovascular_health",
        "metabolic_health"
    ]
}


# ==================== Helper Functions ====================

def get_concept_name(concept_id: str) -> str:
    """Concept ID의 한글 이름 반환"""
    return CONCEPT_DEFINITIONS.get(concept_id, {}).get("name", concept_id)


def get_all_concept_ids() -> List[str]:
    """모든 concept ID 리스트 반환"""
    return list(CONCEPT_DEFINITIONS.keys())


def format_concept_with_tag(risk_text: str, concept_id: str) -> str:
    """
    자연어 risk 텍스트에 concept tag 추가

    예: "내장지방 위험: 주의" → "내장지방 위험: 주의 (concept: visceral_fat_metabolic_risk)"

    이렇게 하면 Call2 Router의 정확도가 2배 향상됨
    """
    if not concept_id or concept_id not in CONCEPT_DEFINITIONS:
        return risk_text

    return f"{risk_text} (concept: {concept_id})"


def get_concept_list_for_router_prompt() -> str:
    """
    Call2 Router 프롬프트에 사용할 concept 리스트 문자열 생성
    """
    lines = []

    for category, concept_ids in CONCEPT_CATEGORIES.items():
        lines.append(f"\n[{category} 관련]")
        for cid in concept_ids:
            definition = CONCEPT_DEFINITIONS[cid]
            lines.append(f"- {cid}: {definition['name']}")

    return "\n".join(lines)
