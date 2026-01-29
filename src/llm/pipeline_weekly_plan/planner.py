"""
주간 계획 생성 로직
"""

from typing import List
from datetime import datetime, timedelta

from shared.models import UserGoal, UserPreferences, WeeklyPlan
from shared.llm_clients import BaseLLMClient
from shared.database import Database

from pipeline_weekly_plan.rag_retriever import InBodyRAGRetriever
from pipeline_weekly_plan.prompt_generator import create_weekly_plan_prompt


class WeeklyPlanner:
    """주간 운동/식단 계획 생성기"""

    def __init__(
        self, db: Database, llm_client: BaseLLMClient, model_version: str, use_ollama_rag: bool = False
    ):
        """
        Args:
            db: Database 인스턴스
            llm_client: LLM 클라이언트
            model_version: 모델 버전
            use_ollama_rag: RAG에서 Ollama bge-m3 사용 여부
        """
        self.db = db
        self.llm_client = llm_client
        self.model_version = model_version
        self.rag_retriever = InBodyRAGRetriever(db, use_ollama=use_ollama_rag)

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
        print("=" * 60)

        # 1단계: InBody 분석 결과 검색 (RAG)
        print("\n🔍 1단계: InBody 분석 결과 검색...")
        inbody_context = self.rag_retriever.retrieve_similar_analyses(
            user_id=user_id, query="체형 분석", top_k=6
        )

        if not inbody_context:
            print("  ⚠️  InBody 분석 결과가 없습니다. 일반적인 계획을 생성합니다.")

        # 2단계: 날짜 계산
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

        print(f"  ✓ 기간: {start_date} ~ {end_date}")

        # 3단계: 프롬프트 생성
        print("\n📝 2단계: 프롬프트 생성...")
        system_prompt, user_prompt = create_weekly_plan_prompt(
            user_goals=goals,
            user_preferences=preferences,
            inbody_context=inbody_context,
            week_number=week_number,
            start_date=start_date,
        )

        # 4단계: LLM 호출
        print("\n🤖 3단계: LLM 주간 계획 생성...")
        print("  - LLM 호출 중...")
        llm_output = self.llm_client.generate_chat(system_prompt, user_prompt)

        print(f"  ✓ 계획 생성 완료 ({len(llm_output)} 글자)")

        # 5단계: WeeklyPlan 모델 생성 (자연어 출력 사용)
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

    def save_plan_to_db(self, weekly_plan: WeeklyPlan) -> int:
        """
        주간 계획을 DB에 저장 (SQLAlchemy)

        Args:
            weekly_plan: 주간 계획

        Returns:
            plan_id
        """
        print("\n💾 주간 계획 저장...")

        try:
            # datetime.date 객체로 변환
            from datetime import datetime

            start_date_obj = datetime.strptime(
                weekly_plan.start_date, "%Y-%m-%d"
            ).date()
            end_date_obj = datetime.strptime(weekly_plan.end_date, "%Y-%m-%d").date()

            # DB에 저장 (SQLAlchemy)
            # mode='json'을 사용하여 datetime을 문자열로 직렬화
            plan_id = self.db.save_weekly_plan(
                user_id=weekly_plan.user_id,
                week_number=weekly_plan.week_number,
                start_date=start_date_obj,
                end_date=end_date_obj,
                plan_data=weekly_plan.model_dump(mode='json'),
                model_version=weekly_plan.model_version,
            )

            print(f"  ✓ DB 저장 완료 (Plan ID: {plan_id})")

            return plan_id

        except Exception as e:
            print(f"  ⚠️  DB 저장 실패: {e}")
            import traceback

            traceback.print_exc()
            return 1  # fallback ID
