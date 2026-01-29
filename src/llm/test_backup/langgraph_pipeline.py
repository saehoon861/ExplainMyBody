#!/usr/bin/env python3
"""
LangGraph 기반 2단계 LLM 파이프라인
Step 1: 자연어로 추천 생성
Step 2: 자연어를 JSON으로 변환
"""

from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import json
from pydantic import ValidationError

from models import BodyAnalysisResult, LLMRecommendation


class PipelineState(TypedDict):
    """
    LangGraph 상태 정의
    - 그래프의 각 노드를 통해 전달되는 데이터 구조
    """
    analysis_result: dict  # 체형 분석 결과
    natural_language_response: str | None  # Step 1: 자연어 추천
    json_response: dict | None  # Step 2: JSON 변환 결과
    error: str | None  # 에러 메시지


def generate_natural_language(state: PipelineState, client) -> PipelineState:
    """
    Node 1: LLM에게 자연어로 추천 생성 요청

    Args:
        state: 현재 상태 (분석 결과 포함)
        client: LLM 클라이언트 (Claude, OpenAI, Ollama 등)

    Returns:
        업데이트된 상태 (자연어 응답 포함)
    """
    print("[Step 1] Generating natural language recommendations...")

    try:
        analysis = state["analysis_result"]

        # 자연어 생성용 프롬프트
        system_prompt = """당신은 전문 피트니스 트레이너입니다.
사용자의 체형 분석 결과를 바탕으로 친절하고 자세한 운동 및 식단 추천을 제공하세요.
자연스러운 대화체로 작성하되, 다음 내용을 포함해주세요:
1. 체형 분석 요약
2. 운동 계획 (주간 목표, 추천 운동, 부위별 운동)
3. 식단 계획 (목표 칼로리, 식사 구성, 영양소 비율)
4. 생활 습관 조언"""

        user_prompt = f"""다음은 사용자의 체형 분석 결과입니다:

{json.dumps(analysis, ensure_ascii=False, indent=2)}

위 분석 결과를 바탕으로 상세한 운동 및 식단 추천을 작성해주세요."""

        # LLM 호출
        natural_response = client.generate_chat(system_prompt, user_prompt)

        if not natural_response:
            raise Exception("자연어 생성 실패")

        print(f"  ✓ Generated {len(natural_response)} characters")

        # 상태 업데이트
        state["natural_language_response"] = natural_response
        state["error"] = None

    except Exception as e:
        print(f"  ✗ Error: {type(e).__name__} - {str(e)}")
        state["error"] = f"Step 1 failed: {str(e)}"

    return state


