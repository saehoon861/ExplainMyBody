"""
KCI OpenAPI를 사용한 한국어 논문 자동 수집

공공데이터포털(data.go.kr)에서 발급받은 API 키를 사용하여
한국학술지인용색인(KCI)의 논문 정보를 자동으로 수집합니다.

API 키 발급:
https://www.data.go.kr/data/3049042/openapi.do
https://www.data.go.kr/data/15085348/openapi.do
"""

import requests
import time
import json
from typing import List, Optional
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET

from models import PaperMetadata


class KCIAPICollector:
    """KCI OpenAPI 수집기"""

    def __init__(self, api_key: str):
        """
        Args:
            api_key: 공공데이터포털에서 발급받은 API 키
        """
        self.api_key = api_key

        # KCI Open API 엔드포인트 (KCI 직접)
        self.base_url = "https://open.kci.go.kr/po/openapi/openApiSearch.kci"

        # Rate limiting
        self.rate_limit = 1.0  # 1초에 1개 요청

    def search_papers(
        self,
        query: str,
        max_results: int = 100,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> List[dict]:
        """
        KCI에서 논문 검색

        Args:
            query: 검색어 (한국어)
            max_results: 최대 결과 수
            start_year: 시작 연도
            end_year: 종료 연도

        Returns:
            논문 정보 딕셔너리 리스트
        """
        papers = []

        print(f"\n🔍 KCI 검색: '{query}' (최대 {max_results}개)")

        # 페이지네이션 (한 번에 100개씩 가져올 수 있음)
        page_size = 100
        total_pages = (max_results + page_size - 1) // page_size

        for page in range(1, total_pages + 1):
            try:
                # API 요청 파라미터 (KCI 직접 API 형식)
                params = {
                    'apiCode': 'articleSearch',  # 논문 검색
                    'key': self.api_key,  # API 키
                    'keyword': query,  # 키워드 검색 (제목+초록)
                    'displayCount': min(page_size, max_results - len(papers)),  # 한 페이지 결과 수
                    'pageNo': page,  # 페이지 번호
                }

                # 연도 필터 (있는 경우)
                if start_year:
                    params['startYear'] = str(start_year)
                if end_year:
                    params['endYear'] = str(end_year)

                # API 요청
                response = requests.get(self.base_url, params=params, timeout=30)

                if response.status_code != 200:
                    print(f"  ⚠️ API 요청 실패 (status: {response.status_code})")
                    print(f"     응답: {response.text[:200]}")
                    break

                # XML 파싱
                root = ET.fromstring(response.content)

                # 에러 체크 (다양한 형식 시도)
                error_elem = root.find('.//error')
                if error_elem is not None:
                    error_msg = error_elem.text or "Unknown error"
                    print(f"  ⚠️ API 에러: {error_msg}")
                    break

                # 총 결과 수 확인 (다양한 태그 시도)
                total = None
                for tag in ['.//totalCount', './/total', './/recordCount']:
                    total_elem = root.find(tag)
                    if total_elem is not None and total_elem.text:
                        try:
                            total = int(total_elem.text)
                            if page == 1:
                                print(f"  📊 총 {total}개 논문 발견")
                            break
                        except:
                            pass

                # 논문 정보 추출 (다양한 경로 시도)
                items = []
                for path in ['.//records/record', './/items/item', './/list/item', './/record', './/item']:
                    items = root.findall(path)
                    if items:
                        break

                if not items:
                    print(f"  ⚠️ {page}페이지에 결과 없음")
                    break

                for item in items:
                    paper_info = self._parse_kci_item(item)
                    if paper_info:
                        papers.append(paper_info)

                print(f"  ✅ {page}/{total_pages} 페이지: {len(items)}개 수집 (총 {len(papers)}개)")

                # Rate limiting
                time.sleep(self.rate_limit)

                # 목표 달성 시 중단
                if len(papers) >= max_results:
                    break

            except Exception as e:
                print(f"  ❌ 페이지 {page} 처리 실패: {e}")
                continue

        print(f"✅ KCI 검색 완료: {len(papers)}개 수집")
        return papers

    def _parse_kci_item(self, item: ET.Element) -> Optional[dict]:
        """KCI XML 아이템을 딕셔너리로 파싱"""
        try:
            # 제목 (여러 가능한 태그 시도)
            title = None
            for tag in ['.//articleTitle', './/title', './/article-title']:
                title_elem = item.find(tag)
                if title_elem is not None and title_elem.text:
                    title = title_elem.text.strip()
                    break

            if not title:
                return None

            # 초록
            abstract = ""
            for tag in ['.//abstract', './/summary']:
                abstract_elem = item.find(tag)
                if abstract_elem is not None and abstract_elem.text:
                    abstract = abstract_elem.text.strip()
                    break

            # 초록이 너무 짧으면 스킵
            if len(abstract) < 100:
                return None

            # 키워드
            keywords = []
            for tag in ['.//keyword', './/keywords']:
                keyword_elem = item.find(tag)
                if keyword_elem is not None and keyword_elem.text:
                    # 세미콜론 또는 쉼표로 구분
                    kw_text = keyword_elem.text.replace(';', ',')
                    keywords = [k.strip() for k in kw_text.split(',') if k.strip()]
                    break

            # 연도
            year = None
            for tag in ['.//pubiYr', './/pub-year', './/year']:
                year_elem = item.find(tag)
                if year_elem is not None and year_elem.text:
                    try:
                        year = int(year_elem.text.strip())
                    except:
                        pass
                    break

            # 저자
            authors = []
            for tag in ['.//author', './/authors', './/creator']:
                author_elem = item.find(tag)
                if author_elem is not None and author_elem.text:
                    # 세미콜론 또는 쉼표로 구분
                    author_text = author_elem.text.replace(';', ',')
                    authors = [a.strip() for a in author_text.split(',') if a.strip()][:5]
                    break

            # 저널
            journal = "KCI 학술지"
            for tag in ['.//journalTitle', './/journal-title', './/journal']:
                journal_elem = item.find(tag)
                if journal_elem is not None and journal_elem.text:
                    journal = journal_elem.text.strip()
                    break

            # DOI
            doi = None
            doi_elem = item.find('.//doi')
            if doi_elem is not None and doi_elem.text:
                doi = doi_elem.text.strip()

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
        seen_titles = set()  # 중복 제거

        results_per_query = max(10, target_count // len(queries))
        current_year = datetime.now().year

        for query in queries:
            papers_data = self.search_papers(
                query=query,
                max_results=results_per_query,
                start_year=start_year,
                end_year=current_year
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
                    source='KCI',
                    year=data['year'],
                    pmid=None,
                    doi=data.get('doi'),
                    authors=data['authors'],
                    journal=data['journal']
                )

                all_papers.append(paper)

            # 목표 달성 확인
            if len(all_papers) >= target_count:
                break

            # 쿼리 간 대기
            time.sleep(2)

        return all_papers[:target_count]


def main():
    """메인 실행 함수"""

    print("=" * 60)
    print("🇰🇷 KCI OpenAPI 한국어 논문 수집")
    print("=" * 60)

    # API 키 입력
    print("\n📋 KCI API 키 발급:")
    print("  1. https://www.data.go.kr/ 회원가입")
    print("  2. 'KCI 논문정보서비스' 검색")
    print("  3. 활용신청 → API 키 발급")
    print("")

    api_key = input("API 키를 입력하세요: ").strip()

    if not api_key:
        print("❌ API 키가 필요합니다.")
        return

    # 수집기 초기화
    collector = KCIAPICollector(api_key=api_key)

    # 한국어 검색어
    BODY_COMPOSITION_QUERIES = [
    "BIA 체성분 그래프 패턴별 대사적 위험도 분석"
    "체지방률 및 골격근량 지수(SMI) 기반의 체형 분류 모델"
    "체형부위별 근육 불균형(Segmental Lean Analysis)과 신체 기능의 상관관계"
    "상·하체 근육량 비율에 따른 근감소성 비만(Sarcopenic Obesity) 판정 기준"
    "InBody 데이터를 활용한 체형 지수(Body Shape Index) 산출 로직"
    "체성분 분석 결과에 따른 맞춤형 운동 강도(FITT) 설정 근거"
    "근육량 및 기초대사량 기반의 유산소·무산소 운동 배분 전략"
    "운동 숙련도별 체성분 변화 양상 및 적정 운동 처방 모델"
    "홈 트레이닝과 휘트니스 센터 기반 운동 프로그램의 체성분 개선 효과 비교"
    "심박수 및 기초대사량을 고려한 목표 칼로리 소비량 산정 로직"
    "복부지방률(WHR) 및 내장지방레벨에 따른 고강도 인터벌 트레이닝(HIIT)의 효과"
    "좌우측 상하지 근육 불균형 교정을 위한 편측성 운동(Unilateral Exercise) 처방"
    "신체 부위별 체지방 분포와 인슐린 저항성 간의 관계"
    "무기질 및 단백질 섭취 상태와 근력 운동 효율의 상관성"
        
    ]

    INBODY_BIA_KR_QUERIES = [
    "생체전기저항분석 체성분 평가",
    "인바디 체성분 분석 신뢰도",
    "생체전기저항법 골격근량 정확도",
    "DXA와 생체전기저항분석 비교",
    "체성분 측정방법 타당도 연구",
    ]

    BODY_TYPE_CLASSIFICATION_KR_QUERIES = [
    "체성분 기반 체형 분류",
    "체지방량 골격근량 체형 유형",
    "근육-지방 불균형 체형 분석",
    "체성분 지표를 이용한 군집분석",
    "비만 유형 체성분 phenotype 연구",
    ]

    SARCOPENIA_KR_QUERIES = [
    "근감소증 골격근량 기준 한국인",
    "아시아 근감소증 진단기준 생체전기저항",
    "사지골격근량지수(SMI) 참고치",
    "노인 근육량 감소 체성분 연구",
    "근감소성 비만 한국인 유병률",
    ]

    BODYFAT_OBESITY_KR_QUERIES = [
    "체지방률 기준 한국인",
    "BMI와 체지방률 비교 연구",
    "정상체중비만 체성분 분석",
    "비만도 평가 체성분 지표",
    "체지방량과 대사질환 위험",
    ]
    
    VISCERAL_FAT_KR_QUERIES = [
    "내장지방 수준 대사증후군 위험",
    "복부비만 내장지방 체성분 분석",
    "내장지방면적과 인슐린저항성",
    "중심성비만 건강위험 연구",
    "생체전기저항분석 내장지방 추정",
    ]

    SEGMENTAL_BALANCE_KR_QUERIES = [
    "부위별 골격근량 불균형 분석",
    "사지 근육량 좌우 차이",
    "팔 다리 근육 비대칭 체성분",
    "부위별 체지방 분포 연구",
    "국소 체성분 불균형 운동처방",
    ]

    EXERCISE_INTERVENTION_KR_QUERIES = [
    "저항운동 골격근량 증가 체성분 변화",
    "유산소운동 내장지방 감소 효과",
    "복합운동 체지방률 개선 연구",
    "운동중재 체성분 개선 프로그램",
    "운동처방 기반 체성분 분석",
    ]

    MUSCLE_ADJUSTMENT_KR_QUERIES = [
    "근육량 증가 프로그램 효과",
    "단백질 섭취와 근육량 변화",
    "근감소 예방 저항성운동 처방",
    "제지방량 증가 중재연구",
    ]

    BMR_NUTRITION_KR_QUERIES = [
    "기초대사량과 제지방량 관계",
    "체성분 기반 에너지 필요량 추정",
    "권장섭취열량 산정 체성분 연구",
    "체중조절 프로그램 대사량 변화",
    ]

    METABOLIC_RISK_KR_QUERIES = [
    "체성분과 대사증후군 위험",
    "골격근량과 당뇨병 위험",
    "내장지방과 심혈관질환 연관",
    "체성분 지표 건강예측모델",
    ]

    # 체형 분석 수집 (목표: 200-300개)
    print("\n" + "=" * 60)
    print("📚 도메인 2: 체형 분석/인바디 (목표: 500개)")
    print("=" * 60)

    body_comp_papers1 = collector.collect_domain(
        domain='body_composition',
        queries=BODY_COMPOSITION_QUERIES,
        target_count=500,
        start_year=2010
    )
    # 체형 분석 수집 (목표: 200-300개)
    print("\n" + "=" * 60)
    print("📚 도메인 3: 인바디/체성분 분석 핵심 키워드 (목표: 250개)")
    print("=" * 60)

    body_comp_papers2 = collector.collect_domain(
        domain='body_composition',
        queries=INBODY_BIA_KR_QUERIES,
        target_count=250,
        start_year=2010
    )
    # 체형 분석 수집 (목표: 200-300개)
    print("\n" + "=" * 60)
    print("📚 도메인 4: 체형분석/체성분 기반 유형화 (목표: 250개)")
    print("=" * 60)

    body_comp_papers3 = collector.collect_domain(
        domain='body_composition',
        queries=BODY_TYPE_CLASSIFICATION_KR_QUERIES,
        target_count=250,
        start_year=2010
    )
    # 체형 분석 수집 (목표: 200-300개)
    print("\n" + "=" * 60)
    print("📚 도메인 5: 근감소증 + 근감소성비만 (목표: 250개)")
    print("=" * 60)

    body_comp_papers4 = collector.collect_domain(
        domain='body_composition',
        queries=SARCOPENIA_KR_QUERIES,
        target_count=250,
        start_year=2010
    )
    # 체형 분석 수집 (목표: 200-300개)
    print("\n" + "=" * 60)
    print("📚 도메인 6: 체지방률·비만도·BMI 한계 (목표: 250개)")
    print("=" * 60)

    body_comp_papers5 = collector.collect_domain(
        domain='body_composition',
        queries=BODYFAT_OBESITY_KR_QUERIES,
        target_count=250,
        start_year=2010
    )
    # 체형 분석 수집 (목표: 200-300개)
    print("\n" + "=" * 60)
    print("📚 도메인 7: 복부지방률·내장지방 레벨 (목표: 250개)")
    print("=" * 60)

    body_comp_papers6 = collector.collect_domain(
        domain='body_composition',
        queries=VISCERAL_FAT_KR_QUERIES,
        target_count=250,
        start_year=2010
    )
    # 체형 분석 수집 (목표: 200-300개)
    print("\n" + "=" * 60)
    print("📚 도메인 8: 부위별 근육/지방 불균형 (Segmental) (목표: 250개)")
    print("=" * 60)

    body_comp_papers7 = collector.collect_domain(
        domain='body_composition',
        queries=SEGMENTAL_BALANCE_KR_QUERIES,
        target_count=250,
        start_year=2010
    )
    # 체형 분석 수집 (목표: 200-300개)
    print("\n" + "=" * 60)
    print("📚 도메인 9: 운동처방 근거 (근육 증가/지방 감소) (목표: 250개)")
    print("=" * 60)

    body_comp_papers8 = collector.collect_domain(
        domain='body_composition',
        queries=EXERCISE_INTERVENTION_KR_QUERIES,
        target_count=250,
        start_year=2010
    )
    # 체형 분석 수집 (목표: 200-300개)
    print("\n" + "=" * 60)
    print("📚 도메인 10: 기초대사량(BMR) + 에너지 처방 (목표: 250개)")
    print("=" * 60)

    body_comp_papers9 = collector.collect_domain(
        domain='body_composition',
        queries=MUSCLE_ADJUSTMENT_KR_QUERIES,
        target_count=250,
        start_year=2010
    )
    # 체형 분석 수집 (목표: 200-300개)
    print("\n" + "=" * 60)
    print("📚 도메인 11: 기초대사량(BMR) + 에너지 처방 (목표: 250개)")
    print("=" * 60)

    body_comp_papers10 = collector.collect_domain(
        domain='body_composition',
        queries=BMR_NUTRITION_KR_QUERIES,
        target_count=250,
        start_year=2010
    )
    # 체형 분석 수집 (목표: 200-300개)
    print("\n" + "=" * 60)
    print("📚 도메인 12: 체성분과 대사증후군 (목표: 250개)")
    print("=" * 60)

    body_comp_papers11 = collector.collect_domain(
        domain='body_composition',
        queries=METABOLIC_RISK_KR_QUERIES,
        target_count=250,
        start_year=2010
    )



    # 전체 수집 결과
    all_papers = korean_diet_papers + body_comp_papers1 + body_comp_papers2 + body_comp_papers3 + body_comp_papers4 + body_comp_papers5 + body_comp_papers6 + body_comp_papers7 + body_comp_papers8 + body_comp_papers9 + body_comp_papers10 + body_comp_papers11


    # 결과 저장
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 전체 저장
    corpus_path = output_dir / f"kci_korean_{timestamp}.json"
    with open(corpus_path, "w", encoding="utf-8") as f:
        json.dump([p.model_dump() for p in all_papers], f, ensure_ascii=False, indent=2)

    print(f"\n✅ 저장 완료: {corpus_path}")

    # 도메인별 저장
    if korean_diet_papers:
        diet_path = output_dir / f"korean_diet_kci_{timestamp}.json"
        with open(diet_path, "w", encoding="utf-8") as f:
            json.dump([p.model_dump() for p in korean_diet_papers], f, ensure_ascii=False, indent=2)
        print(f"   - 한국 식단: {diet_path} ({len(korean_diet_papers)}개)")

    if body_comp_papers:
        body_path = output_dir / f"body_composition_kci_{timestamp}.json"
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
