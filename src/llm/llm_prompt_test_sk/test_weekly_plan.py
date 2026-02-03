"""
주간 계획 생성 테스트 (LLM2 + RAG)
샘플 데이터로 주간 운동/식단 계획 생성 프롬프트 테스트
"""

import asyncio
from datetime import datetime

from sample_data import SAMPLE_MEASUREMENTS, SAMPLE_USER, SAMPLE_GOAL, SAMPLE_ANALYSIS_RESULT
from schemas import GoalPlanInput
from llm_clients import create_llm_client
from weekly_plan_graph_rag import create_weekly_plan_agent_with_rag


async def test_weekly_plan():
    """주간 계획 생성 테스트"""

    print("=" * 60)
    print("주간 계획 생성 테스트 (LLM2 + RAG)")
    print("=" * 60)

    # 1. 입력 데이터 준비
    plan_input = GoalPlanInput(
        user_goal_type=SAMPLE_GOAL["user_goal_type"],
        user_goal_description=SAMPLE_GOAL["user_goal_description"],
        record_id=SAMPLE_USER["record_id"],
        user_id=SAMPLE_USER["user_id"],
        measured_at=SAMPLE_USER["measured_at"],
        measurements=SAMPLE_MEASUREMENTS,
        status_analysis_result=SAMPLE_ANALYSIS_RESULT,
        status_analysis_id=None,
        main_goal=SAMPLE_GOAL["main_goal"],
        target_weight=SAMPLE_GOAL["target_weight"],
        target_date=SAMPLE_GOAL["target_date"],
        preferred_exercise_types=SAMPLE_GOAL["preferred_exercise_types"],
        available_days_per_week=SAMPLE_GOAL["available_days_per_week"],
        available_time_per_session=SAMPLE_GOAL["available_time_per_session"],
        restrictions=SAMPLE_GOAL["restrictions"]
    )

    print("\n[1] 입력 데이터")
    print(f"  User ID: {plan_input.user_id}")
    print(f"  목표: {plan_input.user_goal_type}")
    print(f"  목표 설명: {plan_input.user_goal_description}")
    print(f"  선호 운동: {', '.join(plan_input.preferred_exercise_types)}")
    print(f"  주당 운동 일수: {plan_input.available_days_per_week}일")
    print(f"  1회 운동 시간: {plan_input.available_time_per_session}분")
    print(f"  제약사항: {', '.join(plan_input.restrictions) if plan_input.restrictions else '없음'}")

    # 2. LLM 클라이언트 및 에이전트 생성
    print("\n[2] LLM 에이전트 초기화")
    llm_client = create_llm_client("gpt-4o-mini")
    plan_agent = create_weekly_plan_agent_with_rag(llm_client, use_rag=True)
    print("  ✓ 에이전트 생성 완료 (RAG 활성화)")

    # 3. 에이전트 실행
    print("\n[3] 계획 생성 중...")
    thread_id = f"test_plan_{datetime.now().timestamp()}"
    config = {"configurable": {"thread_id": thread_id}}

    try:
        result = plan_agent.invoke(
            {
                "plan_input": plan_input,
                "messages": [],
                "rag_context": None
            },
            config=config
        )

        # 4. 결과 출력
        print("\n[4] 주간 계획")
        print("=" * 60)

        plan_text = result['messages'][-1].content
        print(plan_text)

        print("\n" + "=" * 60)
        print("[5] 추가 정보")
        print(f"  Thread ID: {thread_id}")

        if result.get("rag_context"):
            print(f"  RAG 검색: ✓ (논문 컨텍스트 포함)")
        else:
            print(f"  RAG 검색: × (논문 검색 실패 또는 비활성화)")

        print(f"  이전 분석 결과: ✓ (포함됨)")

        print("\n✅ 테스트 완료!")

    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_weekly_plan())
