"""
InBody 분석 워크플로우
OCR 추출 -> 사용자 확인 -> Stage 계산 -> DB 저장 -> LLM 리포트 생성
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# rule_based_bodytype 모듈 임포트
sys.path.append(str(Path(__file__).parent / "rule_based_bodytype"))
from rule_based_bodytype.body_analysis.pipeline import BodyCompositionAnalyzer

from database import Database
from prompt_generator_measurements import create_fitness_prompt_from_measurements


class InBodyAnalysisWorkflow:
    """InBody 분석 전체 워크플로우 관리"""

    def __init__(self, db: Database, llm_client, model_version: str):
        """
        Args:
            db: Database 인스턴스
            llm_client: LLM 클라이언트 (claude_client, openai_client 등)
            model_version: 모델 버전 (예: "claude-3-5-sonnet-20241022")
        """
        self.db = db
        self.llm_client = llm_client
        self.model_version = model_version
        self.analyzer = BodyCompositionAnalyzer()

    def extract_ocr_data(self, sample_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        1단계: OCR 데이터 추출 (시뮬레이션)
        실제로는 이미지에서 OCR로 추출하지만, 지금은 sample_profile을 사용

        Args:
            sample_profile: sample_profiles.json의 프로필 데이터

        Returns:
            OCR 추출 데이터 (measurements 형식)
        """
        print("📸 1단계: OCR 데이터 추출...")

        # sample_profile을 measurements 형식으로 변환
        ocr_data = {
            "성별": sample_profile.get("sex", ""),
            "나이": sample_profile.get("age", 0),
            "신장": sample_profile.get("height_cm", 0.0),
            "체중": sample_profile.get("weight_kg", 0.0),
            "BMI": sample_profile.get("bmi", 0.0),
            "체지방률": sample_profile.get("fat_rate", 0.0),
            "골격근량": sample_profile.get("smm", 0.0),
            # 기본값 설정 (sample_profile에 없는 경우)
            "무기질": sample_profile.get("mineral", 3.5),
            "체수분": sample_profile.get("body_water", 40.0),
            "단백질": sample_profile.get("protein", 12.0),
            "체지방": sample_profile.get("body_fat", 15.0),
            "복부지방률": sample_profile.get("waist_hip_ratio", 0.85),
            "내장지방레벨": sample_profile.get("visceral_fat_level", 8),
            "기초대사량": sample_profile.get("basal_metabolic_rate", 1500),
            "비만도": sample_profile.get("obesity_degree", 100),
            "적정체중": sample_profile.get("ideal_weight", 65.0),
            "권장섭취열량": sample_profile.get("recommended_calorie", 2000),
            "체중조절": sample_profile.get("weight_control", 0.0),
            "지방조절": sample_profile.get("fat_control", 0.0),
            "근육조절": sample_profile.get("muscle_control", 0.0),
            # 부위별 데이터
            "근육_부위별등급": sample_profile.get("muscle_seg", {}),
            "체지방_부위별등급": sample_profile.get("fat_seg", {})
        }

        print(f"  ✓ OCR 데이터 추출 완료: {ocr_data['성별']}, {ocr_data['나이']}세")
        return ocr_data

    def get_user_confirmation(self, ocr_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        2단계: 사용자에게 OCR 데이터 확인 받기 (시뮬레이션)
        실제로는 Frontend에서 사용자가 데이터를 확인하고 수정

        Args:
            ocr_data: OCR 추출 데이터

        Returns:
            사용자가 확인/수정한 데이터
        """
        print("✅ 2단계: 사용자 데이터 확인...")
        print("  (시뮬레이션: 사용자가 데이터를 확인했다고 가정)")

        # 실제로는 여기서 사용자 입력을 받아 수정
        # 지금은 그대로 반환
        confirmed_data = ocr_data.copy()

        print("  ✓ 사용자 확인 완료")
        return confirmed_data

    def calculate_stages(self, ocr_data: Dict[str, Any]) -> Dict[str, str]:
        """
        3단계: Stage 계산 (rule_based_bodytype 알고리즘 사용)

        Args:
            ocr_data: OCR 추출 데이터

        Returns:
            Stage 분석 결과 {"stage2": "...", "stage3": "..."}
        """
        print("🧮 3단계: Stage 분석 계산...")

        # rule_based_bodytype의 입력 형식으로 변환
        body_data = {
            "sex": ocr_data["성별"],
            "age": ocr_data["나이"],
            "height_cm": ocr_data["신장"],
            "weight_kg": ocr_data["체중"],
            "bmi": ocr_data["BMI"],
            "fat_rate": ocr_data["체지방률"],
            "smm": ocr_data["골격근량"],
            "muscle_seg": ocr_data["근육_부위별등급"],
            "fat_seg": ocr_data["체지방_부위별등급"]
        }

        # BodyCompositionAnalyzer로 분석
        stage_results = self.analyzer.analyze_full_pipeline(body_data)

        print(f"  ✓ Stage 2: {stage_results['stage2']}")
        print(f"  ✓ Stage 3: {stage_results['stage3']}")

        return stage_results

    def merge_data(
        self,
        confirmed_ocr_data: Dict[str, Any],
        stage_results: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        4단계: OCR 데이터와 Stage 결과 병합

        Args:
            confirmed_ocr_data: 사용자 확인 완료 OCR 데이터
            stage_results: Stage 분석 결과

        Returns:
            병합된 measurements 데이터
        """
        print("🔄 4단계: 데이터 병합...")

        full_measurements = confirmed_ocr_data.copy()
        full_measurements["stage2_근육보정체형"] = stage_results["stage2"]
        full_measurements["stage3_상하체밸런스"] = stage_results["stage3"]

        print("  ✓ 데이터 병합 완료")
        return full_measurements

    def save_health_record(
        self,
        user_id: int,
        measurements: Dict[str, Any],
        source: str = "manual"
    ) -> int:
        """
        5단계: health_records에 저장

        Args:
            user_id: 사용자 ID
            measurements: 병합된 measurements 데이터
            source: 데이터 소스 (예: "inbody_ocr", "manual")

        Returns:
            생성된 record_id
        """
        print("💾 5단계: health_records 저장...")

        record_id = self.db.save_health_record(
            user_id=user_id,
            measurements=measurements,
            source=source
        )

        print(f"  ✓ health_record 저장 완료 (ID: {record_id})")
        return record_id

    def generate_llm_report(self, user_id: int, record_id: int) -> int:
        """
        6단계: LLM 분석 리포트 생성

        Args:
            user_id: 사용자 ID
            record_id: health_record ID

        Returns:
            생성된 report_id
        """
        print("🤖 6단계: LLM 분석 리포트 생성...")

        # health_record에서 measurements 추출
        record = self.db.get_health_record(record_id)
        if not record:
            raise ValueError(f"health_record {record_id}를 찾을 수 없습니다")

        measurements = record['measurements']

        # 프롬프트 생성
        system_prompt, user_prompt = create_fitness_prompt_from_measurements(measurements)

        # LLM 호출
        print("  - LLM 호출 중...")
        llm_output = self.llm_client.generate_chat(system_prompt, user_prompt)

        if not llm_output:
            raise ValueError("LLM 응답을 받지 못했습니다")

        print(f"  ✓ LLM 응답 생성 완료 ({len(llm_output)} 글자)")

        # analysis_reports에 저장
        report_id = self.db.save_analysis_report(
            user_id=user_id,
            record_id=record_id,
            llm_output=llm_output,
            model_version=self.model_version
        )

        print(f"  ✓ 분석 리포트 저장 완료 (ID: {report_id})")
        return report_id

    def run_full_workflow(
        self,
        user_id: int,
        sample_profile: Dict[str, Any],
        source: str = "manual"
    ) -> Dict[str, int]:
        """
        전체 워크플로우 실행

        Args:
            user_id: 사용자 ID
            sample_profile: 샘플 프로필 데이터
            source: 데이터 소스

        Returns:
            {"record_id": int, "report_id": int}
        """
        print("=" * 60)
        print(f"InBody 분석 워크플로우 시작 (User ID: {user_id})")
        print("=" * 60)

        # 1단계: OCR 추출
        ocr_data = self.extract_ocr_data(sample_profile)

        # 2단계: 사용자 확인
        confirmed_data = self.get_user_confirmation(ocr_data)

        # 3단계: Stage 계산
        stage_results = self.calculate_stages(confirmed_data)

        # 4단계: 데이터 병합
        full_measurements = self.merge_data(confirmed_data, stage_results)

        # 5단계: health_records 저장
        record_id = self.save_health_record(user_id, full_measurements, source)

        # 6단계: LLM 분석 리포트 생성
        report_id = self.generate_llm_report(user_id, record_id)

        print("=" * 60)
        print("✨ 워크플로우 완료!")
        print(f"  - Record ID: {record_id}")
        print(f"  - Report ID: {report_id}")
        print("=" * 60)

        return {
            "record_id": record_id,
            "report_id": report_id
        }


class UserAuthManager:
    """사용자 인증 관리"""

    def __init__(self, db: Database):
        self.db = db

    def register_or_login(self, username: str, email: str) -> Dict[str, Any]:
        """
        회원가입 또는 로그인

        Args:
            username: 사용자명
            email: 이메일

        Returns:
            사용자 정보 딕셔너리
        """
        # 이메일로 기존 사용자 확인
        user = self.db.get_user_by_email(email)

        if user:
            # 기존 사용자 - 로그인
            print(f"✅ 로그인 성공: {user['username']} ({user['email']})")
            return user
        else:
            # 신규 사용자 - 회원가입
            user_id = self.db.create_user(username, email)
            user = self.db.get_user_by_id(user_id)
            print(f"🎉 회원가입 완료: {username} ({email})")
            return user
