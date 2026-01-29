"""
KCI API 검색 테스트

간단한 검색어로 실제 결과가 나오는지 확인
"""

import sys

# API 키 입력받기
if len(sys.argv) > 1:
    api_key = sys.argv[1]
else:
    api_key = input("KCI API 키를 입력하세요: ").strip()

if not api_key:
    print("❌ API 키가 필요합니다.")
    sys.exit(1)

from kci_api_collector import KCIAPICollector

# 수집기 초기화
collector = KCIAPICollector(api_key=api_key)

# 간단한 검색어로 테스트
test_queries = [
    "체성분",      # 매우 일반적
    "인바디",      # 구체적
    "근감소증",    # 전문 용어
    "내장지방",    # 일반적
    "BIA",        # 영문 약어
]

print("=" * 60)
print("🧪 KCI API 검색 테스트")
print("=" * 60)

results = {}

for query in test_queries:
    papers = collector.search_papers(
        query=query,
        max_results=10,  # 10개만 테스트
        start_year=2015   # 최근 논문만
    )

    results[query] = len(papers)

    if papers:
        print(f"\n✅ '{query}': {len(papers)}개 발견")
        # 첫 번째 논문 제목 출력
        if papers:
            print(f"   예시: {papers[0]['title'][:50]}...")
    else:
        print(f"\n❌ '{query}': 결과 없음")

print("\n" + "=" * 60)
print("📊 테스트 결과 요약")
print("=" * 60)

for query, count in results.items():
    status = "✅" if count > 0 else "❌"
    print(f"{status} '{query}': {count}개")

total = sum(results.values())
success_rate = (sum(1 for c in results.values() if c > 0) / len(results)) * 100

print(f"\n총 수집: {total}개")
print(f"성공률: {success_rate:.0f}%")

if success_rate < 50:
    print("\n⚠️ 성공률이 낮습니다!")
    print("   가능한 원인:")
    print("   1. API 키가 잘못되었거나 만료됨")
    print("   2. KCI API 엔드포인트 변경됨")
    print("   3. 네트워크 문제")
else:
    print(f"\n🎉 성공! 간단한 검색어를 사용하세요!")
    print(f"   예상 수집량: 각 검색어당 50-200개")
