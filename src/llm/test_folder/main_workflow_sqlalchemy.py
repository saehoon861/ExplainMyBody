#!/usr/bin/env python3
"""
ExplainMyBody - SQLAlchemy 버전
main_workflow.py와 동일하지만 database_sqlalchemy 사용
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# ⭐ 유일한 차이점: SQLAlchemy 사용
from database_sqlalchemy import DatabaseSQLAlchemy as Database

from workflow import InBodyAnalysisWorkflow, UserAuthManager
from claude_client import ClaudeClient
from openai_client import OpenAIClient
from ollama_client import OllamaClient

# 환경 변수 로드
load_dotenv()

# 나머지 코드는 main_workflow.py와 완전히 동일!
# (복사-붙여넣기)

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
    print("📋 LLM 분석 리포트 (SQLAlchemy 버전)")
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

    record = db.get_health_record(report['record_id'])
    username = record['measurements'].get('성별', 'user')

    generated_at = report['generated_at']
    if isinstance(generated_at, datetime):
        timestamp = generated_at.strftime('%Y-%m-%d_%H-%M-%S')
        generated_at_str = generated_at.strftime('%Y-%m-%d %H:%M:%S')
    else:
        timestamp = str(generated_at).replace(':', '').replace(' ', '_')
        generated_at_str = str(generated_at)

    filename = f"report_sqlalchemy_{report_id}_{timestamp}.txt"
    filepath = output_path / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("ExplainMyBody 분석 리포트 (SQLAlchemy)\n")
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
    parser = argparse.ArgumentParser(description="ExplainMyBody SQLAlchemy 버전")

    parser.add_argument("--username", type=str, help="사용자명")
    parser.add_argument("--email", type=str, help="이메일")
    parser.add_argument("--profile-id", type=int, help="Sample profile ID (1-10)")
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="Model name"
    )
    parser.add_argument("--output-dir", default="outputs", help="Output directory")
    parser.add_argument("--db-url", default=None, help="Database URL")
    parser.add_argument("--list-profiles", action="store_true", help="List profiles")
    parser.add_argument("--list-users", action="store_true", help="List users")

    args = parser.parse_args()

    # SQLAlchemy Database 초기화
    db = Database(args.db_url)
    print(f"✅ 데이터베이스 연결 (SQLAlchemy)")

    if args.list_users:
        print("\n=== 등록된 사용자 목록 ===")
        with db.get_session() as session:
            from db_models import User
            from sqlalchemy import select

            stmt = select(User)
            users = session.scalars(stmt).all()

            if users:
                for user in users:
                    print(f"  [{user.id}] {user.username} ({user.email}) - {user.created_at}")
            else:
                print("  등록된 사용자가 없습니다.")
        return

    profiles = load_sample_profiles()
    if args.list_profiles:
        print("\n=== 샘플 프로필 목록 ===")
        for profile in profiles:
            pid = profile.get("id", 0)
            name = profile.get("name", "")
            desc = profile.get("description", "")
            print(f"  [{pid}] {name} - {desc}")
        return

    if not args.username or not args.email:
        print("오류: --username과 --email을 입력해주세요.")
        sys.exit(1)

    if not args.profile_id:
        print("오류: --profile-id를 입력해주세요.")
        sys.exit(1)

    # LLM 클라이언트 생성
    if args.model.startswith("claude-"):
        client = ClaudeClient(model=args.model)
        print(f"🤖 LLM: Claude ({args.model})")
    elif args.model.startswith("gpt-"):
        client = OpenAIClient(model=args.model)
        print(f"🤖 LLM: OpenAI ({args.model})")
    else:
        client = OllamaClient(model=args.model)
        print(f"🤖 LLM: Ollama ({args.model})")

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

        display_report(db, report_id)
        save_report_to_file(db, report_id, args.output_dir)

        print(f"\n✨ 모든 작업이 완료되었습니다! (SQLAlchemy)")
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
