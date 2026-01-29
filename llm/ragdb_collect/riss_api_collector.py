"""
RISS OpenAPI를 사용한 한국어 논문 자동 수집

공공데이터포털 또는 RISS API 센터에서 발급받은 API 키를 사용하여
학술연구정보서비스(RISS)의 논문 정보를 자동으로 수집합니다.

API 키 발급:
- 공공데이터포털: https://www.data.go.kr/data/3046254/openapi.do
- RISS API 센터: https://www.riss.kr/openAPI/OpenApiMain.do
"""

import requests
import time
import json
from typing import List, Optional
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET

from models import PaperMetadata


class RISSAPICollector:
    """RISS OpenAPI 수집기"""

    def __init__(self, api_key: str):
        """
        Args:
            api_key: RISS에서 발급받은 API 키
        """
        self.api_key = api_key

        # RISS OpenAPI 엔드포인트
        # 국내학술지논문
        self.search_url = "http://www.riss.kr/openapi/search/search.jsp"

        # Rate limiting
        self.rate_limit = 1.0  # 1초에 1개 요청

    def search_papers(
        self,
        query: str,
        max_results: int = 100,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        paper_type: str = "ARTICLE"  # ARTICLE(학술지), THESIS(학위논문)
    ) -> List[dict]:
        """
        RISS에서 논문 검색

        Args:
            query: 검색어 (한국어)
            max_results: 최대 결과 수
            start_year: 시작 연도
            end_year: 종료 연도
            paper_type: ARTICLE(학술지) 또는 THESIS(학위논문)

        Returns:
            논문 정보 딕셔너리 리스트
        """
        papers = []

        print(f"\n🔍 RISS 검색: '{query}' (최대 {max_results}개)")

        # 페이지네이션 (한 번에 100개씩)
        page_size = 100
        total_pages = (max_results + page_size - 1) // page_size

        for page in range(1, total_pages + 1):
            try:
                # API 요청 파라미터
                params = {
                    'apikey': self.api_key,
                    'query': query,
                    'displayCount': min(page_size, max_results - len(papers)),
                    'startIndex': (page - 1) * page_size + 1,
                    'searchGubun': paper_type,
                }

                # 연도 필터
                if start_year and end_year:
                    params['pubYear'] = f"{start_year}~{end_year}"
                elif start_year:
                    params['pubYear'] = f"{start_year}~{datetime.now().year}"

                # API 요청
                response = requests.get(self.search_url, params=params, timeout=30)

                if response.status_code != 200:
                    print(f"  ⚠️ API 요청 실패 (status: {response.status_code})")
                    break

                # XML 파싱
                root = ET.fromstring(response.content)

                # 총 결과 수
                total_elem = root.find('.//result/totalCount')
                if total_elem is not None and page == 1:
                    total = int(total_elem.text)
                    print(f"  📊 총 {total}개 논문 발견")

                # 논문 정보 추출
                items = root.findall('.//items/item')

                if not items:
                    print(f"  ⚠️ {page}페이지에 결과 없음")
                    break

                for item in items:
                    paper_info = self._parse_riss_item(item)
                    if paper_info:
                        papers.append(paper_info)

                print(f"  ✅ {page}/{total_pages} 페이지: {len(items)}개 수집 (총 {len(papers)}개)")

                # Rate limiting
                time.sleep(self.rate_limit)

                # 목표 달성
                if len(papers) >= max_results:
                    break

            except Exception as e:
                print(f"  ❌ 페이지 {page} 처리 실패: {e}")
                continue

        print(f"✅ RISS 검색 완료: {len(papers)}개 수집")
        return papers

    def _parse_riss_item(self, item: ET.Element) -> Optional[dict]:
        """RISS XML 아이템을 딕셔너리로 파싱"""
        try:
            # 제목
            title_elem = item.find('.//title')
            title = title_elem.text if title_elem is not None else None

            if not title:
                return None

            # 초록
            abstract_elem = item.find('.//abstract')
            abstract = abstract_elem.text if abstract_elem is not None else ""

            # 초록이 너무 짧으면 스킵
            if len(abstract) < 100:
                return None

            # 키워드
            keywords = []
            keyword_elem = item.find('.//keyword')
            if keyword_elem is not None and keyword_elem.text:
                # 세미콜론 또는 쉼표로 구분
                kw_text = keyword_elem.text.replace(';', ',')
                keywords = [k.strip() for k in kw_text.split(',') if k.strip()]

            # 연도
            year_elem = item.find('.//pubYear')
            year = None
            if year_elem is not None and year_elem.text:
                try:
                    year = int(year_elem.text)
                except:
                    pass

            # 저자
            authors = []
            author_elem = item.find('.//author')
            if author_elem is not None and author_elem.text:
                # 세미콜론으로 구분
                author_text = author_elem.text.replace(';', ',')
                authors = [a.strip() for a in author_text.split(',') if a.strip()][:5]

            # 저널/학회지
            journal_elem = item.find('.//publisher')
            journal = journal_elem.text if journal_elem is not None else "RISS 학술지"

            # DOI
            doi_elem = item.find('.//doi')
            doi = doi_elem.text if doi_elem is not None else None

            return {
                'title': title,
                'abstract': abstract,
                'keywords': keywords,
                'year': year,
                'authors': authors,
                'journal': journal,
                'doi': doi
            }

        except Exception as e:
            print(f"  ⚠️ 아이템 파싱 실패: {e}")
            return None

    def collect_domain(
        self,
        domain: str,
        queries: List[str],
        target_count: int,
        start_year: int = 2010,
        include_thesis: bool = False
    ) -> List[PaperMetadata]:
        """
        특정 도메인의 논문 수집

        Args:
            domain: 도메인 분류
            queries: 검색어 리스트
            target_count: 목표 수집 개수
            start_year: 시작 연도
            include_thesis: 학위논문 포함 여부

        Returns:
            PaperMetadata 리스트
        """
        all_papers = []
        seen_titles = set()

        results_per_query = max(10, target_count // len(queries))
        current_year = datetime.now().year

        # 논문 유형
        paper_types = ["ARTICLE"]  # 학술지
        if include_thesis:
            paper_types.append("THESIS")  # 학위논문

        for query in queries:
            for paper_type in paper_types:
                papers_data = self.search_papers(
                    query=query,
                    max_results=results_per_query // len(paper_types),
                    start_year=start_year,
                    end_year=current_year,
                    paper_type=paper_type
                )

                # PaperMetadata로 변환
                for data in papers_data:
                    # 중복 체크
                    title_normalized = data['title'].lower().strip()
                    if title_normalized in seen_titles:
                        continue

                    seen_titles.add(title_normalized)

                    # 출처 표시
                    source = "RISS 학술지" if paper_type == "ARTICLE" else "RISS 학위논문"

                    # PaperMetadata 생성
                    paper = PaperMetadata(
                        domain=domain,
                        language='ko',
                        title=data['title'],
                        abstract=data['abstract'],
                        keywords=data['keywords'],
                        source=source,
                        year=data['year'],
                        pmid=None,
                        doi=data.get('doi'),
                        authors=data['authors'],
                        journal=data['journal']
                    )

                    all_papers.append(paper)

                # 목표 달성
                if len(all_papers) >= target_count:
                    break

            if len(all_papers) >= target_count:
                break

            # 쿼리 간 대기
            time.sleep(2)

        return all_papers[:target_count]


def main():
    """메인 실행 함수"""

    print("=" * 60)
    print("🇰🇷 RISS OpenAPI 한국어 논문 수집")
    print("=" * 60)

    # API 키 입력
    print("\n📋 RISS API 키 발급:")
    print("  1. https://www.data.go.kr/ 또는 https://www.riss.kr/")
    print("  2. 회원가입 → API 키 신청")
    print("  3. 승인 후 API 키 발급")
    print("")

    api_key = input("API 키를 입력하세요: ").strip()

    if not api_key:
        print("❌ API 키가 필요합니다.")
        return

    # 수집기 초기화
    collector = RISSAPICollector(api_key=api_key)

    # 한국어 검색어
    KOREAN_DIET_QUERIES = [
        "한식 건강",
        "김치 영양",
        "한국인 식습관",
        "발효식품 효과",
        "전통식단",
    ]

    BODY_COMPOSITION_QUERIES = [
        "근감소증",
        "체성분",
        "골격근",
        "체지방",
        "인바디",
    ]

    # 학위논문 포함 여부
    include_thesis = input("\n학위논문도 포함할까요? (y/n, 기본: n): ").strip().lower() == 'y'

    # 한국 식단 수집
    print("\n" + "=" * 60)
    print("📚 도메인 1: 한국형 식단 (목표: 300개)")
    print("=" * 60)

    korean_diet_papers = collector.collect_domain(
        domain='korean_diet',
        queries=KOREAN_DIET_QUERIES,
        target_count=300,
        start_year=2010,
        include_thesis=include_thesis
    )

    # 체형 분석 수집
    print("\n" + "=" * 60)
    print("📚 도메인 2: 체형 분석/인바디 (목표: 300개)")
    print("=" * 60)

    body_comp_papers = collector.collect_domain(
        domain='body_composition',
        queries=BODY_COMPOSITION_QUERIES,
        target_count=300,
        start_year=2010,
        include_thesis=include_thesis
    )

    # 전체 수집 결과
    all_papers = korean_diet_papers + body_comp_papers

    # 결과 저장
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 전체 저장
    corpus_path = output_dir / f"riss_korean_{timestamp}.json"
    with open(corpus_path, "w", encoding="utf-8") as f:
        json.dump([p.model_dump() for p in all_papers], f, ensure_ascii=False, indent=2)

    print(f"\n✅ 저장 완료: {corpus_path}")

    # 도메인별 저장
    if korean_diet_papers:
        diet_path = output_dir / f"korean_diet_riss_{timestamp}.json"
        with open(diet_path, "w", encoding="utf-8") as f:
            json.dump([p.model_dump() for p in korean_diet_papers], f, ensure_ascii=False, indent=2)
        print(f"   - 한국 식단: {diet_path} ({len(korean_diet_papers)}개)")

    if body_comp_papers:
        body_path = output_dir / f"body_composition_riss_{timestamp}.json"
        with open(body_path, "w", encoding="utf-8") as f:
            json.dump([p.model_dump() for p in body_comp_papers], f, ensure_ascii=False, indent=2)
        print(f"   - 체형 분석: {body_path} ({len(body_comp_papers)}개)")

    # 통계
    print("\n" + "=" * 60)
    print("📊 수집 완료")
    print("=" * 60)
    print(f"총 수집: {len(all_papers)}개")
    print(f"  - 한국 식단: {len(korean_diet_papers)}개")
    print(f"  - 체형 분석: {len(body_comp_papers)}개")
    print("=" * 60)


if __name__ == "__main__":
    main()
