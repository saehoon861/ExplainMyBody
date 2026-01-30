"""
한국어 코퍼스 병합 스크립트

여러 소스에서 수집한 한국어 논문을 하나로 병합하고
기존 PubMed 영어 논문과 통합합니다.
"""

import json
from typing import List, Dict
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher

from models import PaperMetadata, CollectionStats


class KoreanCorpusMerger:
    """한국어 코퍼스 병합기"""

    def __init__(self, similarity_threshold: float = 0.85):
        """
        Args:
            similarity_threshold: 제목 유사도 임계값 (이상이면 중복으로 간주)
        """
        self.similarity_threshold = similarity_threshold

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """두 텍스트의 유사도 계산 (0.0 ~ 1.0)"""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def is_duplicate(self, paper: PaperMetadata, existing_papers: List[PaperMetadata]) -> bool:
        """
        기존 논문 리스트에서 중복 여부 확인

        Args:
            paper: 확인할 논문
            existing_papers: 기존 논문 리스트

        Returns:
            중복이면 True
        """
        for existing in existing_papers:
            # PMID가 있고 같으면 중복
            if paper.pmid and existing.pmid and paper.pmid == existing.pmid:
                return True

            # DOI가 있고 같으면 중복
            if paper.doi and existing.doi and paper.doi == existing.doi:
                return True

            # 제목 유사도로 중복 검사
            similarity = self.calculate_similarity(paper.title, existing.title)
            if similarity >= self.similarity_threshold:
                return True

        return False

    def merge_papers(
        self,
        paper_lists: List[List[PaperMetadata]],
        source_names: List[str]
    ) -> tuple[List[PaperMetadata], Dict]:
        """
        여러 소스의 논문을 병합하고 중복 제거

        Args:
            paper_lists: 소스별 논문 리스트들
            source_names: 각 리스트의 소스명

        Returns:
            (병합된 논문 리스트, 통계 딕셔너리)
        """
        merged = []
        stats = {
            'total_input': 0,
            'total_output': 0,
            'duplicates_removed': 0,
            'by_source': {}
        }

        for papers, source_name in zip(paper_lists, source_names):
            stats['total_input'] += len(papers)
            added_count = 0

            print(f"\n📊 처리 중: {source_name} ({len(papers)}개)")

            for paper in papers:
                if not self.is_duplicate(paper, merged):
                    merged.append(paper)
                    added_count += 1
                else:
                    stats['duplicates_removed'] += 1

            stats['by_source'][source_name] = {
                'input': len(papers),
                'added': added_count,
                'duplicates': len(papers) - added_count
            }

            print(f"  ✅ {added_count}개 추가 (중복 {len(papers) - added_count}개 제거)")

        stats['total_output'] = len(merged)

        return merged, stats

    def load_json_file(self, json_path: str) -> List[PaperMetadata]:
        """JSON 파일에서 PaperMetadata 리스트 로드"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            papers = [PaperMetadata(**item) for item in data]
            print(f"  📥 로드 완료: {json_path} ({len(papers)}개)")
            return papers

        except Exception as e:
            print(f"  ❌ 로드 실패 {json_path}: {e}")
            return []

    def create_final_stats(self, papers: List[PaperMetadata]) -> CollectionStats:
        """최종 통계 생성"""

        stats = CollectionStats()
        stats.total_collected = len(papers)

        for paper in papers:
            # 도메인별
            stats.by_domain[paper.domain] = stats.by_domain.get(paper.domain, 0) + 1

            # 언어별
            stats.by_language[paper.language] = stats.by_language.get(paper.language, 0) + 1

            # 소스별
            stats.by_source[paper.source] = stats.by_source.get(paper.source, 0) + 1

        return stats


def main():
    """메인 실행 함수"""

    print("=" * 60)
    print("🔀 한국어 코퍼스 병합 시작")
    print("=" * 60)

    merger = KoreanCorpusMerger(similarity_threshold=0.85)

    # outputs 폴더에서 수집된 파일들 찾기
    output_dir = Path("outputs")

    if not output_dir.exists():
        print(f"\n❌ outputs 폴더가 없습니다: {output_dir}")
        return

    # 1. 기존 PubMed 영어 논문 로드
    print("\n" + "=" * 60)
    print("1️⃣ PubMed 영어 논문 로드")
    print("=" * 60)

    # 여러 패턴의 PubMed 파일들 수집
    pubmed_files = (
        list(output_dir.glob("ragdb_corpus_*.json")) +
        list(output_dir.glob("body_composition_*.json")) +
        list(output_dir.glob("fat_loss_*.json")) +
        list(output_dir.glob("protein_hypertrophy_*.json"))
    )
    pubmed_papers = []

    if pubmed_files:
        print(f"  📁 발견된 PubMed 파일: {len(pubmed_files)}개")
        
        # 모든 파일 로드 (중복 제거는 나중에 병합 단계에서)
        for pubmed_file in pubmed_files:
            papers = merger.load_json_file(str(pubmed_file))
            pubmed_papers.extend(papers)
        
        print(f"✅ PubMed 논문 총합: {len(pubmed_papers)}개")
    else:
        print("⚠️ PubMed 코퍼스 파일이 없습니다.")
        print("   먼저 main.py를 실행하여 PubMed 논문을 수집하세요.")

    # 2. Google Scholar 한국어 논문 로드
    print("\n" + "=" * 60)
    print("2️⃣ Google Scholar 한국어 논문 로드")
    print("=" * 60)

    # stats 파일 제외하고 논문 데이터만 로드
    all_scholar_files = list(output_dir.glob("google_scholar_*.json"))
    scholar_files = [f for f in all_scholar_files if "stats" not in f.name]
    scholar_papers = []

    if scholar_files:
        print(f"  📁 발견된 Google Scholar 파일: {len(scholar_files)}개")
        
        # 모든 논문 파일 로드
        for scholar_file in scholar_files:
            papers = merger.load_json_file(str(scholar_file))
            scholar_papers.extend(papers)
        
        print(f"✅ Google Scholar 총합: {len(scholar_papers)}개")
    else:
        print("⚠️ Google Scholar 파일이 없습니다.")

    # 3. 정부 보고서 로드
    print("\n" + "=" * 60)
    print("3️⃣ 정부 보고서 로드")
    print("=" * 60)

    # stats 파일 제외
    all_gov_files = list(output_dir.glob("government_reports_*.json"))
    gov_files = [f for f in all_gov_files if "stats" not in f.name]
    gov_papers = []

    if gov_files:
        print(f"  📁 발견된 정부 보고서 파일: {len(gov_files)}개")
        
        for gov_file in gov_files:
            papers = merger.load_json_file(str(gov_file))
            gov_papers.extend(papers)
        
        print(f"✅ 정부 보고서 총합: {len(gov_papers)}개")
    else:
        print("⚠️ 정부 보고서 파일이 없습니다.")

    # 4. 학술지 논문 로드
    print("\n" + "=" * 60)
    print("4️⃣ 학술지 논문 로드")
    print("=" * 60)

    # stats 파일 제외
    all_society_files = list(output_dir.glob("society_papers_*.json"))
    society_files = [f for f in all_society_files if "stats" not in f.name]
    society_papers = []

    if society_files:
        print(f"  📁 발견된 학술지 파일: {len(society_files)}개")
        
        for society_file in society_files:
            papers = merger.load_json_file(str(society_file))
            society_papers.extend(papers)
        
        print(f"✅ 학술지 총합: {len(society_papers)}개")
    else:
        print("⚠️ 학술지 파일이 없습니다.")

    # 5. KCI API 논문 로드
    print("\n" + "=" * 60)
    print("5️⃣ KCI API 한국어 논문 로드")
    print("=" * 60)

    # stats 파일 제외
    all_kci_files = list(output_dir.glob("kci_korean_*.json"))
    kci_files = [f for f in all_kci_files if "stats" not in f.name]
    kci_papers = []

    if kci_files:
        print(f"  📁 발견된 KCI 파일: {len(kci_files)}개")
        
        for kci_file in kci_files:
            papers = merger.load_json_file(str(kci_file))
            kci_papers.extend(papers)
        
        print(f"✅ KCI API 총합: {len(kci_papers)}개")
    else:
        print("⚠️ KCI API 파일이 없습니다.")

    # 6. RISS API 논문 로드
    print("\n" + "=" * 60)
    print("6️⃣ RISS API 한국어 논문 로드")
    print("=" * 60)

    # stats 파일 제외
    all_riss_files = list(output_dir.glob("riss_korean_*.json"))
    riss_files = [f for f in all_riss_files if "stats" not in f.name]
    riss_papers = []

    if riss_files:
        print(f"  📁 발견된 RISS 파일: {len(riss_files)}개")
        
        for riss_file in riss_files:
            papers = merger.load_json_file(str(riss_file))
            riss_papers.extend(papers)
        
        print(f"✅ RISS API 총합: {len(riss_papers)}개")
    else:
        print("⚠️ RISS API 파일이 없습니다.")

    # 7. ScienceON API 논문 로드
    print("\n" + "=" * 60)
    print("7️⃣ ScienceON API 한국어 논문 로드")
    print("=" * 60)

    # stats 파일 제외
    all_scienceon_files = list(output_dir.glob("scienceon_korean_*.json"))
    scienceon_files = [f for f in all_scienceon_files if "stats" not in f.name]
    scienceon_papers = []

    if scienceon_files:
        print(f"  📁 발견된 ScienceON 파일: {len(scienceon_files)}개")
        
        for scienceon_file in scienceon_files:
            papers = merger.load_json_file(str(scienceon_file))
            scienceon_papers.extend(papers)
        
        print(f"✅ ScienceON API 총합: {len(scienceon_papers)}개")
    else:
        print("⚠️ ScienceON API 파일이 없습니다.")

    # 8. 병합
    print("\n" + "=" * 60)
    print("8️⃣ 전체 병합 및 중복 제거")
    print("=" * 60)

    all_paper_lists = []
    source_names = []

    if pubmed_papers:
        all_paper_lists.append(pubmed_papers)
        source_names.append("PubMed (영어)")

    if scholar_papers:
        all_paper_lists.append(scholar_papers)
        source_names.append("Google Scholar (한국어)")

    if gov_papers:
        all_paper_lists.append(gov_papers)
        source_names.append("정부 보고서")

    if society_papers:
        all_paper_lists.append(society_papers)
        source_names.append("학술지")

    if kci_papers:
        all_paper_lists.append(kci_papers)
        source_names.append("KCI API")

    if riss_papers:
        all_paper_lists.append(riss_papers)
        source_names.append("RISS API")

    if scienceon_papers:
        all_paper_lists.append(scienceon_papers)
        source_names.append("ScienceON API")

    if not all_paper_lists:
        print("❌ 병합할 파일이 없습니다.")
        print("   먼저 수집 스크립트를 실행하세요:")
        print("   - python main.py (PubMed)")
        print("   - python kci_api_collector.py (KCI API)")
        print("   - python riss_api_collector.py (RISS API)")
        print("   - python scienceon_api_collector.py (ScienceON API)")
        print("   - python google_scholar_korean_collector.py (Google Scholar)")
        print("   - python government_report_parser.py --process (정부 보고서)")
        print("   - python society_csv_parser.py --process [파일] (학술지)")
        return

    merged_papers, merge_stats = merger.merge_papers(all_paper_lists, source_names)

    # 9. 최종 통계
    print("\n" + "=" * 60)
    print("9️⃣ 최종 통계 생성")
    print("=" * 60)

    final_stats = merger.create_final_stats(merged_papers)

    print(f"\n📊 도메인별 분포:")
    for domain, count in final_stats.by_domain.items():
        print(f"  - {domain}: {count}개")

    print(f"\n🌍 언어별 분포:")
    for lang, count in final_stats.by_language.items():
        lang_name = "한국어" if lang == "ko" else "영어"
        print(f"  - {lang_name} ({lang}): {count}개")

    print(f"\n📚 소스별 분포:")
    for source, count in final_stats.by_source.items():
        print(f"  - {source}: {count}개")

    # 10. 저장
    print("\n" + "=" * 60)
    print("🔟 최종 코퍼스 저장")
    print("=" * 60)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 전체 코퍼스 저장
    final_corpus_path = output_dir / f"ragdb_final_corpus_{timestamp}.json"
    with open(final_corpus_path, 'w', encoding='utf-8') as f:
        json.dump([p.model_dump() for p in merged_papers], f, ensure_ascii=False, indent=2)

    print(f"✅ 최종 코퍼스: {final_corpus_path}")
    print(f"   총 {len(merged_papers)}개 논문")

    # 통계 저장
    stats_path = output_dir / f"ragdb_final_stats_{timestamp}.json"
    with open(stats_path, 'w', encoding='utf-8') as f:
        stats_data = {
            'collection_stats': final_stats.model_dump(),
            'merge_stats': merge_stats
        }
        json.dump(stats_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 통계: {stats_path}")

    # 도메인별 분할 저장
    print("\n📂 도메인별 분할 저장:")
    for domain in final_stats.by_domain.keys():
        domain_papers = [p for p in merged_papers if p.domain == domain]
        domain_path = output_dir / f"{domain}_final_{timestamp}.json"

        with open(domain_path, 'w', encoding='utf-8') as f:
            json.dump([p.model_dump() for p in domain_papers], f, ensure_ascii=False, indent=2)

        print(f"  ✅ {domain}: {domain_path} ({len(domain_papers)}개)")

    # 최종 요약
    print("\n" + "=" * 60)
    print("✅ 병합 완료!")
    print("=" * 60)
    print(f"\n📊 최종 결과:")
    print(f"  입력: {merge_stats['total_input']}개")
    print(f"  중복 제거: {merge_stats['duplicates_removed']}개")
    print(f"  출력: {merge_stats['total_output']}개")
    print(f"\n🎯 목표 대비 달성률:")

    targets = {
        'protein_hypertrophy': 800,
        'fat_loss': 800,
        'korean_diet': 600,
        'body_composition': 800
    }

    total_target = sum(targets.values())
    current = len(merged_papers)
    progress = (current / total_target) * 100

    for domain, target in targets.items():
        actual = final_stats.by_domain.get(domain, 0)
        domain_progress = (actual / target) * 100
        status = "✅" if actual >= target else "📈"
        print(f"  {status} {domain}: {actual}/{target} ({domain_progress:.1f}%)")

    print(f"\n  총합: {current}/{total_target} ({progress:.1f}%)")

    if progress >= 100:
        print("\n🎉 목표 달성! 3000개 코퍼스 완성!")
    else:
        remaining = total_target - current
        print(f"\n📌 추가 필요: {remaining}개")

        # 부족한 도메인 안내
        for domain, target in targets.items():
            actual = final_stats.by_domain.get(domain, 0)
            if actual < target:
                shortage = target - actual
                print(f"   - {domain}: {shortage}개 부족")


if __name__ == "__main__":
    main()
