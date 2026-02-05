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
    "workout_place": "아웃도어",              # "헬스장", "홈트", "아웃도어", "스포츠"
    "preferred_sport": ""                # workout_place가 "스포츠"일 때: "축구", "농구", "테니스", "배드민턴", "수영", "클라이밍", "기타"
}

# 샘플 사용자 프로필 (다양한 케이스)
SAMPLE_PROFILES = {
    "홈트_마른비만": {
        "body_type1": "마른비만형",
        "body_type2": "상체비만형",
        "workout_place": "홈트",
        "preferred_sport": "농구"
    },
    "헬스장_표준": {
        "body_type1": "표준형",
        "body_type2": "표준형",
        "workout_place": "헬스장",
        "preferred_sport": ""
    },
    "스포츠_축구": {
        "body_type1": "근육형",
        "body_type2": "상체발달형",
        "workout_place": "스포츠",
        "preferred_sport": "축구"
    },
    "아웃도어_비만": {
        "body_type1": "비만형",
        "body_type2": "하체비만형",
        "workout_place": "아웃도어",
        "preferred_sport": ""
    }
}

# 샘플 목표 정보
SAMPLE_GOAL = {
    "user_goal_type": "체지방 감소 및 근육 증가",
    "user_goal_description": "4개월 내 체지방률 18%로 감소, 골격근량 10kg 증가, 체중 68kg 목표",
    "main_goal": "체성분 개선 (근육 증가 + 지방 감소)",
    "target_weight": 68.0,
    "target_date": "2026-06-30",
    "preferred_exercise_types": ["웨이트 트레이닝", "기능성 운동"],
    "available_days_per_week": 5,
    "available_time_per_session": 75,
    "restrictions": ["없음"]
}
