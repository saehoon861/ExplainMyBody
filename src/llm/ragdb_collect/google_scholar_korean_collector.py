"""
Google Scholar 한국어 논문 자동 수집기

scholarly 라이브러리를 사용하여 Google Scholar에서 한국어 논문을 자동 수집합니다.
"""

import time
import json
from typing import List, Optional
from datetime import datetime
from pathlib import Path

try:
    from scholarly import scholarly, ProxyGenerator
except ImportError:
    print("❌ scholarly 라이브러리가 필요합니다: pip install scholarly")
    exit(1)

from models import PaperMetadata, CollectionStats


class GoogleScholarKoreanCollector:
    """Google Scholar 한국어 논문 수집기"""

    def __init__(self, use_proxy: bool = True, rate_limit: float = 15.0):
        """
        Args:
            use_proxy: 프록시 사용 여부 (rate limit 회피용, 선택사항)
            rate_limit: 요청 간 대기 시간 (초) - Captcha 방지를 위해 12-15초 권장
        """
        self.rate_limit = rate_limit

        if use_proxy:
            try:
                pg = ProxyGenerator()
                pg.FreeProxies()
                scholarly.use_proxy(pg)
                print("✅ 프록시 설정 완료")
            except Exception as e:
                print(f"⚠️ 프록시 설정 실패 (직접 연결 사용): {e}")

    def search_korean_papers(
        self,
        query: str,
        domain: str,
        max_results: int = 50,
        year_from: Optional[int] = None
    ) -> List[PaperMetadata]:
        """
        Google Scholar에서 한국어 논문 검색

        Args:
            query: 검색어 (한국어)
            domain: 도메인 분류 (korean_diet, body_composition)
            max_results: 최대 수집 개수
            year_from: 시작 연도 (None이면 제한 없음)

        Returns:
            PaperMetadata 리스트
        """
        papers = []

        print(f"\n🔍 검색 중: '{query}' (최대 {max_results}개)")

        # Google Scholar 검색 쿼리 구성
        search_query = query
        if year_from:
            search_query = f"{query} after:{year_from}"

        try:
            search_results = scholarly.search_pubs(search_query)

            collected = 0
            for result in search_results:
                if collected >= max_results:
                    break

                try:
                    # ✨ 전체 논문 정보 가져오기 (초록 포함)
                    print(f"  🔄 논문 상세 정보 가져오는 중...", end='', flush=True)

                    try:
                        filled_result = scholarly.fill(result)
                        print(" ✅")
                    except Exception as fill_error:
                        # Captcha 또는 차단 감지
                        error_msg = str(fill_error).lower()
                        if 'captcha' in error_msg or 'blocked' in error_msg or 'unusual traffic' in error_msg:
                            print(f"\n\n⚠️  CAPTCHA 감지됨!")
                            print("=" * 60)
                            print("Google Scholar에서 자동화 탐지로 차단했습니다.")
                            print("다음 중 하나를 선택하세요:")
                            print("  1. 브라우저에서 https://scholar.google.com 접속 후 Captcha 풀기")
                            print("  2. 10-15분 대기 후 재시도")
                            print("  3. 프록시 사용 (--use-proxy 옵션)")
                            print("  4. 현재까지 수집된 데이터로 진행 (Enter)")
                            print("=" * 60)

                            user_choice = input("\n계속 진행하시겠습니까? (y/n): ").strip().lower()
                            if user_choice != 'y':
                                print(f"중단됨. 현재까지 수집: {len(papers)}개")
                                return papers
                            else:
                                print("재시도 중...")
                                time.sleep(15)  # 15초 대기 후 재시도
                                continue
                        else:
                            # 다른 에러는 스킵
                            print(f" ❌ ({fill_error})")
                            continue

                    # 논문 정보 추출
                    paper = self._parse_scholar_result(filled_result, domain)

                    # 초록이 있는 논문만 수집
                    if paper and paper.abstract and len(paper.abstract) >= 100:
                        papers.append(paper)
                        collected += 1
                        print(f"  ✅ [{collected}/{max_results}] {paper.title[:50]}... (초록: {len(paper.abstract)}자)")

                    # Rate limiting (Captcha 방지를 위해 증가)
                    time.sleep(self.rate_limit)

                except Exception as e:
                    print(f"  ⚠️ 논문 파싱 실패: {e}")
                    continue

            print(f"✅ '{query}': {len(papers)}개 수집 완료")

        except Exception as e:
            print(f"❌ 검색 실패 '{query}': {e}")

        return papers

    def _parse_scholar_result(self, result: dict, domain: str) -> Optional[PaperMetadata]:
        """Google Scholar 검색 결과를 PaperMetadata로 변환"""

        try:
            # 제목 추출
            title = result.get('bib', {}).get('title', '')
            if not title:
                return None

            # 초록 추출 (있는 경우)
            abstract = result.get('bib', {}).get('abstract', '')

            # 연도 추출
            year_str = result.get('bib', {}).get('pub_year', '')
            year = int(year_str) if year_str and year_str.isdigit() else None

            # 저자 추출
            authors_raw = result.get('bib', {}).get('author', [])
            if isinstance(authors_raw, str):
                authors = [authors_raw]
            elif isinstance(authors_raw, list):
                authors = authors_raw[:5]  # 최대 5명
            else:
                authors = []

            # 저널 추출
            journal = result.get('bib', {}).get('venue', '') or \
                     result.get('bib', {}).get('journal', '')

            # Metadata 생성
            paper = PaperMetadata(
                domain=domain,
                language='ko',
                title=title,
                abstract=abstract,
                keywords=[],  # Google Scholar는 키워드 제공 안함
                source='Google Scholar',
                year=year,
                pmid=None,
                doi=None,
                authors=authors,
                journal=journal
            )

            return paper

        except Exception as e:
            print(f"  ⚠️ 파싱 오류: {e}")
            return None

    def collect_domain(
        self,
        domain: str,
        queries: List[str],
        target_count: int,
        year_from: int = 2010
    ) -> List[PaperMetadata]:
        """
        특정 도메인의 논문 수집

        Args:
            domain: 도메인 분류
            queries: 검색어 리스트
            target_count: 목표 수집 개수
            year_from: 시작 연도

        Returns:
            PaperMetadata 리스트 (중복 제거됨)
        """
        all_papers = []
        seen_titles = set()  # 제목 기반 중복 제거

        results_per_query = max(10, target_count // len(queries))

        for query in queries:
            papers = self.search_korean_papers(
                query=query,
                domain=domain,
                max_results=results_per_query,
                year_from=year_from
            )

            # 중복 제거
            for paper in papers:
                title_normalized = paper.title.lower().strip()
                if title_normalized not in seen_titles:
                    seen_titles.add(title_normalized)
                    all_papers.append(paper)

            # 목표 달성 확인
            if len(all_papers) >= target_count:
                break

            # 쿼리 간 대기
            time.sleep(5)

        return all_papers[:target_count]


def main():
    """메인 실행 함수"""

    # 한국어 논문 검색어 (config.py에서 가져올 수도 있음)
    KOREAN_DIET_QUERIES = [
        "한국 식단 영양",
         ]

        # "한식 식사패턴 건강",
        # "김치 섭취 효과",
        # "한국인 단백질 섭취",
        # "전통 발효식품 건강",
        # "된장 건강 효과",
        # "한국형 식생활 지침",
        # "국민건강영양조사 식이섭취",
   
    BODY_COMPOSITION_QUERIES = [
     "체지방률 및 골격근량 지수(SMI) 기반의 체형 분류 모델"
    "체형부위별 근육 불균형(Segmental Lean Analysis)과 신체 기능의 상관관계"
    "상·하체 근육량 비율에 따른 근감소성 비만(Sarcopenic Obesity) 판정 기준"
    "InBody 데이터를 활용한 체형 지수(Body Shape Index) 산출 로직"
    "복부지방률(WHR) 및 내장지방레벨에 따른 고강도 인터벌 트레이닝(HIIT)의 효과"
    "좌우측 상하지 근육 불균형 교정을 위한 편측성 운동(Unilateral Exercise) 처방"
    "신체 부위별 체지방 분포와 인슐린 저항성 간의 관계"
    "무기질 및 단백질 섭취 상태와 근력 운동 효율의 상관성"
        
    ]

        # "근감소증 한국인",
        # "체성분 분석 인바디",
        # "골격근량 평가",
        # "체지방률 기준",
        # "노인 근육량",
        # "생체전기저항 분석",

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
    
    # VISCERAL_FAT_KR_QUERIES = [
    # "내장지방 수준 대사증후군 위험",
    # "복부비만 내장지방 체성분 분석",
    # "내장지방면적과 인슐린저항성",
    # "중심성비만 건강위험 연구",
    # "생체전기저항분석 내장지방 추정",
    # ]

    # SEGMENTAL_BALANCE_KR_QUERIES = [
    # "부위별 골격근량 불균형 분석",
    # "사지 근육량 좌우 차이",
    # "팔 다리 근육 비대칭 체성분",
    # "부위별 체지방 분포 연구",
    # "국소 체성분 불균형 운동처방",
    # ]

    # EXERCISE_INTERVENTION_KR_QUERIES = [
    # "저항운동 골격근량 증가 체성분 변화",
    # "유산소운동 내장지방 감소 효과",
    # "복합운동 체지방률 개선 연구",
    # "운동중재 체성분 개선 프로그램",
    # "운동처방 기반 체성분 분석",
    # ]

    # MUSCLE_ADJUSTMENT_KR_QUERIES = [
    # "근육량 증가 프로그램 효과",
    # "단백질 섭취와 근육량 변화",
    # "근감소 예방 저항성운동 처방",
    # "제지방량 증가 중재연구",
    # ]

    # BMR_NUTRITION_KR_QUERIES = [
    # "기초대사량과 제지방량 관계",
    # "체성분 기반 에너지 필요량 추정",
    # "권장섭취열량 산정 체성분 연구",
    # "체중조절 프로그램 대사량 변화",
    # ]

    # METABOLIC_RISK_KR_QUERIES = [
    # "체성분과 대사증후군 위험",
    # "골격근량과 당뇨병 위험",
    # "내장지방과 심혈관질환 연관",
    # "체성분 지표 건강예측모델",
    # ]




    # 수집기 초기화 (Captcha 방지를 위해 rate_limit 15초)
    collector = GoogleScholarKoreanCollector(use_proxy=False, rate_limit=15.0)

    # 한국 식단 수집 (목표: 200-300개)
    print("\n" + "=" * 60)
    print("📚 도메인 1: 한국형 식단/한식 (목표: 250개)")
    print("=" * 60)

    korean_diet_papers = collector.collect_domain(
        domain='korean_diet',
        queries=KOREAN_DIET_QUERIES,
        target_count=2,
        year_from=2010
    )

    # 체형 분석 수집 (목표: 200-300개)
    print("\n" + "=" * 60)
    print("📚 도메인 2: 체형 분석/인바디 (목표: 500개)")
    print("=" * 60)

    body_comp_papers1 = collector.collect_domain(
        domain='body_composition',
        queries=BODY_COMPOSITION_QUERIES,
        target_count=100,
        year_from=2010
    )
    # 체형 분석 수집 (목표: 200-300개)
    print("\n" + "=" * 60)
    print("📚 도메인 3: 인바디/체성분 분석 핵심 키워드 (목표: 250개)")
    print("=" * 60)

    body_comp_papers2 = collector.collect_domain(
        domain='body_composition',
        queries=INBODY_BIA_KR_QUERIES,
        target_count=100,
        year_from=2010
    )
    # 체형 분석 수집 (목표: 200-300개)
    print("\n" + "=" * 60)
    print("📚 도메인 4: 체형분석/체성분 기반 유형화 (목표: 250개)")
    print("=" * 60)

    body_comp_papers3 = collector.collect_domain(
        domain='body_composition',
        queries=BODY_TYPE_CLASSIFICATION_KR_QUERIES,
        target_count=100,
        year_from=2010
    )
    # 체형 분석 수집 (목표: 200-300개)
    print("\n" + "=" * 60)
    print("📚 도메인 5: 근감소증 + 근감소성비만 (목표: 250개)")
    print("=" * 60)

    body_comp_papers4 = collector.collect_domain(
        domain='body_composition',
        queries=SARCOPENIA_KR_QUERIES,
        target_count=100,
        year_from=2010
    )
    # 체형 분석 수집 (목표: 200-300개)
    print("\n" + "=" * 60)
    print("📚 도메인 6: 체지방률·비만도·BMI 한계 (목표: 250개)")
    print("=" * 60)

    body_comp_papers5 = collector.collect_domain(
        domain='body_composition',
        queries=BODYFAT_OBESITY_KR_QUERIES,
        target_count=100,
        year_from=2010
    )
    # # 체형 분석 수집 (목표: 200-300개)
    # print("\n" + "=" * 60)
    # print("📚 도메인 7: 복부지방률·내장지방 레벨 (목표: 250개)")
    # print("=" * 60)

    # body_comp_papers6 = collector.collect_domain(
    #     domain='body_composition',
    #     queries=VISCERAL_FAT_KR_QUERIES,
    #     target_count=100,
    #     year_from=2010
    # )
    # # 체형 분석 수집 (목표: 200-300개)
    # print("\n" + "=" * 60)
    # print("📚 도메인 8: 부위별 근육/지방 불균형 (Segmental) (목표: 250개)")
    # print("=" * 60)

    # body_comp_papers7 = collector.collect_domain(
    #     domain='body_composition',
    #     queries=SEGMENTAL_BALANCE_KR_QUERIES,
    #     target_count=100,
    #     year_from=2010
    # )
    # # 체형 분석 수집 (목표: 200-300개)
    # print("\n" + "=" * 60)
    # print("📚 도메인 9: 운동처방 근거 (근육 증가/지방 감소) (목표: 250개)")
    # print("=" * 60)

    # body_comp_papers8 = collector.collect_domain(
    #     domain='body_composition',
    #     queries=EXERCISE_INTERVENTION_KR_QUERIES,
    #     target_count=100,
    #     year_from=2010
    # )
    # # 체형 분석 수집 (목표: 200-300개)
    # print("\n" + "=" * 60)
    # print("📚 도메인 10: 기초대사량(BMR) + 에너지 처방 (목표: 250개)")
    # print("=" * 60)

    # body_comp_papers9 = collector.collect_domain(
    #     domain='body_composition',
    #     queries=MUSCLE_ADJUSTMENT_KR_QUERIES,
    #     target_count=100,
    #     year_from=2010
    # )
    # # 체형 분석 수집 (목표: 200-300개)
    # print("\n" + "=" * 60)
    # print("📚 도메인 11: 기초대사량(BMR) + 에너지 처방 (목표: 250개)")
    # print("=" * 60)

    # body_comp_papers10 = collector.collect_domain(
    #     domain='body_composition',
    #     queries=BMR_NUTRITION_KR_QUERIES,
    #     target_count=100,
    #     year_from=2010
    # )
    # # 체형 분석 수집 (목표: 200-300개)
    # print("\n" + "=" * 60)
    # print("📚 도메인 12: 체성분과 대사증후군 (목표: 250개)")
    # print("=" * 60)

    # body_comp_papers11 = collector.collect_domain(
    #     domain='body_composition',
    #     queries=METABOLIC_RISK_KR_QUERIES,
    #     target_count=100,
    #     year_from=2010
    # )


    # 전체 수집 결과
    all_papers = korean_diet_papers + body_comp_papers1 + body_comp_papers2 + body_comp_papers3 + body_comp_papers4 + body_comp_papers5 + body_comp_papers6 + body_comp_papers7 + body_comp_papers8 + body_comp_papers9 + body_comp_papers10 + body_comp_papers11


    # 통계 생성
    stats = CollectionStats(
        total_collected=len(all_papers),
        by_domain={
            'korean_diet': len(korean_diet_papers),
            'body_composition': len(body_comp_papers)
        },
        by_language={'ko': len(all_papers)},
        by_source={'Google Scholar': len(all_papers)},
        failed_count=0
    )

    # 결과 저장
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 전체 저장
    corpus_path = output_dir / f"google_scholar_korean_{timestamp}.json"
    with open(corpus_path, "w", encoding="utf-8") as f:
        json.dump([p.model_dump() for p in all_papers], f, ensure_ascii=False, indent=2)

    print(f"\n✅ 저장 완료: {corpus_path}")

    # 도메인별 분할 저장
    if korean_diet_papers:
        diet_path = output_dir / f"korean_diet_scholar_{timestamp}.json"
        with open(diet_path, "w", encoding="utf-8") as f:
            json.dump([p.model_dump() for p in korean_diet_papers], f, ensure_ascii=False, indent=2)
        print(f"   - 한국 식단: {diet_path}")

    if body_comp_papers:
        body_path = output_dir / f"body_composition_scholar_{timestamp}.json"
        with open(body_path, "w", encoding="utf-8") as f:
            json.dump([p.model_dump() for p in body_comp_papers], f, ensure_ascii=False, indent=2)
        print(f"   - 체형 분석: {body_path}")

    # 통계 저장
    stats_path = output_dir / f"google_scholar_stats_{timestamp}.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats.model_dump(), f, ensure_ascii=False, indent=2)

    print(f"   - 통계: {stats_path}")

    # 최종 통계 출력
    print("\n" + "=" * 60)
    print("📊 수집 완료 통계")
    print("=" * 60)
    print(f"총 수집: {stats.total_collected}개")
    print(f"  - 한국 식단: {stats.by_domain['korean_diet']}개")
    print(f"  - 체형 분석: {stats.by_domain['body_composition']}개")
    print("=" * 60)


if __name__ == "__main__":
    main()
