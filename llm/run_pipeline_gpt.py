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
from prompt_generator_gpt import create_fitness_prompt
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


def generate_recommendations(analysis_result: BodyAnalysisResult, client: OllamaClient) -> dict | str | None:
    """
    LLM 추천 생성
    
    Args:
        analysis_result: 체형 분석 결과
        client: Ollama 클라이언트
        
    Returns:
        - LLMRecommendation dict (JSON 파싱 성공 시)
        - str (JSON 파싱 실패 시 원본 텍스트)
        - None (응답 없음)
    """
    system_prompt, user_prompt = create_fitness_prompt(analysis_result.model_dump())

    # 먼저 원본 텍스트 응답 받기
    raw_text = client.generate_chat(system_prompt, user_prompt)
    
    if not raw_text:
        return None
    
    # JSON 파싱 시도
    try:
        json_start = raw_text.find("{")
        json_end = raw_text.rfind("}") + 1

        if json_start != -1 and json_end > json_start:
            json_str = raw_text[json_start:json_end]

            # _fix_json 메서드가 있는 경우에만 사용
            if hasattr(client, '_fix_json'):
                json_str = client._fix_json(json_str)

            parsed = json.loads(json_str)

            # Pydantic 검증
            validated = LLMRecommendation(**parsed)
            return validated.model_dump()
    except Exception as e:
        # 모든 예외를 처리: JSON 파싱 오류, Pydantic 검증 오류, AttributeError 등
        print(f"[Info] JSON/Pydantic 검증 실패, 텍스트로 저장: {type(e).__name__} - {str(e)}")

    # JSON 실패 시 원본 텍스트 반환
    return raw_text


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
        if isinstance(recommendations, dict):
            if verbose:
                print("  Done! (JSON + Pydantic validated)")
        elif isinstance(recommendations, str):
            if verbose:
                print("  Done! (텍스트 응답 저장)")
    else:
        if verbose:
            print("  [Warning] No response from LLM")
    
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
    결과 저장
    - JSON: 분석 결과
    - MD: 텍스트 추천 (LLM 응답이 텍스트인 경우)
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    name = result.profile.name or "unknown"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = name + "_" + timestamp
    
    # 텍스트 응답이면 별도 .md 파일로 저장
    if isinstance(result.recommendations, str):
        md_filepath = output_path / (base_filename + "_recommendations.md")
        with open(md_filepath, "w", encoding="utf-8") as f:
            f.write("# " + name + " 운동/식단 추천\n\n")
            f.write(result.recommendations)
        print("  Recommendations saved: " + str(md_filepath))
        
        # JSON에는 md 파일 경로만 저장
        result_dict = result.model_dump()
        result_dict["recommendations"] = "See: " + str(md_filepath.name)
    else:
        result_dict = result.model_dump()
    
    # JSON 저장
    json_filepath = output_path / (base_filename + ".json")
    with open(json_filepath, "w", encoding="utf-8") as f:
        json.dump(result_dict, f, ensure_ascii=False, indent=2)
    
    return json_filepath


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
        
        # 추천 결과 출력
        if result.recommendations:
            recs = result.recommendations
            print("=== Recommendation Summary ===")
            
            if isinstance(recs, dict):
                # JSON 파싱 성공한 경우
                print("Body type: " + recs.get("body_analysis_summary", {}).get("body_type", "N/A"))
                print("Weekly goal: " + recs.get("exercise_plan", {}).get("weekly_goal", "N/A"))
                print("Daily calories: " + str(recs.get("diet_plan", {}).get("daily_calorie_target", "N/A")) + " kcal")
            elif isinstance(recs, str):
                # 텍스트 응답인 경우 - 처음 500자만 출력
                print("[텍스트 응답 - 전체 내용은 저장된 파일 확인]")
                preview = recs[:500].replace("\n", "\n  ")
                print("  " + preview + "...")
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