def convert_to_json(state: PipelineState, client) -> PipelineState:
    """
    Node 2: 자연어 응답을 구조화된 JSON으로 변환

    Args:
        state: 현재 상태 (자연어 응답 포함)
        client: LLM 클라이언트

    Returns:
        업데이트된 상태 (JSON 응답 포함)
    """
    print("[Step 2] Converting to structured JSON...")

    try:
        natural_text = state["natural_language_response"]

        if not natural_text:
            raise Exception("자연어 응답이 없습니다")

        # JSON 변환용 프롬프트
        system_prompt = """당신은 자연어 텍스트를 구조화된 JSON으로 변환하는 전문가입니다.
주어진 운동/식단 추천 텍스트를 아래 JSON 스키마에 맞게 정확히 변환하세요.

JSON 스키마:
{
  "body_analysis_summary": {
    "body_type": "체형 유형 (예: 마른비만형)",
    "key_issues": ["주요 문제점1", "주요 문제점2"],
    "overall_goal": "전체 목표"
  },
  "exercise_plan": {
    "weekly_goal": "주간 목표",
    "recommended_exercises": [
      {
        "name": "운동 이름",
        "type": "유산소/무산소/스트레칭",
        "frequency": "주 N회",
        "duration": "N분",
        "intensity": "강도",
        "description": "설명"
      }
    ],
    "body_part_focus": {
      "upper_body": ["상체 운동1", "상체 운동2"],
      "lower_body": ["하체 운동1", "하체 운동2"],
      "core": ["코어 운동1", "코어 운동2"]
    }
  },
  "diet_plan": {
    "daily_calorie_target": 칼로리_숫자,
    "meal_composition": {
      "breakfast": "아침 식단 구성",
      "lunch": "점심 식단 구성",
      "dinner": "저녁 식단 구성",
      "snacks": "간식 구성"
    },
    "macronutrient_ratio": {
      "carbs_percent": 탄수화물_비율,
      "protein_percent": 단백질_비율,
      "fat_percent": 지방_비율
    },
    "hydration_goal": "수분 섭취 목표",
    "foods_to_avoid": ["피해야 할 음식1", "피해야 할 음식2"]
  },
  "lifestyle_advice": {
    "sleep_recommendation": "수면 권장사항",
    "stress_management": "스트레스 관리",
    "daily_habits": ["일상 습관1", "일상 습관2"]
  }
}

반드시 유효한 JSON만 출력하세요. 추가 설명이나 마크다운 코드 블록 없이 순수 JSON만 반환하세요."""

        user_prompt = f"""다음 텍스트를 위 JSON 스키마에 맞게 변환하세요:

{natural_text}"""

        # LLM 호출
        json_text = client.generate_chat(system_prompt, user_prompt)

        if not json_text:
            raise Exception("JSON 변환 실패")

        # JSON 파싱
        json_start = json_text.find("{")
        json_end = json_text.rfind("}") + 1

        if json_start == -1 or json_end <= json_start:
            raise Exception("JSON 형식을 찾을 수 없습니다")

        json_str = json_text[json_start:json_end]
        parsed_json = json.loads(json_str)

        print(f"  ✓ Successfully parsed JSON")

        # Pydantic 검증 (선택사항)
        try:
            validated = LLMRecommendation(**parsed_json)
            state["json_response"] = validated.model_dump()
            print(f"  ✓ Pydantic validation passed")
        except ValidationError as e:
            print(f"  ! Pydantic validation failed, using raw JSON")
            state["json_response"] = parsed_json

        state["error"] = None

    except Exception as e:
        print(f"  ✗ Error: {type(e).__name__} - {str(e)}")
        state["error"] = f"Step 2 failed: {str(e)}"

    return state


def should_continue(state: PipelineState) -> str:
    """
    Conditional Edge: 다음 단계로 진행할지 결정

    Args:
        state: 현재 상태

    Returns:
        "convert_to_json": Step 2로 진행
        "end": 종료 (에러 발생 시)
    """
    if state.get("error"):
        print(f"  ! Stopping due to error: {state['error']}")
        return "end"

    if state.get("natural_language_response") and not state.get("json_response"):
        return "convert_to_json"

    return "end"


def create_langgraph_pipeline(client):
    """
    LangGraph 파이프라인 생성

    구조:
    [START] -> generate_natural_language -> convert_to_json -> [END]
             └─> (error) -> [END]

    Args:
        client: LLM 클라이언트

    Returns:
        실행 가능한 그래프
    """
    # StateGraph 생성
    workflow = StateGraph(PipelineState)

    # Node 추가
    # 각 노드는 함수이며, state를 받아 업데이트된 state를 반환
    workflow.add_node("generate_natural_language",
                      lambda state: generate_natural_language(state, client))
    workflow.add_node("convert_to_json",
                      lambda state: convert_to_json(state, client))

    # Entry point 설정
    workflow.set_entry_point("generate_natural_language")

    # Edge 추가
    # Conditional edge: 조건에 따라 다음 노드 결정
    workflow.add_conditional_edges(
        "generate_natural_language",  # 시작 노드
        should_continue,  # 조건 함수
        {
            "convert_to_json": "convert_to_json",  # 조건 결과 -> 다음 노드
            "end": END  # 종료
        }
    )

    # convert_to_json에서 END로
    workflow.add_edge("convert_to_json", END)

    # 그래프 컴파일
    app = workflow.compile()

    return app


