#!/usr/bin/env python3
"""
ExplainMyBody - Main Pipeline with Pydantic
InBody Data -> Rule-based Analysis -> LLM Recommendations

Pydantic 적용:
1. 입력 검증: InBodyProfile 모델로 프로필 데이터 유효성 검사
2. 분석 결과: BodyAnalysisResult 모델로 규칙기반 결과 구조화
3. LLM 출력: LLMRecommendation 모델로 JSON 응답 파싱 및 검증
4. 최종 결과: PipelineResult 모델로 전체 결과 통합
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from pydantic import ValidationError

from rulebase_wrapper import full_body_analysis_from_inbody
from ollama_client import OllamaClient
from claude_client import ClaudeClient
from openai_client import OpenAIClient
from prompt_generator import create_fitness_prompt
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv()
from models import (
    InBodyProfile,
    BodyAnalysisResult,
    BasicInfo,
    Stage12Result,
    LLMRecommendation,
    PipelineResult,
    ProfileSummary
)


def load_sample_profiles(path="sample_profiles.json") -> list[InBodyProfile]:
    """
    샘플 프로필 로드 및 Pydantic 검증
    
    Returns:
        검증된 InBodyProfile 객체 리스트
    """
    with open(path, "r", encoding="utf-8") as f:
        raw_profiles = json.load(f)
    
    validated_profiles = []
    for raw in raw_profiles:
        try:
            profile = InBodyProfile(**raw)
            validated_profiles.append(profile)
        except ValidationError as e:
            print("Profile validation error for " + str(raw.get("name", "unknown")) + ": " + str(e))
    
    return validated_profiles


def analyze_profile(profile: InBodyProfile) -> BodyAnalysisResult:
    """
    규칙기반 분석 실행 및 Pydantic 모델로 변환
    
    Args:
        profile: 검증된 InBodyProfile 객체
        
    Returns:
        BodyAnalysisResult Pydantic 모델
    """
    # dict 형태로 변환하여 기존 함수 호출
    result = full_body_analysis_from_inbody(
        bmi=profile.bmi,
        weight_kg=profile.weight_kg,
        fat_rate=profile.fat_rate,
        smm=profile.smm,
        smm_cat=None,
        muscle_input=profile.muscle_seg,
        fat_input=profile.fat_seg,
        sex=profile.sex,
        age=profile.age
    )
    
    # Pydantic 모델로 변환
    return BodyAnalysisResult(
        basic_info=BasicInfo(**result["basic_info"]),
        stage1_2=Stage12Result(**result["stage1_2"]),
        muscle_seg=result["muscle_seg"],
        fat_seg=result["fat_seg"],
        stage3=result["stage3"]
    )


def generate_recommendations(analysis_result: BodyAnalysisResult, client: OllamaClient) -> LLMRecommendation | None:
    """
    LLM 추천 생성 및 Pydantic 모델로 검증
    
    Args:
        analysis_result: 체형 분석 결과
        client: Ollama 클라이언트
        
    Returns:
        검증된 LLMRecommendation 또는 None
    """
    # Pydantic 모델을 dict로 변환하여 프롬프트 생성
    prompt = create_fitness_prompt(analysis_result.model_dump())
    raw_response = client.generate_json(prompt)
    
    if not raw_response:
        return None
    
    try:
        # LLM 응답을 Pydantic 모델로 검증
        return LLMRecommendation(**raw_response)
    except Exception as e:
        # 모든 예외를 처리: Pydantic 검증 오류, 타입 오류 등
        print("[Warning] LLM response validation failed: " + type(e).__name__ + " - " + str(e))
        return None


def run_pipeline(profile: InBodyProfile, client: OllamaClient, verbose: bool = True) -> PipelineResult:
    """
    전체 파이프라인 실행
    
    Args:
        profile: 검증된 InBodyProfile
        client: Ollama 클라이언트
        verbose: 상세 출력 여부
        
    Returns:
        PipelineResult Pydantic 모델
    """
    if verbose:
        print("=" * 60)
        name = profile.name
        desc = profile.description or ""
        print("Profile: " + name + " (" + desc + ")")
        print("=" * 60)
    
    # Step 1: 규칙기반 분석
    if verbose:
        print("[1/2] Rule-based body analysis...")
    
    analysis = analyze_profile(profile)
    
    if verbose:
        s12 = analysis.stage1_2
        print("  BMI: " + str(s12.bmi) + " (" + s12.bmi_category + ")")
        print("  Stage1: " + s12.stage1_type)
        print("  Stage2: " + s12.stage2_type)
        print("  Stage3: " + analysis.stage3)
    
    # Step 2: LLM 추천 생성
    if verbose:
        print("[2/2] LLM recommendation generation...")
    
    recommendations = generate_recommendations(analysis, client)
    
    if recommendations:
        if verbose:
            print("  Done! (Pydantic validated)")
    else:
        if verbose:
            print("  [Warning] Failed or validation error")
    
    # PipelineResult 모델로 통합
    return PipelineResult(
        profile=ProfileSummary(
            name=profile.name,
            sex=profile.sex,
            age=profile.age,
            height_cm=profile.height_cm,
            weight_kg=profile.weight_kg
        ),
        analysis=analysis,
        recommendations=recommendations,
        generated_at=datetime.now().isoformat()
    )


def save_result(result: PipelineResult, output_dir: str = "outputs") -> Path:
    """
    결과 저장 (Pydantic model_dump 사용)
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    name = result.profile.name or "unknown"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = name + "_" + timestamp + ".json"
    
    filepath = output_path / filename
    
    # Pydantic model_dump()로 JSON 직렬화
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, ensure_ascii=False, indent=2)
    
    return filepath


