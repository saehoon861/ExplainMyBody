"""
KCI API용 짧고 효과적인 검색어 모음

KCI는 제목(title)만 검색하므로 짧고 핵심적인 단어 사용 필수!
"""

# 체성분/인바디 관련 (핵심 키워드)
BODY_COMPOSITION_SIMPLE = [
    "체성분",
    "인바디",
    "BIA",
    "생체전기저항",
    "골격근량",
    "체지방률",
    "근육량",
]

# 근감소증/노화
SARCOPENIA_SIMPLE = [
    "근감소증",
    "사코페니아",
    "노인 근육",
    "근육 감소",
]

# 비만/내장지방
OBESITY_SIMPLE = [
    "내장지방",
    "복부비만",
    "체지방",
    "비만",
]

# 운동처방
EXERCISE_SIMPLE = [
    "저항운동",
    "유산소운동",
    "운동처방",
    "운동중재",
]

# 영양/단백질
NUTRITION_SIMPLE = [
    "단백질 섭취",
    "영양",
    "기초대사량",
]

# 대사증후군
METABOLIC_SIMPLE = [
    "대사증후군",
    "인슐린저항성",
    "당뇨병",
]

# 통합 검색어 (권장)
ALL_QUERIES = (
    BODY_COMPOSITION_SIMPLE +
    SARCOPENIA_SIMPLE +
    OBESITY_SIMPLE +
    EXERCISE_SIMPLE +
    NUTRITION_SIMPLE +
    METABOLIC_SIMPLE
)

print(f"총 {len(ALL_QUERIES)}개의 간단한 검색어")
print("각 검색어당 50-100개씩 수집하면 1000-2000개 논문 수집 가능!")
