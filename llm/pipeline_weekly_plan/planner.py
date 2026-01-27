"""
주간 계획 생성 로직
"""

import json
from typing import List, Dict, Any
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

        # 5단계: JSON 파싱
        print("\n📊 4단계: JSON 파싱...")
        try:
            # LLM 응답에서 JSON 추출
            plan_data = self._extract_json(llm_output)

            # WeeklyPlan 모델 생성
            weekly_plan = WeeklyPlan(
                user_id=user_id,
                week_number=week_number,
                start_date=start_date,
                end_date=end_date,
                weekly_summary=plan_data.get("weekly_summary", ""),
                weekly_goal=plan_data.get("weekly_goal", ""),
                tips=plan_data.get("tips", []),
                daily_plans=plan_data.get("daily_plans", []),
                model_version=self.model_version,
            )

            print(f"  ✓ 파싱 성공: {len(weekly_plan.daily_plans)}일 계획")

        except Exception as e:
            print(f"  ⚠️  JSON 파싱 실패: {e}")
            print("  원본 응답을 사용합니다.")

            # Fallback: 기본 구조 생성
            weekly_plan = WeeklyPlan(
                user_id=user_id,
                week_number=week_number,
                start_date=start_date,
                end_date=end_date,
                weekly_summary=llm_output,
                weekly_goal="",
                daily_plans=[],
                model_version=self.model_version,
            )

        print("\n" + "=" * 60)
        print("✨ 주간 계획 생성 완료!")
        print("=" * 60)

        return weekly_plan

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        LLM 응답에서 JSON 추출

        Args:
            text: LLM 응답 텍스트

        Returns:
            파싱된 JSON dict
        """
        # JSON 블록 찾기 (```json ... ``` 또는 순수 JSON)
        import re

        # 1. Markdown JSON 블록 찾기
        json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 2. 중괄호로 시작하는 JSON 찾기
            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                # 3. 전체를 JSON으로 시도
                json_str = text

        return json.loads(json_str)

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
            plan_id = self.db.save_weekly_plan(
                user_id=weekly_plan.user_id,
                week_number=weekly_plan.week_number,
                start_date=start_date_obj,
                end_date=end_date_obj,
                plan_data=weekly_plan.model_dump(),
                model_version=weekly_plan.model_version,
            )

            print(f"  ✓ DB 저장 완료 (Plan ID: {plan_id})")

            # 백업: JSON 파일로도 저장
            from pathlib import Path

            output_dir = Path("outputs/weekly_plans")
            output_dir.mkdir(parents=True, exist_ok=True)

            filename = f"user{weekly_plan.user_id}_week{weekly_plan.week_number}_{weekly_plan.start_date}.json"
            filepath = output_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(
                    weekly_plan.model_dump(),
                    f,
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                )

            print(f"  ✓ 백업 저장: {filepath}")

            return plan_id

        except Exception as e:
            print(f"  ⚠️  DB 저장 실패: {e}")
            import traceback

            traceback.print_exc()
            return 1  # fallback ID
