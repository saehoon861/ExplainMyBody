"""
LLM 호출 성능 비교 테스트 - 종합 비교
3가지 방식을 모두 실행하고 결과를 비교합니다.
"""

import asyncio
import sys
from pathlib import Path

# 현재 디렉토리를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.llm.test_weekly_plan_async import test_async_parallel
from services.llm.test_weekly_plan_sync import test_sync_sequential
from services.llm.test_weekly_plan_single import test_single_combined


def print_header(title):
    """헤더 출력"""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80 + "\n")


async def run_all_tests():
    """모든 테스트 실행 및 비교"""
    print_header("🚀 LLM 호출 성능 비교 테스트 시작")
    print("📌 테스트 방식:")
    print("   1️⃣  Async 병렬 방식 (asyncio.gather) - 현재 구현")
    print("   2️⃣  Sync 순차 방식 (하나씩 순차 실행)")
    print("   3️⃣  Single Call 방식 (4개 프롬프트를 1개로 통합)")
    print("\n⚠️  각 테스트는 실제 OpenAI API를 호출하므로 비용이 발생할 수 있습니다.")
    print("⏱️  네트워크 상태에 따라 결과가 달라질 수 있습니다.")

    input("\n▶️  Enter를 눌러 테스트를 시작하세요...")

    results = {}

    # 1. Async 병렬 방식
    try:
        results['async'] = await test_async_parallel()
    except Exception as e:
        print(f"❌ Async 테스트 실패: {e}")
        results['async'] = None

    # 2. Sync 순차 방식
    try:
        results['sync'] = test_sync_sequential()
    except Exception as e:
        print(f"❌ Sync 테스트 실패: {e}")
        results['sync'] = None

    # 3. Single Call 방식
    try:
        results['single'] = test_single_combined()
    except Exception as e:
        print(f"❌ Single Call 테스트 실패: {e}")
        results['single'] = None

    # 결과 비교
    print_header("📊 성능 비교 결과")

    if all(results.values()):
        print("┌─────────────────────────┬──────────────┬──────────────┬──────────────┐")
        print("│ 방식                    │ 소요 시간    │ 상대 속도    │ 효율성       │")
        print("├─────────────────────────┼──────────────┼──────────────┼──────────────┤")

        fastest = min(results.values())

        async_time = results['async']
        async_speedup = async_time / fastest if fastest > 0 else 1
        print(f"│ 1️⃣  Async 병렬 (현재)    │ {async_time:>8.3f}초  │ {async_speedup:>8.2f}x   │ {'🏆 최고' if async_time == fastest else '     '} │")

        sync_time = results['sync']
        sync_speedup = sync_time / fastest if fastest > 0 else 1
        print(f"│ 2️⃣  Sync 순차           │ {sync_time:>8.3f}초  │ {sync_speedup:>8.2f}x   │ {'🏆 최고' if sync_time == fastest else '     '} │")

        single_time = results['single']
        single_speedup = single_time / fastest if fastest > 0 else 1
        print(f"│ 3️⃣  Single Call         │ {single_time:>8.3f}초  │ {single_speedup:>8.2f}x   │ {'🏆 최고' if single_time == fastest else '     '} │")

        print("└─────────────────────────┴──────────────┴──────────────┴──────────────┘")

        # 속도 향상률 계산
        if results['sync'] > results['async']:
            improvement = ((results['sync'] - results['async']) / results['sync']) * 100
            print(f"\n💡 Async 병렬 방식이 Sync 순차 방식보다 {improvement:.1f}% 빠릅니다.")

        if results['sync'] > results['single']:
            improvement = ((results['sync'] - results['single']) / results['sync']) * 100
            print(f"💡 Single Call 방식이 Sync 순차 방식보다 {improvement:.1f}% 빠릅니다.")

        if results['async'] < results['single']:
            improvement = ((results['single'] - results['async']) / results['single']) * 100
            print(f"💡 Async 병렬 방식이 Single Call 방식보다 {improvement:.1f}% 빠릅니다.")
        elif results['single'] < results['async']:
            improvement = ((results['async'] - results['single']) / results['async']) * 100
            print(f"💡 Single Call 방식이 Async 병렬 방식보다 {improvement:.1f}% 빠릅니다.")

        # 권장사항
        print("\n" + "="*80)
        print("📌 권장사항")
        print("="*80)

        if results['async'] == fastest:
            print("✅ Async 병렬 방식이 가장 빠릅니다.")
            print("   - 4개의 LLM 호출이 동시에 처리되어 대기 시간이 최소화됩니다.")
            print("   - 네트워크 I/O가 많은 작업에 최적화되어 있습니다.")
        elif results['single'] == fastest:
            print("✅ Single Call 방식이 가장 빠릅니다.")
            print("   - 단일 API 호출로 오버헤드가 줄어듭니다.")
            print("   - 하지만 프롬프트가 길어져 토큰 비용이 증가할 수 있습니다.")
            print("   - 또한 하나의 섹션이 잘못되면 전체를 재생성해야 합니다.")
        else:
            print("⚠️  Sync 순차 방식이 가장 빠릅니다. (예상 밖의 결과)")
            print("   - 네트워크 상태나 API 서버 부하에 따라 결과가 달라질 수 있습니다.")
            print("   - 일반적으로는 Async 병렬이나 Single Call이 더 빠릅니다.")

        print("\n💰 비용 고려사항:")
        print("   - Async 병렬: 4번의 API 호출, 개별 응답 토큰")
        print("   - Sync 순차: 4번의 API 호출, 개별 응답 토큰")
        print("   - Single Call: 1번의 API 호출, 하지만 프롬프트가 4배 길어져 입력 토큰 증가")
        print("   → 실제 비용은 토큰 사용량에 따라 결정됩니다.")

    else:
        print("❌ 일부 테스트가 실패하여 비교할 수 없습니다.")
        for method, time in results.items():
            status = f"{time:.3f}초" if time else "실패"
            print(f"   - {method}: {status}")

    print("\n" + "="*80)
    print("✅ 모든 테스트 완료")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
