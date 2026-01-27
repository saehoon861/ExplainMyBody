#!/usr/bin/env python3
"""
주간 계획 생성 파이프라인 실행 파일
Endpoint: /api/weekly-plan/generate
"""

import sys
import argparse
import json
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.database import Database
from shared.llm_clients import create_llm_client
from shared.models import (
    UserGoal,
    UserPreferences,
    WeeklyPlanRequest,
    WeeklyPlanResponse,
)

from pipeline_weekly_plan.planner import WeeklyPlanner

load_dotenv()


def run_weekly_plan_generation(
    user_id: int,
    goals_dict_list: list,
    preferences_dict: dict,
    week_number: int = 1,
    start_date: str = None,
    model: str = "gpt-4o-mini",
    db_url: str = None,
    use_ollama_rag: bool = False,
) -> WeeklyPlanResponse:
    """
    주간 계획 생성 파이프라인 실행

    Args:
        user_id: 사용자 ID
        goals_dict_list: 목표 리스트 (dict)
        preferences_dict: 선호도 (dict)
        week_number: 주차
        start_date: 시작 날짜
        model: LLM 모델
        db_url: DB URL
        use_ollama_rag: RAG에서 Ollama bge-m3 사용 여부

    Returns:
        WeeklyPlanResponse
    """
    try:
        # 1. Pydantic 모델 검증
        goals = [UserGoal(**g) for g in goals_dict_list]
        preferences = UserPreferences(**preferences_dict)

        # 2. Database 및 LLM 클라이언트 초기화
        db = Database(db_url)
        llm_client = create_llm_client(model)

        print(f"✅ 데이터베이스 연결 완료")
        print(f"🤖 LLM 모델: {model}")

        # 3. 주간 계획 생성
        planner = WeeklyPlanner(db, llm_client, model, use_ollama_rag=use_ollama_rag)
        weekly_plan = planner.generate_plan(
            user_id=user_id,
            goals=goals,
            preferences=preferences,
            week_number=week_number,
            start_date=start_date,
        )

        # 4. DB 저장 (선택적)
        plan_id = planner.save_plan_to_db(weekly_plan)

        # 5. 성공 응답
        return WeeklyPlanResponse(
            success=True, plan_id=plan_id, weekly_plan=weekly_plan
        )

    except Exception as e:
        # 에러 응답
        print(f"\n❌ 오류 발생: {e}")
        import traceback

        traceback.print_exc()

        return WeeklyPlanResponse(success=False, error=str(e))


def main():
    parser = argparse.ArgumentParser(description="주간 계획 생성 파이프라인")

    # 필수 인자
    parser.add_argument("--user-id", type=int, required=True, help="사용자 ID")

    # 목표 및 선호도 입력
    parser.add_argument("--goals-json", type=str, help="목표 JSON 문자열 (리스트)")
    parser.add_argument("--goals-file", type=str, help="목표 JSON 파일")
    parser.add_argument("--preferences-json", type=str, help="선호도 JSON 문자열")
    parser.add_argument("--preferences-file", type=str, help="선호도 JSON 파일")

    # 선택적 인자
    parser.add_argument("--week-number", type=int, default=1, help="주차 (기본: 1)")
    parser.add_argument("--start-date", type=str, help="시작 날짜 (YYYY-MM-DD)")
    parser.add_argument(
        "--model", default="gpt-4o-mini", help="LLM 모델"
    )
    parser.add_argument("--db-url", default=None, help="데이터베이스 URL")
    parser.add_argument("--output-file", type=str, help="결과 저장 JSON 파일")
    parser.add_argument(
        "--use-ollama-rag",
        action="store_true",
        help="RAG에서 Ollama bge-m3 사용 (기본: OpenAI)",
    )

    args = parser.parse_args()

    # 목표 로드
    if args.goals_json:
        goals_list = json.loads(args.goals_json)
    elif args.goals_file:
        with open(args.goals_file, "r", encoding="utf-8") as f:
            goals_list = json.load(f)
    else:
        # 기본 목표
        print("⚠️  목표가 지정되지 않았습니다. 기본 목표를 사용합니다.")
        goals_list = [
            {
                "goal_type": "건강유지",
                "priority": "medium",
            }
        ]

    # 선호도 로드
    if args.preferences_json:
        preferences_dict = json.loads(args.preferences_json)
    elif args.preferences_file:
        with open(args.preferences_file, "r", encoding="utf-8") as f:
            preferences_dict = json.load(f)
    else:
        # 기본 선호도
        print("⚠️  선호도가 지정되지 않았습니다. 기본 설정을 사용합니다.")
        preferences_dict = {
            "preferred_exercise_types": ["웨이트", "유산소"],
            "exercise_frequency": 3,
            "exercise_duration": 60,
            "exercise_intensity": "medium",
            "dietary_restrictions": [],
            "preferred_cuisine": ["한식"],
            "disliked_foods": [],
            "meal_frequency": 3,
            "health_conditions": [],
            "injuries": [],
            "medications": [],
        }

    # 계획 생성
    response = run_weekly_plan_generation(
        user_id=args.user_id,
        goals_dict_list=goals_list,
        preferences_dict=preferences_dict,
        week_number=args.week_number,
        start_date=args.start_date,
        model=args.model,
        db_url=args.db_url,
        use_ollama_rag=args.use_ollama_rag,
    )

    # 결과 출력
    print("\n" + "=" * 60)
    print("📋 주간 계획 결과")
    print("=" * 60)

    if response.success:
        print(f"✅ 성공!")
        print(f"   - Plan ID: {response.plan_id}")
        print(f"\n## 주간 요약")
        print(response.weekly_plan.weekly_summary)
        print(f"\n## 주간 목표")
        print(response.weekly_plan.weekly_goal)

        if response.weekly_plan.tips:
            print(f"\n## 팁")
            for i, tip in enumerate(response.weekly_plan.tips, 1):
                print(f"{i}. {tip}")

        print(f"\n## 요일별 계획")
        for day_plan in response.weekly_plan.daily_plans:
            print(f"\n### {day_plan.day_of_week}")
            print(f"  운동: {len(day_plan.exercises)}개")
            print(f"  식사: {len(day_plan.meals)}개")
            if day_plan.total_calories:
                print(f"  총 칼로리: {day_plan.total_calories} kcal")

        # 파일로 저장
        if args.output_file:
            output_data = response.model_dump()
            with open(args.output_file, "w", encoding="utf-8") as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2, default=str)
            print(f"\n💾 결과 저장: {args.output_file}")

    else:
        print(f"❌ 실패: {response.error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
