#!/usr/bin/env python3
"""
RAG 코퍼스 수집 메인 파이프라인
4개 축 동등 분배: 단백질/근육, 감량, 한식, 체형
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List

from models import PaperMetadata, CollectionStats
from pubmed_collector import PubMedCollector
from kci_collector import KCICollector
import config


def collect_all_domains(
    email: str,
    api_key: str = None,
    output_dir: str = "outputs",
) -> List[PaperMetadata]:
    """
    모든 도메인 수집

    Args:
        email: PubMed API 이메일
        api_key: PubMed API Key (선택)
        output_dir: 출력 디렉토리

    Returns:
        전체 PaperMetadata 리스트
    """
    all_papers = []
    stats = CollectionStats()

    # PubMed Collector 초기화
    pubmed = PubMedCollector(email=email, api_key=api_key)

    # ========== 1. 단백질/근육 증가 ==========
    print("\n" + "=" * 80)
    print("1️⃣  단백질/근육 증가 도메인 수집")
    print("=" * 80)

    protein_papers = pubmed.collect_domain(
        domain="protein_hypertrophy",
        queries=config.PROTEIN_HYPERTROPHY_QUERIES,
        target_count=config.PROTEIN_HYPERTROPHY_TARGET,
        results_per_query=config.PUBMED_RESULTS_PER_QUERY,
    )
    all_papers.extend(protein_papers)
    stats.by_domain["protein_hypertrophy"] = len(protein_papers)

    # ========== 2. 체지방 감량/다이어트 ==========
    print("\n" + "=" * 80)
    print("2️⃣  체지방 감량/다이어트 도메인 수집")
    print("=" * 80)

    fatloss_papers = pubmed.collect_domain(
        domain="fat_loss",
        queries=config.FAT_LOSS_QUERIES,
        target_count=config.FAT_LOSS_TARGET,
        results_per_query=config.PUBMED_RESULTS_PER_QUERY,
    )
    all_papers.extend(fatloss_papers)
    stats.by_domain["fat_loss"] = len(fatloss_papers)

    # ========== 3. 한국형 식단/한식 (영어 논문만 PubMed에서) ==========
    print("\n" + "=" * 80)
    print("3️⃣  한국형 식단/한식 도메인 수집 (영어 논문)")
    print("=" * 80)

    korean_diet_papers_en = pubmed.collect_domain(
        domain="korean_diet",
        queries=config.KOREAN_DIET_QUERIES_EN,
        target_count=config.KOREAN_DIET_TARGET // 2,  # 절반만 영어
        results_per_query=config.PUBMED_RESULTS_PER_QUERY,
    )
    all_papers.extend(korean_diet_papers_en)

    # 한국어 논문은 수동 수집 (KCI)
    print("\n📌 한국어 논문은 수동 수집이 필요합니다.")
    print("   가이드: kci_collector.py 참고")
    stats.by_domain["korean_diet"] = len(korean_diet_papers_en)

    # ========== 4. 체형 분석/인바디 ==========
    print("\n" + "=" * 80)
    print("4️⃣  체형 분석/인바디 도메인 수집 (영어 논문)")
    print("=" * 80)

    body_comp_papers_en = pubmed.collect_domain(
        domain="body_composition",
        queries=config.BODY_COMPOSITION_QUERIES_EN,
        target_count=config.BODY_COMPOSITION_TARGET // 2,  # 절반만 영어
        results_per_query=config.PUBMED_RESULTS_PER_QUERY,
    )
    all_papers.extend(body_comp_papers_en)

    # 한국어 논문은 수동 수집 (KCI)
    print("\n📌 한국어 논문은 수동 수집이 필요합니다.")
    stats.by_domain["body_composition"] = len(body_comp_papers_en)

    # ========== 통계 ==========
    stats.total_collected = len(all_papers)
    stats.by_language = {"en": len([p for p in all_papers if p.language == "en"])}
    stats.by_source = {"PubMed": len(all_papers)}

    return all_papers, stats


def save_results(
    papers: List[PaperMetadata],
    stats: CollectionStats,
    output_dir: str = "outputs",
):
    """
    수집 결과 저장

    Args:
        papers: 논문 리스트
        stats: 통계
        output_dir: 출력 디렉토리
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 1. 전체 JSON 저장
    all_json_path = output_path / f"{config.OUTPUT_FILE_PREFIX}_{timestamp}.json"
    with open(all_json_path, "w", encoding="utf-8") as f:
        json.dump(
            [p.model_dump() for p in papers], f, ensure_ascii=False, indent=2
        )
    print(f"\n✅ 전체 JSON 저장: {all_json_path}")

    # 2. 도메인별 분할 저장
    for domain in stats.by_domain.keys():
        domain_papers = [p for p in papers if p.domain == domain]
        domain_path = output_path / f"{domain}_{timestamp}.json"
        with open(domain_path, "w", encoding="utf-8") as f:
            json.dump(
                [p.model_dump() for p in domain_papers],
                f,
                ensure_ascii=False,
                indent=2,
            )
        print(f"  - {domain}: {domain_path} ({len(domain_papers)}개)")

    # 3. 통계 저장
    stats_path = output_path / f"stats_{timestamp}.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats.model_dump(), f, ensure_ascii=False, indent=2)
    print(f"  - 통계: {stats_path}")

    # 4. 통계 출력
    print("\n" + "=" * 80)
    print("📊 수집 통계")
    print("=" * 80)
    print(f"총 수집: {stats.total_collected}개")
    print(f"\n도메인별:")
    for domain, count in stats.by_domain.items():
        print(f"  - {domain}: {count}개")
    print(f"\n언어별:")
    for lang, count in stats.by_language.items():
        print(f"  - {lang}: {count}개")


def main():
    parser = argparse.ArgumentParser(
        description="RAG 코퍼스 수집 파이프라인 (4개 축 동등 분배)"
    )

    parser.add_argument(
        "--email",
        type=str,
        required=True,
        help="PubMed API 이메일 (NCBI 요구사항)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="PubMed API Key (선택, 속도 향상)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs",
        help="출력 디렉토리 (기본: outputs)",
    )

    args = parser.parse_args()

    print("\n" + "=" * 80)
    print("🚀 RAG 코퍼스 수집 시작")
    print("=" * 80)
    print(f"이메일: {args.email}")
    print(f"API Key: {'있음' if args.api_key else '없음 (속도 제한 있음)'}")
    print(f"출력 디렉토리: {args.output_dir}")

    # 수집 실행
    papers, stats = collect_all_domains(
        email=args.email,
        api_key=args.api_key,
        output_dir=args.output_dir,
    )

    # 결과 저장
    save_results(papers, stats, output_dir=args.output_dir)

    print("\n" + "=" * 80)
    print("✅ 수집 완료!")
    print("=" * 80)

    # KCI 수동 수집 가이드
    kci = KCICollector()
    print("\n" + kci.create_manual_guide())

    # 템플릿 저장
    template_path = Path(args.output_dir) / "kci_template.json"
    kci.save_template(str(template_path))


if __name__ == "__main__":
    main()
