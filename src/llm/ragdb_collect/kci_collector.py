"""
KCI (한국학술지인용색인) 논문 수집
참고: KCI는 공식 API가 제한적이므로 수동 수집 가이드 제공
"""

from typing import List
from models import PaperMetadata


class KCICollector:
    """
    KCI 수집기 (수동 수집 가이드)

    KCI는 공식 API가 제한적이므로, 다음 방법으로 수집:
    1. KCI 웹사이트에서 검색 (https://www.kci.go.kr/)
    2. 검색 결과를 CSV/Excel로 다운로드
    3. 이 클래스의 parse_csv() 메서드로 변환

    또는:
    - KoreaScience (https://www.koreascience.or.kr/) 사용
    - RISS (http://www.riss.kr/) 사용
    """

    def __init__(self):
        self.base_url = "https://www.kci.go.kr/"

    def create_manual_guide(self) -> str:
        """수동 수집 가이드 생성"""
        guide = """
        ================================================
        KCI 한국어 논문 수집 가이드
        ================================================

        ## 방법 1: KCI 웹사이트 (권장)

        1. https://www.kci.go.kr/ 접속
        2. 검색창에 키워드 입력:
           - "한식 식사패턴"
           - "김치 섭취 건강"
           - "단백질 섭취 실태"
           etc.

        3. 검색 결과에서 "초록" 있는 논문만 선택
        4. "내보내기" → Excel/CSV 다운로드
        5. 아래 형식으로 정리:

        | title | abstract | keywords | year | authors | journal |
        |-------|----------|----------|------|---------|---------|

        6. CSV 저장 후 parse_csv() 사용

        ## 방법 2: KoreaScience

        1. https://www.koreascience.or.kr/ 접속
        2. 검색 후 논문 상세 페이지에서 초록 복사
        3. JSON 파일로 수동 작성

        ## 방법 3: RISS

        1. http://www.riss.kr/ 접속
        2. 검색 후 상세보기 → 초록 복사
        3. JSON 파일로 수동 작성

        ================================================
        예시 JSON 형식:
        ================================================

        [
            {
                "title": "한국인의 단백질 섭취 실태 연구",
                "abstract": "본 연구는 국민건강영양조사 자료를 활용하여...",
                "keywords": ["단백질", "섭취", "한국인"],
                "year": 2020,
                "authors": ["김철수", "이영희"],
                "journal": "한국영양학회지"
            }
        ]

        ================================================
        """
        return guide

    def parse_manual_json(
        self, json_data: List[dict], domain: str
    ) -> List[PaperMetadata]:
        """
        수동 작성한 JSON을 PaperMetadata로 변환

        Args:
            json_data: 논문 정보 리스트 (JSON)
            domain: 도메인 (korean_diet, body_composition)

        Returns:
            PaperMetadata 리스트
        """
        papers = []

        for item in json_data:
            if not item.get("abstract"):
                continue

            metadata = PaperMetadata(
                domain=domain,
                language="ko",
                title=item["title"],
                abstract=item["abstract"],
                keywords=item.get("keywords", []),
                source="KCI",
                year=item.get("year"),
                authors=item.get("authors", []),
                journal=item.get("journal"),
            )
            papers.append(metadata)

        return papers

    def save_template(self, filepath: str):
        """
        수동 수집용 템플릿 JSON 저장

        Args:
            filepath: 저장할 경로
        """
        template = [
            {
                "title": "논문 제목",
                "abstract": "초록 전문 (최소 100자 이상)",
                "keywords": ["키워드1", "키워드2", "키워드3"],
                "year": 2020,
                "authors": ["저자1", "저자2"],
                "journal": "학술지명",
            }
        ]

        import json

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(template, f, ensure_ascii=False, indent=2)

        print(f"✅ 템플릿 저장 완료: {filepath}")
        print("이 파일을 복사하여 논문 정보를 입력하세요.")


# ========== 간단한 스크래핑 예시 (참고용) ==========
# 주의: 웹사이트 이용약관 확인 필요

def scrape_koreascience_example(keyword: str) -> List[dict]:
    """
    KoreaScience 간단 스크래핑 예시 (참고용)

    실제 사용 시:
    1. robots.txt 확인
    2. 이용약관 확인
    3. Rate limit 준수
    """
    # TODO: 실제 구현 필요
    # import requests
    # from bs4 import BeautifulSoup

    print("⚠️  이 함수는 예시입니다. 실제 사용 시 이용약관을 확인하세요.")
    return []
