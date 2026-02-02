"""
Google Scholar 개선된 수집 테스트 스크립트

.fill() 메서드 추가 후 초록 길이 개선 확인
소량 테스트 (10개)로 Captcha 없이 안전하게 테스트
"""

import json
from pathlib import Path
from datetime import datetime
from google_scholar_korean_collector import GoogleScholarKoreanCollector

def test_improved_collection():
    """개선된 수집 테스트"""

    print("=" * 70)
    print("🧪 Google Scholar 개선 테스트 (.fill() 메서드 적용)")
    print("=" * 70)
    print()

    # 수집기 초기화 (Captcha 방지를 위해 rate_limit 15초)
    collector = GoogleScholarKoreanCollector(
        use_proxy=False,
        rate_limit=15.0
    )

    # 테스트 쿼리 (소량)
    test_queries = [
        "근감소증 한국인",
        "체성분 분석 인바디",
    ]

    print(f"📋 테스트 설정:")
    print(f"  - 검색어: {test_queries}")
    print(f"  - 목표 수집: 10개")
    print(f"  - Rate limit: 15초")
    print(f"  - 예상 시간: {10 * 15 / 60:.1f}분")
    print()

    # 수집 시작
    papers = collector.collect_domain(
        domain='body_composition',
        queries=test_queries,
        target_count=10,
        year_from=2010
    )

    # 결과 분석
    print()
    print("=" * 70)
    print("📊 수집 결과 분석")
    print("=" * 70)

    if not papers:
        print("❌ 수집된 논문 없음")
        return

    print(f"총 수집: {len(papers)}개")
    print()

    # 초록 길이 분석
    abstracts = [p.abstract for p in papers if p.abstract]
    abstract_lengths = [len(a) for a in abstracts]

    if abstract_lengths:
        print(f"✅ 초록 통계:")
        print(f"  - 초록 있음: {len(abstract_lengths)}개")
        print(f"  - 평균 길이: {sum(abstract_lengths)/len(abstract_lengths):.1f}자")
        print(f"  - 최소 길이: {min(abstract_lengths)}자")
        print(f"  - 최대 길이: {max(abstract_lengths)}자")
        print()

        # 개선 효과 계산
        avg_length = sum(abstract_lengths) / len(abstract_lengths)
        baseline = 135.6  # 이전 평균

        if avg_length > baseline:
            improvement = ((avg_length - baseline) / baseline) * 100
            print(f"🎉 개선 효과: +{improvement:.1f}% (기존 {baseline}자 → {avg_length:.1f}자)")
        else:
            print(f"⚠️  예상보다 짧음: {avg_length:.1f}자 (기존 {baseline}자)")

    # 샘플 출력
    print()
    print("=" * 70)
    print("📄 논문 샘플 (처음 3개)")
    print("=" * 70)

    for i, paper in enumerate(papers[:3], 1):
        print(f"\n논문 {i}:")
        print(f"  제목: {paper.title[:70]}")
        print(f"  연도: {paper.year}")
        print(f"  초록 길이: {len(paper.abstract)}자")
        print(f"  초록 미리보기: {paper.abstract[:150]}...")
        print("-" * 70)

    # 저장
    output_dir = Path("outputs/test")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"test_improved_{timestamp}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            [p.model_dump() for p in papers],
            f,
            ensure_ascii=False,
            indent=2
        )

    print()
    print(f"💾 결과 저장: {output_file}")
    print()

    # 다음 단계 안내
    print("=" * 70)
    print("✅ 테스트 완료!")
    print("=" * 70)
    print()
    print("📋 다음 단계:")
    print()

    if avg_length > 300:
        print("  ✅ 초록 길이 우수! 본격 수집 가능")
        print()
        print("  본격 수집 실행:")
        print("    python google_scholar_korean_collector.py")
    elif avg_length > 200:
        print("  ⚠️  초록 길이 보통 (200-300자)")
        print()
        print("  옵션:")
        print("    1. 이대로 본격 수집 진행")
        print("    2. KCI/RISS API로 전환 검토")
    else:
        print("  ❌ 초록 길이 여전히 짧음 (<200자)")
        print()
        print("  권장 조치:")
        print("    1. scholarly 라이브러리 업데이트 확인")
        print("    2. KCI/RISS API 사용 검토")
        print("    3. LLM 초록 보강 검토")

    print()
    print("  Captcha 대응 가이드:")
    print("    cat CAPTCHA_HANDLING_GUIDE.md")
    print()


if __name__ == "__main__":
    try:
        test_improved_collection()
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 중단됨")
    except Exception as e:
        print(f"\n\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