def run_langgraph_pipeline(analysis_result: BodyAnalysisResult, client):
    """
    LangGraph 파이프라인 실행

    Args:
        analysis_result: 체형 분석 결과
        client: LLM 클라이언트

    Returns:
        최종 상태 (자연어 응답 + JSON 응답)
    """
    print("=" * 60)
    print("LangGraph 2-Step Pipeline")
    print("=" * 60)

    # 그래프 생성
    app = create_langgraph_pipeline(client)

    # 초기 상태 설정
    initial_state: PipelineState = {
        "analysis_result": analysis_result.model_dump(),
        "natural_language_response": None,
        "json_response": None,
        "error": None
    }

    # 그래프 실행
    # invoke()는 상태를 받아 그래프를 실행하고 최종 상태를 반환
    final_state = app.invoke(initial_state)

    print("=" * 60)

    if final_state.get("error"):
        print(f"Pipeline failed: {final_state['error']}")
        return None

    print("Pipeline completed successfully!")
    return final_state


# 사용 예시
if __name__ == "__main__":
    from claude_client import ClaudeClient
    from openai_client import OpenAIClient
    from rulebase_wrapper import full_body_analysis_from_inbody
    from models import BodyAnalysisResult, BasicInfo, Stage12Result
    import argparse
    from dotenv import load_dotenv

    load_dotenv()

    parser = argparse.ArgumentParser(description="LangGraph Pipeline Test")
    parser.add_argument("--model", default="claude-3-5-sonnet-20241022",
                       help="Model name (claude-* or gpt-*)")
    args = parser.parse_args()

    # 클라이언트 생성
    if args.model.startswith("claude-"):
        client = ClaudeClient(model=args.model)
        print(f"Using Claude: {args.model}")
    elif args.model.startswith("gpt-"):
        client = OpenAIClient(model=args.model)
        print(f"Using OpenAI: {args.model}")
    else:
        print("Error: Model must start with 'claude-' or 'gpt-'")
        exit(1)

    # 테스트용 분석 결과 (샘플)
    sample_result = {
        "basic_info": {
            "bmi": 23.5,
            "weight_kg": 70.0,
            "fat_rate": 25.0,
            "smm": 30.0
        },
        "stage1_2": {
            "bmi": 23.5,
            "bmi_category": "정상",
            "stage1_type": "보통",
            "stage2_type": "근육부족형"
        },
        "muscle_seg": {"left_arm": "보통", "right_arm": "보통"},
        "fat_seg": {"trunk": "높음"},
        "stage3": "상체 근력 강화 필요"
    }

    analysis = BodyAnalysisResult(
        basic_info=BasicInfo(**sample_result["basic_info"]),
        stage1_2=Stage12Result(**sample_result["stage1_2"]),
        muscle_seg=sample_result["muscle_seg"],
        fat_seg=sample_result["fat_seg"],
        stage3=sample_result["stage3"]
    )

    # 파이프라인 실행
    result = run_langgraph_pipeline(analysis, client)

    if result:
        print("\n=== Results ===")
        print(f"Natural Language Length: {len(result['natural_language_response']) if result['natural_language_response'] else 0}")
        print(f"JSON Keys: {list(result['json_response'].keys()) if result['json_response'] else 'None'}")

        # 결과 저장
        if result['json_response']:
            with open("langgraph_output.json", "w", encoding="utf-8") as f:
                json.dump(result['json_response'], f, ensure_ascii=False, indent=2)
            print("\nJSON saved to: langgraph_output.json")

        if result['natural_language_response']:
            with open("langgraph_output_natural.txt", "w", encoding="utf-8") as f:
                f.write(result['natural_language_response'])
            print("Natural language saved to: langgraph_output_natural.txt")
