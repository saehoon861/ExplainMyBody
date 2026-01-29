"""
ScienceON API Gateway를 사용한 한국어 논문 자동 수집

KISTI의 ScienceON API를 사용하여 과학기술 논문을 자동으로 수집합니다.
1억 3780만 건 이상의 논문 데이터베이스 (2026-01-19 기준)

API 키 발급:
https://scienceon.kisti.re.kr/apigateway/
"""

import requests
import time
import json
from typing import List, Optional, Dict
from datetime import datetime
from pathlib import Path

from models import PaperMetadata


class ScienceOnAPICollector:
    """ScienceON API Gateway 수집기"""

    def __init__(self, client_id: str, client_secret: str):
        """
        Args:
            client_id: API 클라이언트 ID
            client_secret: API 클라이언트 시크릿
        """
        self.client_id = client_id
        self.client_secret = client_secret

        # ScienceON API Gateway 엔드포인트
        self.base_url = "https://scienceon.kisti.re.kr/api"
        self.token_url = f"{self.base_url}/auth/token"
        self.search_url = f"{self.base_url}/article/search"

        # 액세스 토큰 (2시간 유효)
        self.access_token = None
        self.token_expires_at = None

        # Rate limiting
        self.rate_limit = 0.5  # 0.5초 대기

    def _get_access_token(self) -> str:
        """OAuth 2.0 액세스 토큰 발급"""

        # 토큰이 유효하면 재사용
        if self.access_token and self.token_expires_at:
            if datetime.now().timestamp() < self.token_expires_at:
                return self.access_token

        print("🔑 액세스 토큰 발급 중...")

        try:
            # 토큰 요청
            payload = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }

            response = requests.post(self.token_url, data=payload, timeout=30)

            if response.status_code != 200:
                raise Exception(f"토큰 발급 실패 (status: {response.status_code})")

            data = response.json()

            self.access_token = data['access_token']
            # 2시간 후 만료 (조금 여유있게 1시간 50분으로 설정)
            self.token_expires_at = datetime.now().timestamp() + (110 * 60)

            print("✅ 액세스 토큰 발급 완료")
            return self.access_token

        except Exception as e:
            print(f"❌ 토큰 발급 실패: {e}")
            raise

    def search_papers(
        self,
        query: str,
        max_results: int = 100,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        language: str = "ko"  # ko: 한국어, en: 영어
    ) -> List[dict]:
        """
        ScienceON에서 논문 검색

        Args:
            query: 검색어
            max_results: 최대 결과 수
            start_year: 시작 연도
            end_year: 종료 연도
            language: 언어 필터 (ko, en)

        Returns:
            논문 정보 딕셔너리 리스트
        """
        papers = []

        print(f"\n🔍 ScienceON 검색: '{query}' (최대 {max_results}개)")

        # 액세스 토큰 획득
        token = self._get_access_token()

        # 페이지네이션
        page_size = 100
        total_pages = (max_results + page_size - 1) // page_size

        for page in range(1, total_pages + 1):
            try:
                # API 요청 헤더
                headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }

                # API 요청 파라미터
                params = {
                    'q': query,
                    'size': min(page_size, max_results - len(papers)),
                    'from': (page - 1) * page_size,
                    'lang': language,
                }

                # 연도 필터
                if start_year or end_year:
                    year_filter = {}
                    if start_year:
                        year_filter['gte'] = start_year
                    if end_year:
                        year_filter['lte'] = end_year
                    params['year'] = year_filter

                # API 요청
                response = requests.get(
                    self.search_url,
                    headers=headers,
                    params=params,
                    timeout=30
                )

                if response.status_code == 401:
                    # 토큰 만료, 재발급
                    print("  🔄 토큰 만료, 재발급...")
                    self.access_token = None
                    token = self._get_access_token()
                    headers['Authorization'] = f'Bearer {token}'
                    response = requests.get(
                        self.search_url,
                        headers=headers,
                        params=params,
                        timeout=30
                    )

                if response.status_code != 200:
                    print(f"  ⚠️ API 요청 실패 (status: {response.status_code})")
                    break

                # JSON 파싱
                data = response.json()

                # 총 결과 수
                if page == 1 and 'total' in data:
                    total = data['total']
                    print(f"  📊 총 {total:,}개 논문 발견")

                # 논문 정보 추출
                items = data.get('items', [])

                if not items:
                    print(f"  ⚠️ {page}페이지에 결과 없음")
                    break

                for item in items:
                    paper_info = self._parse_scienceon_item(item)
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

        print(f"✅ ScienceON 검색 완료: {len(papers)}개 수집")
        return papers

    def _parse_scienceon_item(self, item: dict) -> Optional[dict]:
        """ScienceON JSON 아이템을 딕셔너리로 파싱"""
        try:
            # 제목
            title = item.get('title', '').strip()
            if not title:
                return None

            # 초록
            abstract = item.get('abstract', '').strip()

            # 초록이 너무 짧으면 스킵
            if len(abstract) < 100:
                return None

            # 키워드
            keywords = item.get('keywords', [])
            if isinstance(keywords, str):
                keywords = [k.strip() for k in keywords.split(',')]

            # 연도
            year = item.get('year')
            if year:
                try:
                    year = int(year)
                except:
                    year = None

            # 저자
            authors_raw = item.get('authors', [])
            authors = []
            if isinstance(authors_raw, list):
                for author in authors_raw[:5]:
                    if isinstance(author, dict):
                        name = author.get('name', '')
                    else:
                        name = str(author)
                    if name:
                        authors.append(name.strip())
            elif isinstance(authors_raw, str):
                authors = [a.strip() for a in authors_raw.split(',')][:5]

            # 저널
            journal = item.get('journal', {})
            if isinstance(journal, dict):
                journal_name = journal.get('title', 'ScienceON')
            else:
                journal_name = str(journal) if journal else 'ScienceON'

            # DOI
            doi = item.get('doi')

            return {
                'title': title,
                'abstract': abstract,
                'keywords': keywords,
                'year': year,
                'authors': authors,
                'journal': journal_name,
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
        start_year: int = 2010
    ) -> List[PaperMetadata]:
        """
        특정 도메인의 논문 수집

        Args:
            domain: 도메인 분류
            queries: 검색어 리스트
            target_count: 목표 수집 개수
            start_year: 시작 연도

        Returns:
            PaperMetadata 리스트
        """
        all_papers = []
        seen_titles = set()

        results_per_query = max(10, target_count // len(queries))
        current_year = datetime.now().year

        for query in queries:
            papers_data = self.search_papers(
                query=query,
                max_results=results_per_query,
                start_year=start_year,
                end_year=current_year,
                language='ko'
            )

            # PaperMetadata로 변환
            for data in papers_data:
                # 중복 체크
                title_normalized = data['title'].lower().strip()
                if title_normalized in seen_titles:
                    continue

                seen_titles.add(title_normalized)

                # PaperMetadata 생성
                paper = PaperMetadata(
                    domain=domain,
                    language='ko',
                    title=data['title'],
                    abstract=data['abstract'],
                    keywords=data['keywords'],
                    source='ScienceON',
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

            # 쿼리 간 대기
            time.sleep(2)

        return all_papers[:target_count]


def main():
    """메인 실행 함수"""

    print("=" * 60)
    print("🇰🇷 ScienceON API 한국어 논문 수집")
    print("=" * 60)
    print("📊 데이터베이스: 1억 3780만 건 이상 (2026-01-19 기준)")
    print("=" * 60)

    # API 키 입력
    print("\n📋 ScienceON API 키 발급:")
    print("  1. https://scienceon.kisti.re.kr/apigateway/ 접속")
    print("  2. 회원가입 → API 사용 신청")
    print("  3. 승인 후 Client ID, Client Secret 발급")
    print("")

    client_id = input("Client ID를 입력하세요: ").strip()
    client_secret = input("Client Secret을 입력하세요: ").strip()

    if not client_id or not client_secret:
        print("❌ Client ID와 Client Secret이 필요합니다.")
        return

    # 수집기 초기화
    collector = ScienceOnAPICollector(
        client_id=client_id,
        client_secret=client_secret
    )

    # 한국어 검색어
    KOREAN_DIET_QUERIES = [
        "한식 영양",
        "김치 건강",
        "발효식품",
        "한국 식습관",
        "전통음식",
    ]

    BODY_COMPOSITION_QUERIES = [
        "근감소증",
        "체성분 분석",
        "골격근량",
        "체지방",
        "생체전기저항",
    ]

    # 한국 식단 수집
    print("\n" + "=" * 60)
    print("📚 도메인 1: 한국형 식단 (목표: 300개)")
    print("=" * 60)

    korean_diet_papers = collector.collect_domain(
        domain='korean_diet',
        queries=KOREAN_DIET_QUERIES,
        target_count=300,
        start_year=2010
    )

    # 체형 분석 수집
    print("\n" + "=" * 60)
    print("📚 도메인 2: 체형 분석/인바디 (목표: 300개)")
    print("=" * 60)

    body_comp_papers = collector.collect_domain(
        domain='body_composition',
        queries=BODY_COMPOSITION_QUERIES,
        target_count=300,
        start_year=2010
    )

    # 전체 수집 결과
    all_papers = korean_diet_papers + body_comp_papers

    # 결과 저장
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 전체 저장
    corpus_path = output_dir / f"scienceon_korean_{timestamp}.json"
    with open(corpus_path, "w", encoding="utf-8") as f:
        json.dump([p.model_dump() for p in all_papers], f, ensure_ascii=False, indent=2)

    print(f"\n✅ 저장 완료: {corpus_path}")

    # 도메인별 저장
    if korean_diet_papers:
        diet_path = output_dir / f"korean_diet_scienceon_{timestamp}.json"
        with open(diet_path, "w", encoding="utf-8") as f:
            json.dump([p.model_dump() for p in korean_diet_papers], f, ensure_ascii=False, indent=2)
        print(f"   - 한국 식단: {diet_path} ({len(korean_diet_papers)}개)")

    if body_comp_papers:
        body_path = output_dir / f"body_composition_scienceon_{timestamp}.json"
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
