"""
주간 계획 생성 로직 (Graph RAG 적용)
- InBody RAG + Graph RAG (논문 기반) 결합
- 항상 gpt-4o-mini 사용
"""

from typing import List
from datetime import datetime, timedelta

from shared.models import UserGoal, UserPreferences, WeeklyPlan
from shared.llm_clients import BaseLLMClient

from pipeline_weekly_plan_rag.graph_rag_retriever import GraphRAGRetriever
from pipeline_weekly_plan_rag.prompt_generator import create_weekly_plan_prompt


class WeeklyPlannerGraphRAG:
    """주간 운동/식단 계획 생성기 (Graph RAG 적용)"""

    def __init__(
        self,
        llm_client: BaseLLMClient,
        model_version: str = "gpt-4o-mini",
        use_graph_rag: bool = True,
        use_neo4j: bool = True,
    ):
        """
        Args:
            llm_client: LLM 클라이언트
            model_version: 모델 버전 (항상 gpt-4o-mini)
            use_graph_rag: Graph RAG 사용 여부 (기본: True)
            use_neo4j: Neo4j 그래프 탐색 사용 여부 (기본: True)
        """
        self.llm_client = llm_client
        self.model_version = model_version
        self.use_graph_rag = use_graph_rag

        # Graph RAG Retriever (논문만 사용)
        self.graph_rag = None
        if use_graph_rag:
            try:
                self.graph_rag = GraphRAGRetriever(use_neo4j=use_neo4j)
                print("  ✅ Graph RAG 활성화")
            except Exception as e:
                print(f"  ⚠️  Graph RAG 초기화 실패: {e}")
                self.use_graph_rag = False

    def generate_plan(
        self,
        user_id: int,
        goals: List[UserGoal],
        preferences: UserPreferences,
        week_number: int = 1,
        start_date: str = None,
    ) -> WeeklyPlan:
        """
        주간 계획 생성

        Args:
            user_id: 사용자 ID
            goals: 사용자 목표 리스트
            preferences: 사용자 선호도
            week_number: 주차
            start_date: 시작 날짜 (YYYY-MM-DD)

        Returns:
            WeeklyPlan
        """
        print("=" * 60)
        print(f"주간 계획 생성 시작 (User ID: {user_id}, Week {week_number})")
        print(f"  🔧 모델: {self.model_version}")
        print(f"  🔧 Graph RAG: {'✅ Enabled' if self.use_graph_rag else '❌ Disabled'}")
        print("=" * 60)

        # 1단계: Graph RAG 논문 검색
        paper_context = []
        if self.use_graph_rag and self.graph_rag:
            print("\n🔍 1단계: Graph RAG 논문 검색...")

            # 사용자 목표에서 핵심 개념 추출
            concepts = self._extract_concepts_from_goals(goals)

            # 쿼리 생성
            query = self._generate_query_from_goals(goals, preferences)

            # Graph RAG 검색
            paper_context = self.graph_rag.retrieve_relevant_papers(
                query=query,
                concepts=concepts,
                top_k=5,
                domain=None,  # 도메인 자동 추론
                lang="ko",
            )

            if paper_context:
                print(f"  ✓ {len(paper_context)}개 관련 논문 검색 완료")
            else:
                print("  ⚠️  관련 논문이 없습니다.")

        # 3단계: 날짜 계산
        if not start_date:
            # 다음 주 월요일
            today = datetime.now()
            days_until_monday = (7 - today.weekday()) % 7
            if days_until_monday == 0:
                days_until_monday = 7
            next_monday = today + timedelta(days=days_until_monday)
            start_date = next_monday.strftime("%Y-%m-%d")

        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = start + timedelta(days=6)
        end_date = end.strftime("%Y-%m-%d")

        print(f"\n  ✓ 기간: {start_date} ~ {end_date}")

        # 2단계: 프롬프트 생성 (Graph RAG 컨텍스트 포함)
        print("\n📝 2단계: 프롬프트 생성...")
        system_prompt, user_prompt = create_weekly_plan_prompt(
            user_goals=goals,
            user_preferences=preferences,
            inbody_context=[],  # Graph RAG 전용 (InBody 없음)
            week_number=week_number,
            start_date=start_date,
        )

        # Graph RAG 논문 컨텍스트를 프롬프트에 추가
        if paper_context:
            paper_text = self._format_paper_context(paper_context)
            user_prompt += f"\n\n## 📚 과학적 근거 (최신 연구 논문)\n\n{paper_text}"

        # 3단계: LLM 호출 (gpt-4o-mini)
        print(f"\n🤖 3단계: LLM 주간 계획 생성 ({self.model_version})...")
        print("  - LLM 호출 중...")
        llm_output = self.llm_client.generate_chat(system_prompt, user_prompt)

        print(f"  ✓ 계획 생성 완료 ({len(llm_output)} 글자)")

        # 4단계: WeeklyPlan 모델 생성
        print("\n📊 4단계: 계획 저장 준비...")
        weekly_plan = WeeklyPlan(
            user_id=user_id,
            week_number=week_number,
            start_date=start_date,
            end_date=end_date,
            weekly_summary="",
            weekly_goal="",
            tips=[],
            daily_plans=[],
            model_version=self.model_version,
            llm_raw_output=llm_output,  # LLM 원본 자연어 출력
        )

        print(f"  ✓ 자연어 계획 생성 완료")

        print("\n" + "=" * 60)
        print("✨ 주간 계획 생성 완료!")
        print("=" * 60)

        return weekly_plan

    def _extract_concepts_from_goals(self, goals: List[UserGoal]) -> List[str]:
        """
        사용자 목표에서 핵심 개념 추출

        Args:
            goals: 사용자 목표 리스트

        Returns:
            개념 ID 리스트
        """
        # 목표 타입 → 개념 매핑
        goal_to_concepts = {
            "근성장": ["muscle_hypertrophy", "resistance_training", "protein_intake"],
            "체지방감소": ["fat_loss", "caloric_deficit", "cardio"],
            "건강유지": ["general_health", "exercise", "balanced_diet"],
            "체력증진": ["endurance", "cardiovascular_fitness"],
            "근력증가": ["strength_training", "progressive_overload"],
        }

        concepts = set()
        for goal in goals:
            goal_type = goal.goal_type
            if goal_type in goal_to_concepts:
                concepts.update(goal_to_concepts[goal_type])

        return list(concepts)

    def _generate_query_from_goals(
        self, goals: List[UserGoal], preferences: UserPreferences
    ) -> str:
        """
        사용자 목표 및 선호도에서 검색 쿼리 생성

        Args:
            goals: 사용자 목표 리스트
            preferences: 사용자 선호도

        Returns:
            검색 쿼리 문자열
        """
        goal_texts = [goal.goal_type for goal in goals]
        exercise_types = preferences.preferred_exercise_types or []

        query = f"{', '.join(goal_texts)} 목표를 위한 {', '.join(exercise_types)} 운동 효과"
        return query

    def _format_paper_context(self, papers: List[dict]) -> str:
        """
        논문 컨텍스트를 프롬프트 형식으로 포맷팅

        Args:
            papers: 논문 리스트

        Returns:
            포맷된 문자열
        """
        formatted_text = ""

        for i, paper in enumerate(papers, 1):
            title = paper.get('title', 'N/A')
            chunk_text = paper.get('chunk_text', '')
            chunk_ko_summary = paper.get('chunk_ko_summary', '')
            year = paper.get('year', 'N/A')
            source = paper.get('source', 'N/A')
            final_score = paper.get('final_score', 0.0)

            # 한국어 요약이 있으면 우선 사용, 없으면 원문 일부 사용
            content = chunk_ko_summary if chunk_ko_summary else chunk_text[:300]

            formatted_text += f"""
### 논문 {i}: {title}
- 출처: {source} ({year})
- 관련도: {final_score:.2f}
- 요약: {content}

"""

        return formatted_text

    def save_plan_to_db(self, weekly_plan: WeeklyPlan) -> int:
        """
        주간 계획 완료 (Graph RAG 전용 - DB 저장 없음)

        Args:
            weekly_plan: 주간 계획

        Returns:
            plan_id (더미)
        """
        print("\n✅ 주간 계획 생성 완료")
        return 1

    def __del__(self):
        """소멸자 - 리소스 정리"""
        if self.graph_rag:
            self.graph_rag.close()
