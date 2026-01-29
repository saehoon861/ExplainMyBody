#!/usr/bin/env python3
"""
직접 InBody 데이터를 입력하여 분석 실행
"""

from database import Database
from workflow import InBodyAnalysisWorkflow, UserAuthManager
from openai_client import OpenAIClient
from dotenv import load_dotenv

load_dotenv()

# === 여기에 InBody 데이터 입력 ===
my_inbody_data = {
    "sex": "남자",
    "age": 30,
    "height_cm": 175.0,
    "weight_kg": 70.0,
    "bmi": 22.9,
    "fat_rate": 18.5,
    "smm": 33.0,
    "muscle_seg": {
        "왼팔": 3.0,
        "오른팔": 3.1,
        "몸통": 24.0,
        "왼다리": 9.0,
        "오른다리": 9.2
    },
    "fat_seg": {
        "왼팔": 0.8,
        "오른팔": 0.9,
        "몸통": 8.0,
        "왼다리": 2.0,
        "오른다리": 2.1
    }
}

# === 사용자 정보 ===
username = "홍길동"
email = "hong@example.com"

# === LLM 모델 선택 ===
model = "gpt-4o-mini"  # 또는 "claude-3-5-sonnet-20241022"

# === 실행 ===
if __name__ == "__main__":
    # DB 연결
    db = Database()
    print("✅ 데이터베이스 연결 완료")

    # 사용자 등록/로그인
    auth_manager = UserAuthManager(db)
    user = auth_manager.register_or_login(username, email)
    user_id = user['id']
    print(f"✅ 사용자: {username} (ID: {user_id})")

    # LLM 클라이언트
    client = OpenAIClient(model=model)
    print(f"🤖 LLM: {model}")

    # 워크플로우 실행
    workflow = InBodyAnalysisWorkflow(
        db=db,
        llm_client=client,
        model_version=model
    )

    print("\n🚀 분석 시작...\n")

    result = workflow.run_full_workflow(
        user_id=user_id,
        sample_profile=my_inbody_data,
        source="my_inbody_ocr"
    )

    # 결과 출력
    report = db.get_analysis_report(result['report_id'])

    print("\n" + "=" * 60)
    print("📋 LLM 분석 리포트")
    print("=" * 60)
    print(report['llm_output'])
    print("=" * 60)

    print(f"\n✨ 완료!")
    print(f"  - Health Record ID: {result['record_id']}")
    print(f"  - Analysis Report ID: {result['report_id']}")
