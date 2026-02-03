"""
InBody 분석 테스트 (2단계 프롬프트)
- Prompt 1: 5줄 요약
- Prompt 2: 세부 리포트
"""

import asyncio
from datetime import datetime

from sample_data import SAMPLE_MEASUREMENTS, SAMPLE_USER
from schemas import StatusAnalysisInput
from llm_clients import create_llm_client
from agent_graph_rag import create_analysis_agent_with_rag


async def test_two_step_analysis():
    """InBody 분석 테스트 (2단계)"""

    print("=" * 60)
    print("InBody 2단계 분석 테스트")
    print("=" * 60)

    # 1. 입력 데이터 준비
    analysis_input = StatusAnalysisInput(
        record_id=SAMPLE_USER["record_id"],
        user_id=SAMPLE_USER["user_id"],
        measured_at=SAMPLE_USER["measured_at"],
        measurements=SAMPLE_MEASUREMENTS,
        body_type1=SAMPLE_USER["body_type1"],
        body_type2=SAMPLE_USER["body_type2"]
    )

    print("\n[1] 입력 데이터")
    print(f"  User ID: {analysis_input.user_id}")
    print(f"  체중: {SAMPLE_MEASUREMENTS['체중관리']['체중']}kg")
    print(f"  체지방률: {SAMPLE_MEASUREMENTS['비만분석']['체지방률']}%")
    print(f"  골격근량: {SAMPLE_MEASUREMENTS['체중관리']['골격근량']}kg")

    # 2. LLM 클라이언트 및 에이전트 생성
    print("\n[2] LLM 에이전트 초기화")
    llm_client = create_llm_client("gpt-4o-mini")
    analysis_agent = create_analysis_agent_with_rag(llm_client, use_rag=True)
    print("  ✓ 에이전트 생성 완료 (2단계 프롬프트 + RAG)")

    # 3. 에이전트 실행
    print("\n[3] 2단계 분석 수행")
    thread_id = f"test_2step_{datetime.now().timestamp()}"
    config = {"configurable": {"thread_id": thread_id}}

    try:
        result = analysis_agent.invoke(
            {
                "analysis_input": analysis_input,
                "messages": [],
                "embedding": None,
                "rag_context": None
            },
            config=config
        )

        # 4. 결과 출력
        print("\n[4] 분석 결과")
        print("=" * 60)

        analysis_text = result['messages'][-1].content
        print(analysis_text)

        print("\n" + "=" * 60)
        print("[5] 메타 정보")
        print(f"  Thread ID: {thread_id}")
        print(f"  RAG 활성화: {'✓' if result.get('rag_context') else '×'}")
        print(f"  Embedding: {'✓' if result.get('embedding', {}).get('embedding_1536') else '×'}")
        print(f"  총 응답 길이: {len(analysis_text)} 문자")

        # 5. 응답 구조 확인
        print("\n[6] 응답 구조 검증")
        lines = analysis_text.split('\n')
        summary_section = [l for l in lines if '✅' in l]
        detail_sections = [l for l in lines if l.startswith('📊') or l.startswith('📈') or l.startswith('⚠️')]

        print(f"  5줄 요약 항목: {len(summary_section)}개")
        for item in summary_section[:5]:
            print(f"    - {item[:60]}...")

        print(f"\n  세부 리포트 섹션: {len(detail_sections)}개")
        for section in detail_sections:
            print(f"    - {section}")

        print("\n✅ 테스트 완료!")

    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_two_step_analysis())
