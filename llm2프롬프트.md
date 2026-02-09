● ✅ 노드 교체 시 수정 필요한 부분 확인 결과

  🔍 주요 변경사항

  1. 함수 시그니처 변경:
    - def generate_initial_plan(state: PlanState)
    - → async def generate_initial_plan_concurrently(state: PlanState, llm_client)
  
  2. 추가 import:
  import asyncio  # ← 추가 필요
  
  3. workflow 노드 등록 방식 변경:
  
  # 원본
  workflow.add_node("initial_plan", generate_initial_plan)

  # 교체판
  workflow.add_node(
      "initial_plan",
      lambda state: generate_initial_plan_concurrently(state, llm_client)
  )



  ---
  ✅ 수정 불필요한 파일들 (영향 없음)

  1. llm_service.py

  - from .weekly_plan_graph import create_weekly_plan_agent 만 import
  - 노드를 직접 호출하지 않음 → 수정 불필요

  2. weekly_plan_service.py

  - 노드를 직접 호출하지 않음 → 수정 불필요

  3. 스키마/모델/레포지토리

  - schemas/llm.py, models/weekly_plan.py, repositories/llm/weekly_plan_repository.py
  - 노드 내부 로직만 변경되므로 → 수정 불필요

  4. 라우터

  - service만 호출 → 수정 불필요

  ---
  📝 결론

  수정 필요한 파일: weekly_plan_graph.py 단 1개만

  변경 내용:
  1. import asyncio 추가
  2. generate_initial_plan → generate_initial_plan_concurrently 함수 교체
  3. workflow.add_node() 부분 lambda로 감싸기

  다른 모든 파일은 수정 불필요! 노드 내부 구현만 바뀌므로 외부 인터페이스(create_weekly_plan_agent)는 동일합니다.





● weekly_plan_graph 관련 파일 위치:

  📁 핵심 파일 (backend/services/llm/)

  1. weekly_plan_graph.py ← 원본
  2. weekly_plan_graph copy.py ← 복사본 (node 교체용)
  4. weekly_plan_service.py ← 서비스 레이어

  🔗 사용하는 파일들

  5. llm_service.py (line 16: from .weekly_plan_graph import ...)

  📊 데이터 레이어

  9. backend/schemas/llm.py ← WeeklyPlan 스키마
  10. backend/models/weekly_plan.py ← ORM 모델
  11. backend/repositories/llm/weekly_plan_repository.py ← DB 접근

  🧪 테스트 파일들 (src/llm/)

  12. src/llm/llm_test_sk/weekly_plan_graph.py
  13. src/llm/llm_prompt_test_sk/test_weekly_plan.py


