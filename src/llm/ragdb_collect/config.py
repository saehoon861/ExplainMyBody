"""
RAG 코퍼스 수집 설정
4개 축 동등 분배 전략
"""

# ========== 1. 단백질/근육 증가 (목표: 800개) ==========
PROTEIN_HYPERTROPHY_QUERIES = [
    "(resistance training) AND (protein intake) AND hypertrophy",
    "muscle protein synthesis AND leucine",
    "whey supplementation AND strength gain",
    "protein dose response meta-analysis",
    "creatine supplementation AND muscle mass",
    "essential amino acids AND muscle building",
    "post-exercise protein AND recovery",
    "daily protein requirement AND athletes",
    "protein timing AND muscle hypertrophy",
    "casein protein AND overnight recovery",
]

PROTEIN_HYPERTROPHY_TARGET = 800

# ========== 2. 체지방 감량/다이어트 (목표: 800개) ==========
FAT_LOSS_QUERIES = [
    "calorie deficit AND fat loss AND body composition",
    "high protein diet AND weight loss AND lean mass",
    "intermittent fasting AND obesity meta-analysis",
    "dietary intervention AND fat mass reduction",
    "low carbohydrate diet AND weight loss",
    "energy restriction AND metabolic rate",
    "fat oxidation AND exercise intervention",
    "weight loss maintenance AND dietary adherence",
    "thermogenesis AND calorie expenditure",
    "body recomposition AND resistance training",
]

FAT_LOSS_TARGET = 800

# ========== 3. 한국형 식단/한식 (목표: 600개) ==========

# 영어 검색어 (PubMed)
KOREAN_DIET_QUERIES_EN = [
    "Korean diet AND health outcomes",
    "kimchi AND fermented foods AND microbiome",
    "dietary pattern AND Korean adults",
    "traditional Korean food AND obesity",
    "Korean National Health AND Nutrition Examination",
    "KNHANES AND protein intake",
]

# 한국어 검색어 (KCI)
KOREAN_DIET_QUERIES_KO = [
    "한식 식사패턴",
    "김치 섭취 건강",
    "한국형 식단 비만",
    "단백질 섭취 실태",
    "국민건강영양조사 단백질",
    "한국인 영양소 섭취",
    "발효식품 건강",
    "한식 건강 효과",
    "전통 식단 대사",
    "한국인 식사 구성",
]

KOREAN_DIET_TARGET = 600

# ========== 4. 체형 분석/인바디 (목표: 800개) ==========

# 영어 검색어
BODY_COMPOSITION_QUERIES_EN = [
    "bioelectrical impedance analysis AND body composition",
    "skeletal muscle mass index AND sarcopenia",
    "fat free mass AND resistance training intervention",
    "InBody validation study",
    "body composition assessment AND athletes",
    "muscle mass measurement AND BIA",
    "sarcopenia diagnosis AND muscle mass",
    "phase angle AND nutritional status",
]

# 한국어 검색어 (KCI)
BODY_COMPOSITION_QUERIES_KO = [
    "근감소증 한국인",
    "체성분 분석 인바디",
    "노인 단백질 섭취 근력",
    "골격근량 측정",
    "체지방률 기준",
    "생체전기임피던스",
]

BODY_COMPOSITION_TARGET = 800

# ========== PubMed API 설정 ==========
PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
PUBMED_EMAIL = "your_email@example.com"  # NCBI 요구사항
PUBMED_API_KEY = None  # 선택사항 (없으면 속도 제한 있음)
PUBMED_RESULTS_PER_QUERY = 100  # 쿼리당 가져올 결과 수

# ========== 출력 설정 ==========
OUTPUT_DIR = "outputs"
OUTPUT_FILE_PREFIX = "ragdb_corpus"

# ========== 도메인 매핑 ==========
DOMAIN_CONFIG = {
    "protein_hypertrophy": {
        "queries": PROTEIN_HYPERTROPHY_QUERIES,
        "target": PROTEIN_HYPERTROPHY_TARGET,
        "language": "en",
        "source": "PubMed",
    },
    "fat_loss": {
        "queries": FAT_LOSS_QUERIES,
        "target": FAT_LOSS_TARGET,
        "language": "en",
        "source": "PubMed",
    },
    "korean_diet": {
        "queries_en": KOREAN_DIET_QUERIES_EN,
        "queries_ko": KOREAN_DIET_QUERIES_KO,
        "target": KOREAN_DIET_TARGET,
        "language": "mixed",
        "source": "PubMed+KCI",
    },
    "body_composition": {
        "queries_en": BODY_COMPOSITION_QUERIES_EN,
        "queries_ko": BODY_COMPOSITION_QUERIES_KO,
        "target": BODY_COMPOSITION_TARGET,
        "language": "mixed",
        "source": "PubMed+KCI",
    },
}
