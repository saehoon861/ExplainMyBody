#!/usr/bin/env python3
"""
주간 계획 생성 파이프라인 실행 파일 (Graph RAG 적용)
- 항상 gpt-4o-mini 및 text-embedding-3-small 사용
- Graph RAG (Vector + Graph Traversal) 자동 적용
"""

import sys
import argparse
import json
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.llm_clients import create_llm_client
from shared.models import (
    UserGoal,
    UserPreferences,
    WeeklyPlanRequest,
    WeeklyPlanResponse,
)

from pipeline_weekly_plan_rag.planner import WeeklyPlannerGraphRAG

load_dotenv()


def run_weekly_plan_generation_with_graph_rag(
    user_id: int,
    goals_dict_list: list,
    preferences_dict: dict,
    week_number: int = 1,
    start_date: str = None,
    db_url: str = None,
    use_neo4j: bool = True,
) -> WeeklyPlanResponse:
    """
    주간 계획 생성 파이프라인 실행 (Graph RAG 적용)

    Args:
        user_id: 사용자 ID
        goals_dict_list: 목표 리스트 (dict)
        preferences_dict: 선호도 (dict)
        week_number: 주차
        start_date: 시작 날짜
        db_url: DB URL
        use_neo4j: Neo4j 그래프 탐색 사용 여부

    Returns:
        WeeklyPlanResponse
    """
    try:
        # 1. Pydantic 모델 검증
        goals = [UserGoal(**g) for g in goals_dict_list]
        preferences = UserPreferences(**preferences_dict)

        # 2. LLM 클라이언트 초기화 (항상 gpt-4o-mini)
        model = "gpt-4o-mini"
        llm_client = create_llm_client(model)

        print(f"✅ LLM 초기화 완료")
        print(f"🤖 LLM 모델: {model} (고정)")
        print(f"📊 Embedding: text-embedding-3-small (고정)")

        # 3. 주간 계획 생성 (Graph RAG 자동 적용)
        planner = WeeklyPlannerGraphRAG(
            llm_client=llm_client,
            model_version=model,
            use_graph_rag=True,  # 항상 Graph RAG 사용
            use_neo4j=use_neo4j,
        )

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
    parser = argparse.ArgumentParser(description="주간 계획 생성 파이프라인 (Graph RAG)")

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
    parser.add_argument("--db-url", default=None, help="데이터베이스 URL")
    parser.add_argument("--output-file", type=str, help="결과 저장 TXT 파일")
    parser.add_argument(
        "--no-neo4j",
        action="store_true",
        help="Neo4j 그래프 탐색 비활성화 (Vector만 사용)",
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
                "goal_type": "근성장",
                "priority": "high",
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
            "exercise_frequency": 4,
            "exercise_duration": 60,
            "exercise_intensity": "high",
            "dietary_restrictions": [],
            "preferred_cuisine": ["한식"],
            "disliked_foods": [],
            "meal_frequency": 3,
            "health_conditions": [],
            "injuries": [],
            "medications": [],
        }

    # 계획 생성 (Graph RAG 자동 적용)
    response = run_weekly_plan_generation_with_graph_rag(
        user_id=args.user_id,
        goals_dict_list=goals_list,
        preferences_dict=preferences_dict,
        week_number=args.week_number,
        start_date=args.start_date,
        db_url=args.db_url,
        use_neo4j=not args.no_neo4j,
    )

    # 결과 출력
    print("\n" + "=" * 60)
    print("📋 주간 계획 결과 (Graph RAG)")
    print("=" * 60)

    if response.success:
        print(f"✅ 성공!")
        print(f"   - Plan ID: {response.plan_id}")
        print(f"   - 모델: gpt-4o-mini")
        print(f"   - Embedding: text-embedding-3-small")
        print(f"   - Graph RAG: ✅ 적용됨")

        # LLM 원본 출력 표시
        if response.weekly_plan.llm_raw_output:
            print(f"\n{response.weekly_plan.llm_raw_output}")
        else:
            # Fallback: 구조화된 출력
            print(f"\n## 주간 요약")
            print(response.weekly_plan.weekly_summary)
            print(f"\n## 주간 목표")
            print(response.weekly_plan.weekly_goal)

        # 파일로 저장 (TXT 형식 - LLM 원본 출력)
        if args.output_file:
            output_path = Path(args.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write("=" * 80 + "\n")
                f.write("주간 운동/식단 계획 (Graph RAG 적용)\n")
                f.write("=" * 80 + "\n\n")
                f.write(f"Plan ID: {response.plan_id}\n")
                f.write(f"주차: {response.weekly_plan.week_number}\n")
                f.write(f"기간: {response.weekly_plan.start_date} ~ {response.weekly_plan.end_date}\n")
                f.write(f"모델: gpt-4o-mini\n")
                f.write(f"Embedding: text-embedding-3-small\n")
                f.write(f"Graph RAG: ✅ 적용됨\n\n")
                f.write("-" * 80 + "\n\n")

                # LLM 원본 출력 저장
                if response.weekly_plan.llm_raw_output:
                    f.write(response.weekly_plan.llm_raw_output)
                else:
                    # Fallback
                    f.write(response.weekly_plan.weekly_summary)

            print(f"\n💾 결과 저장: {output_path.absolute()}")

    else:
        print(f"❌ 실패: {response.error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
