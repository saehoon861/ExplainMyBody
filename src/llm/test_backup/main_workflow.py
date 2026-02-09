#!/usr/bin/env python3
"""
ExplainMyBody - 통합 워크플로우 메인 실행 파일
회원가입/로그인 -> OCR 추출 -> Stage 계산 -> DB 저장 -> LLM 리포트 생성
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from database import Database
from workflow import InBodyAnalysisWorkflow, UserAuthManager
from claude_client import ClaudeClient
from openai_client import OpenAIClient
from ollama_client import OllamaClient

# 환경 변수 로드
load_dotenv()


def load_sample_profiles(path="sample_profiles.json"):
    """샘플 프로필 로드"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def display_report(db: Database, report_id: int):
    """리포트 출력"""
    report = db.get_analysis_report(report_id)
    if not report:
        print("리포트를 찾을 수 없습니다.")
        return

    print("\n" + "=" * 60)
    print("📋 LLM 분석 리포트")
    print("=" * 60)
    print(f"Model: {report['model_version']}")
    print(f"Generated at: {report['generated_at']}")
    print("-" * 60)
    print(report['llm_output'])
    print("=" * 60)


def save_report_to_file(db: Database, report_id: int, output_dir: str = "outputs"):
    """리포트를 파일로 저장"""
    report = db.get_analysis_report(report_id)
    if not report:
        print("리포트를 찾을 수 없습니다.")
        return

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # health_record 정보 가져오기
    record = db.get_health_record(report['record_id'])
    username = record['measurements'].get('성별', 'user')
    
    # generated_at이 datetime 객체인 경우 문자열로 변환
    generated_at = report['generated_at']
    if isinstance(generated_at, datetime):
        timestamp = generated_at.strftime('%Y-%m-%d_%H-%M-%S')
        generated_at_str = generated_at.strftime('%Y-%m-%d %H:%M:%S')
    else:
        timestamp = str(generated_at).replace(':', '').replace(' ', '_')
        generated_at_str = str(generated_at)

    filename = f"report_{report_id}_{timestamp}.txt"
    filepath = output_path / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("ExplainMyBody 분석 리포트\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Report ID: {report_id}\n")
        f.write(f"Model: {report['model_version']}\n")
        f.write(f"Generated at: {generated_at_str}\n\n")
        f.write("-" * 60 + "\n\n")
        f.write(report['llm_output'])
        f.write("\n\n" + "=" * 60 + "\n")

    print(f"\n💾 리포트 저장 완료: {filepath}")
    return filepath


def main():
    parser = argparse.ArgumentParser(description="ExplainMyBody 통합 워크플로우")

    # 사용자 정보
    parser.add_argument("--username", type=str, help="사용자명")
    parser.add_argument("--email", type=str, help="이메일")

    # 프로필 선택
    parser.add_argument("--profile-id", type=int, help="Sample profile ID (1-10)")

    # LLM 모델 선택
    parser.add_argument(
        "--model",
        default="gpt-4.1",
        help="Model name (ollama: qwen3:14b, claude: claude-3-5-sonnet-20241022, openai: gpt-4o-mini)"
    )

    # 기타 옵션
    parser.add_argument("--output-dir", default="outputs", help="Output directory")
    parser.add_argument("--db-url", default=None, help="Database connection URL (PostgreSQL)")
    parser.add_argument("--list-profiles", action="store_true", help="List available profiles")
    parser.add_argument("--list-users", action="store_true", help="List registered users")

    args = parser.parse_args()

    # 데이터베이스 초기화
    db = Database(args.db_url)
    db_info = args.db_url if args.db_url else "환경변수 DATABASE_URL"
    print(f"✅ 데이터베이스 연결: {db_info}")

    # 사용자 목록 출력
    if args.list_users:
        print("\n=== 등록된 사용자 목록 ===")
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, email, created_at FROM users")
            users = cursor.fetchall()
            if users:
                for user in users:
                    print(f"  [{user['id']}] {user['username']} ({user['email']}) - {user['created_at']}")
            else:
                print("  등록된 사용자가 없습니다.")
        return

    # 프로필 목록 출력
    profiles = load_sample_profiles()
    if args.list_profiles:
        print("\n=== 샘플 프로필 목록 ===")
        for profile in profiles:
            pid = profile.get("id", 0)
            name = profile.get("name", "")
            desc = profile.get("description", "")
            print(f"  [{pid}] {name} - {desc}")
        return

    # 사용자 정보 확인
    if not args.username or not args.email:
        print("오류: --username과 --email을 입력해주세요.")
        print("\n사용 예시:")
        print("  python main_workflow.py --username '홍길동' --email 'hong@example.com' --profile-id 1")
        sys.exit(1)

    # 프로필 ID 확인
    if not args.profile_id:
        print("오류: --profile-id를 입력해주세요.")
        print("\n사용 가능한 프로필:")
        for p in profiles:
            print(f"  [{p['id']}] {p['name']} - {p['description']}")
        sys.exit(1)

    # 모델 클라이언트 생성
    if args.model.startswith("claude-"):
        client = ClaudeClient(model=args.model)
        print(f"🤖 LLM: Claude ({args.model})")
    elif args.model.startswith("gpt-"):
        client = OpenAIClient(model=args.model)
        print(f"🤖 LLM: OpenAI ({args.model})")
    else:
        client = OllamaClient(model=args.model)
        if not client.check_connection():
            print("오류: Ollama 서버에 연결할 수 없습니다.")
            print("실행: ollama serve")
            sys.exit(1)
        print(f"🤖 LLM: Ollama ({args.model})")

    # API 연결 확인
    if args.model.startswith("claude-") or args.model.startswith("gpt-"):
        try:
            if not client.check_connection():
                provider = "Claude" if args.model.startswith("claude-") else "OpenAI"
                print(f"오류: {provider} API에 연결할 수 없습니다.")
                print("API 키를 .env 파일에서 확인하세요.")
                sys.exit(1)
            print("✅ API 연결 성공")
        except Exception as e:
            print(f"오류: {e}")
            sys.exit(1)

    # 회원가입 / 로그인
    auth_manager = UserAuthManager(db)
    user = auth_manager.register_or_login(args.username, args.email)
    user_id = user['id']

    # 프로필 선택
    profile = next((p for p in profiles if p.get("id") == args.profile_id), None)
    if not profile:
        print(f"오류: Profile ID {args.profile_id}를 찾을 수 없습니다.")
        sys.exit(1)

    print(f"\n📊 선택된 프로필: {profile['name']} ({profile['description']})")

    # 워크플로우 실행
    workflow = InBodyAnalysisWorkflow(
        db=db,
        llm_client=client,
        model_version=args.model
    )

    try:
        result = workflow.run_full_workflow(
            user_id=user_id,
            sample_profile=profile,
            source="sample_profile"
        )

        record_id = result['record_id']
        report_id = result['report_id']

        # 리포트 출력
        display_report(db, report_id)

        # 리포트 파일 저장
        save_report_to_file(db, report_id, args.output_dir)

        print(f"\n✨ 모든 작업이 완료되었습니다!")
        print(f"  - User ID: {user_id}")
        print(f"  - Health Record ID: {record_id}")
        print(f"  - Analysis Report ID: {report_id}")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