def main():
    parser = argparse.ArgumentParser(description="ExplainMyBody Pipeline (Pydantic)")
    parser.add_argument("--profile-id", type=int, help="Sample profile ID (1-10)")
    parser.add_argument("--all", action="store_true", help="Process all profiles")
    parser.add_argument("--model", default="qwen3:14b", help="Model name (ollama: qwen3:14b, claude: claude-3-5-sonnet-20241022, openai: gpt-4o-mini)")
    parser.add_argument("--output-dir", default="outputs", help="Output directory")
    parser.add_argument("--quiet", action="store_true", help="Suppress verbose output")
    parser.add_argument("--max-tokens", type=int, default=8192, help="Max tokens for LLM")

    args = parser.parse_args()

    # 모델명에 따라 적절한 클라이언트 선택
    if args.model.startswith("claude-"):
        # Claude API 사용
        client = ClaudeClient(model=args.model, max_tokens=args.max_tokens)
        print("Using Claude API (model: " + args.model + ")")
    elif args.model.startswith("gpt-"):
        # OpenAI API 사용
        client = OpenAIClient(model=args.model, max_tokens=args.max_tokens)
        print("Using OpenAI API (model: " + args.model + ")")
    else:
        # Ollama (로컬 모델) 사용
        client = OllamaClient(model=args.model, max_tokens=args.max_tokens)
        if not client.check_connection():
            print("Error: Cannot connect to Ollama server.")
            print("Run: ollama serve")
            sys.exit(1)
        print("Using Ollama (model: " + args.model + ")")

    # API 연결 확인 (Claude/OpenAI는 check_connection이 API 호출하므로 선택적)
    if args.model.startswith("claude-") or args.model.startswith("gpt-"):
        try:
            if not client.check_connection():
                print("Error: Cannot connect to " + ("Claude" if args.model.startswith("claude-") else "OpenAI") + " API.")
                print("Check your API key in .env file")
                sys.exit(1)
            print("API connection successful")
        except Exception as e:
            print("Error: " + str(e))
            sys.exit(1)
    
    # Pydantic으로 검증된 프로필 로드
    profiles = load_sample_profiles()
    print("Loaded " + str(len(profiles)) + " validated profiles")
    
    if args.all:
        print("Processing " + str(len(profiles)) + " profiles...")
        for profile in profiles:
            try:
                result = run_pipeline(profile, client, verbose=not args.quiet)
                filepath = save_result(result, args.output_dir)
                print("  Saved: " + str(filepath))
            except Exception as e:
                print("  Error: " + str(e))
                
    elif args.profile_id:
        profile = next((p for p in profiles if p.id == args.profile_id), None)
        if not profile:
            print("Error: Profile ID " + str(args.profile_id) + " not found.")
            sys.exit(1)
        
        result = run_pipeline(profile, client, verbose=not args.quiet)
        filepath = save_result(result, args.output_dir)
        print("Result saved: " + str(filepath))
        
        # Pydantic 모델 속성으로 직접 접근
        if result.recommendations:
            recs = result.recommendations
            print("=== Recommendation Summary ===")
            print("Body type: " + recs.body_analysis_summary.body_type)
            print("Weekly goal: " + recs.exercise_plan.weekly_goal)
            print("Daily calories: " + str(recs.diet_plan.daily_calorie_target) + " kcal")
    else:
        print("=== Sample Profiles (Pydantic Validated) ===")
        for p in profiles:
            pid = p.id or 0
            pname = p.name
            pdesc = p.description or ""
            print("  [" + str(pid).rjust(2) + "] " + pname.ljust(6) + " - " + pdesc)
        print()
        print("Usage:")
        print("  python run_pipeline.py --profile-id 1")
        print("  python run_pipeline.py --all")


if __name__ == "__main__":
    main()
