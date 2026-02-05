"""
테스트용 샘플 데이터
실제 InBody 데이터와 동일한 구조
"""

from datetime import datetime

# 샘플 InBody 측정 데이터 (마른비만형 + 상체비만형)
SAMPLE_MEASUREMENTS = {
    "기본정보": {
        "성별": "남성",
        "연령": 28,
        "신장": 175.0
    },
    "체중관리": {
        "체중": 58.5,
        "골격근량": 26.8,
        "적정체중": 70.0,
        "체중조절": 11.5,
        "지방조절": -3.5,
        "근육조절": 15.0
    },
    "비만분석": {
        "BMI": 19.1,
        "체지방률": 25.8,
        "복부지방률": 0.91,
        "내장지방레벨": 7,
        "비만도": 83
    },
    "체성분": {
        "체수분": 32.8,
        "단백질": 9.2,
        "무기질": 3.4,
        "체지방": 13.1
    },
    "연구항목": {
        "기초대사량": 1420,
        "권장섭취열량": 2350
    },
    "부위별근육분석": {
        "오른팔": "낮음",
        "왼팔": "낮음",
        "몸통": "표준미만",
        "오른다리": "표준미만",
        "왼다리": "표준미만"
    },
    "부위별체지방분석": {
        "오른팔": "높음",
        "왼팔": "높음",
        "몸통": "과다",
        "오른다리": "표준",
        "왼다리": "표준"
    },
    "body_type1": "마른비만형",
    "body_type2": "상체비만형"
}

# 샘플 사용자 정보
SAMPLE_USER = {
    "user_id": 999,
    "record_id": 888,
    "measured_at": datetime.now(),
    "body_type1": "비만형",
    "body_type2": "하체비만형",
    "goal_type": "" ,                 # 다중선택 (comma-separated): ['감량', '유지', '증량', '재활']
    "health_specifics": "" ,         # 다중선택 (comma-separated): ['고혈압', '당뇨', '심장 질환', '호흡기 질환', '관절염', '허리 디스크', '근골격계 질환', '기타']
    "preferences": "" ,              # 활동레벨 + 다중선택 preferredExercisesList (comma-separated)
}

# 샘플 사용자 프로필 (다양한 케이스)
SAMPLE_PROFILES = {
    "홈트_마른비만": {
        "body_type1": "마른비만형",
        "body_type2": "상체비만형",
        "goal_type": "감량",
        "health_specifics": "관절염",
        "preferences": "활동레벨: 매우 낮음, 요가, 필라테스, 맨몸운동",
    },
    "헬스장_표준": {
        "body_type1": "표준형",
        "body_type2": "표준형",
        "goal_type": "증량",
        "health_specifics": "",
        "preferences": "활동레벨: 매우 높음, 웨이트, 고강도운동, 무산소",
    },
    "스포츠_축구": {
        "body_type1": "근육형",
        "body_type2": "상체발달형",
        "goal_type": "유지",
        "health_specifics": "",
        "preferences": "활동레벨: 매우 높음, 러닝, 무산소, 실외운동",
    },
    "아웃도어_비만": {
        "body_type1": "비만형",
        "body_type2": "하체비만형",
        "goal_type": "감량",
        "health_specifics": "허리 디스크, 고혈압",
        "preferences": "활동레벨: 매우 낮음, 걷기, 실외운동",
    },
    "재활_허리": {
        "body_type1": "마른근육형",
        "body_type2": "표준형",
        "goal_type": "재활, 감량",          # 다중선택 예시
        "health_specifics": "근골격계 질환",
        "preferences": "활동레벨: 매우 낮음, 맨몸운동, 실내운동",
    },
}

# 샘플 목표 정보
SAMPLE_GOAL = {
    "user_goal_type": "감량",            # 다중선택 가능 (comma-separated): ['감량', '유지', '증량', '재활']
    "user_goal_description": "4개월 내 체지방률 18%로 감소, 골격근량 10kg 증가, 체중 68kg 목표",
    "main_goal": "체성분 개선 (근육 증가 + 지방 감소)",
    "target_weight": 68.0,
    "target_date": "2026-06-30",
    "preferred_exercise_types": ["웨이트 트레이닝", "기능성 운동"],
    "available_days_per_week": 5,
    "available_time_per_session": 75,
    "restrictions": ["없음"]
}

# 재활 테스트용 목표 정보 (재활_허리 프로필과 함께 사용)
SAMPLE_GOAL_REHAB = {
    "user_goal_type": "재활, 감량",       # 다중선택 예시
    "user_goal_description": "허리 재활 — 수술 후 회복 중, 통증 없는 범위 내 운동 진행",
    "main_goal": "허리 안정화 및 코어 강화",
    "target_weight": None,
    "target_date": "2026-08-30",
    "preferred_exercise_types": ["맨몸운동", "스트레칭"],
    "available_days_per_week": 3,
    "available_time_per_session": 45,
    "restrictions": ["무거운 중량", "점프", "허리 비틀림"]
}
