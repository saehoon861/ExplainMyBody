"""
InBody 분석 테스트 (LLM1 + RAG)
샘플 데이터로 건강 상태 분석 프롬프트 생성 및 LLM 호출
"""

import asyncio
from datetime import datetime

from sample_data import SAMPLE_MEASUREMENTS, SAMPLE_USER
from schemas import StatusAnalysisInput
from llm_clients import create_llm_client
from agent_graph_rag import create_analysis_agent_with_rag


async def test_inbody_analysis():
    """InBody 분석 테스트"""

    print("=" * 60)
    print("InBody 건강 상태 분석 테스트 (LLM1 + RAG)")
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
    print(f"  Record ID: {analysis_input.record_id}")
    print(f"  측정일: {analysis_input.measured_at.strftime('%Y-%m-%d')}")
    print(f"  체형: {analysis_input.body_type1} / {analysis_input.body_type2}")
    print(f"  체중: {SAMPLE_MEASUREMENTS['체중관리']['체중']}kg")
    print(f"  체지방률: {SAMPLE_MEASUREMENTS['비만분석']['체지방률']}%")
    print(f"  골격근량: {SAMPLE_MEASUREMENTS['체중관리']['골격근량']}kg")

    # 2. LLM 클라이언트 및 에이전트 생성
    print("\n[2] LLM 에이전트 초기화")
    llm_client = create_llm_client("gpt-4o-mini")
    analysis_agent = create_analysis_agent_with_rag(llm_client, use_rag=True)
    print("  ✓ 에이전트 생성 완료 (RAG 활성화)")

    # 3. 에이전트 실행
    print("\n[3] 분석 수행 중...")
    thread_id = f"test_analysis_{datetime.now().timestamp()}"
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
        print("[5] 추가 정보")
        print(f"  Thread ID: {thread_id}")

        if result.get("rag_context"):
            print(f"  RAG 검색: ✓ (논문 컨텍스트 포함)")
        else:
            print(f"  RAG 검색: × (논문 검색 실패 또는 비활성화)")

        if result.get("embedding"):
            emb = result["embedding"].get("embedding_1536")
            if emb:
                print(f"  Embedding: ✓ (1536D, 첫 3개: {emb[:3]})")
            else:
                print(f"  Embedding: × (생성 실패)")

        print("\n✅ 테스트 완료!")

    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_inbody_analysis())
