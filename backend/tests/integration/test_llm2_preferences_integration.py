"""
LLM2 통합 테스트: 선호도와 건강 특이사항 조합에 따른 주간 계획 생성 검증

동일한 InBody 데이터를 사용하되, 다양한 preferences와 health_specifics 조합으로
LLM2가 생성하는 주간 계획이 적절하게 맞춤화되는지 테스트합니다.
"""

import pytest
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple
from unittest.mock import Mock, patch

from services.llm.llm_service import LLMService
from services.common.health_service import HealthService
from schemas.llm import GoalPlanInput, GoalPlanRequest


# 테스트 결과 저장 디렉토리
TEST_RESULTS_DIR = Path(__file__).parent / "llm2_test_results"


# 공통 InBody 데이터 (30세 남성, 약간 과체중)
COMMON_INBODY_DATA: Dict[str, Any] = {
    "기본정보": {
        "신장": 175.0,
        "연령": 30,
        "성별": "남성"
    },
    "체성분": {
        "체수분": 42.5,
        "단백질": 12.0,
        "무기질": 4.2,
        "체지방": 18.5
    },
    "체중관리": {
        "체중": 78.0,
        "골격근량": 33.5,
        "체지방량": 18.5,
        "적정체중": 70.0,
        "체중조절": -8.0,
        "지방조절": -10.5,
        "근육조절": 2.5
    },
    "비만분석": {
        "BMI": 25.5,
        "체지방률": 23.7,
        "복부지방률": 0.90,
        "내장지방레벨": 8,
        "비만도": 111
    },
    "연구항목": {
        "제지방량": 59.5,
        "기초대사량": 1680,
        "권장섭취열량": 2450
    },
    "부위별근육분석": {
        "왼쪽팔": "표준",
        "오른쪽팔": "표준",
        "복부": "부족",
        "왼쪽하체": "표준",
        "오른쪽하체": "표준"
    },
    "부위별체지방분석": {
        "왼쪽팔": "표준",
        "오른쪽팔": "표준",
        "복부": "표준이상",
        "왼쪽하체": "표준",
        "오른쪽하체": "표준"
    }
}


# 테스트 케이스 정의
TEST_CASES = [
    {
        "case_id": 1,
        "name": "홈트레이닝 + 무릎 통증",
        "filename": "case_1_home_workout_knee_pain.md",
        "preferences": "홈트레이닝 선호, 덤벨과 매트만 사용 가능",
        "health_specifics": "무릎 통증이 있어 스쿼트나 런지 같은 무릎에 부담가는 운동 제한",
        "goal_type": "체중 감량",
        "goal_description": "3개월 내 5kg 감량",
        "expected_keywords": {
            "include": ["홈", "덤벨", "매트", "집"],
            "exclude": ["스쿼트", "런지", "점프"]
        }
    },
    {
        "case_id": 2,
        "name": "헬스장 + 허리 디스크",
        "filename": "case_2_gym_back_disc.md",
        "preferences": "헬스장 이용 가능, 웨이트 트레이닝 선호",
        "health_specifics": "허리 디스크가 있어 데드리프트나 과도한 허리 굴곡 운동 금지",
        "goal_type": "근육 증가",
        "goal_description": "근육량 3kg 증가",
        "expected_keywords": {
            "include": ["헬스장", "웨이트", "벤치프레스"],
            "exclude": ["데드리프트", "굿모닝"]
        }
    },
    {
        "case_id": 3,
        "name": "수영 + 알레르기",
        "filename": "case_3_swimming_allergies.md",
        "preferences": "수영을 좋아하고 수영장 접근 가능",
        "health_specifics": "유제품 알레르기, 견과류 알레르기",
        "goal_type": "체력 향상",
        "goal_description": "전반적인 체력 및 심폐 지구력 향상",
        "expected_keywords": {
            "include": ["수영", "유산소", "물"],
            "exclude": ["우유", "치즈", "요거트", "아몬드", "호두"]
        }
    },
    {
        "case_id": 4,
        "name": "러닝 + 고혈압",
        "filename": "case_4_running_hypertension.md",
        "preferences": "야외 러닝 선호, 유산소 운동 위주",
        "health_specifics": "고혈압 약 복용 중, 과도한 고강도 운동 주의",
        "goal_type": "체중 감량",
        "goal_description": "건강한 체중 감량 및 혈압 관리",
        "expected_keywords": {
            "include": ["러닝", "조깅", "유산소", "저강도", "중강도"],
            "exclude": ["고강도", "HIIT", "전력질주"]
        }
    },
    {
        "case_id": 5,
        "name": "요가/필라테스 + 임신",
        "filename": "case_5_yoga_pregnancy.md",
        "preferences": "요가와 필라테스 선호, 저강도 운동",
        "health_specifics": "임신 2기, 복부 압박 운동과 누운 자세 제한",
        "goal_type": "체력 유지",
        "goal_description": "임신 중 건강한 체중 유지 및 체력 관리",
        "expected_keywords": {
            "include": ["요가", "필라테스", "스트레칭", "저강도"],
            "exclude": ["복근", "윗몸일으키기", "플랭크"]
        }
    },
    {
        "case_id": 6,
        "name": "기본 케이스 (선호도/특이사항 없음)",
        "filename": "case_6_baseline.md",
        "preferences": None,
        "health_specifics": None,
        "goal_type": "체중 감량",
        "goal_description": "건강한 체중 감량",
        "expected_keywords": {
            "include": ["운동", "식단"],
            "exclude": []
        }
    }
]


class TestLLM2PreferencesIntegration:
    """LLM2 선호도 및 건강 특이사항 통합 테스트"""

    @classmethod
    def setup_class(cls):
        """테스트 클래스 초기화"""
        # 결과 저장 디렉토리 생성
        TEST_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        print(f"\n테스트 결과 저장 디렉토리: {TEST_RESULTS_DIR}")

    def _create_goal_plan_input(
        self,
        preferences: str,
        health_specifics: str,
        goal_type: str,
        goal_description: str
    ) -> GoalPlanInput:
        """테스트용 GoalPlanInput 생성"""
        return GoalPlanInput(
            user_goal_type=goal_type,
            user_goal_description=goal_description,
            preferences=preferences,
            health_specifics=health_specifics,
            record_id=999,  # 테스트용 더미 ID
            user_id=999,
            measured_at=datetime.now(),
            measurements=COMMON_INBODY_DATA,
            status_analysis_result="테스트용 분석 결과",
            body_type1="비만형",
            body_type2="표준형",
            user_profile={
                "body_type1": "비만형",
                "body_type2": "표준형",
                "health_specifics": health_specifics or "",
                "preferences": preferences or ""
            },
            available_days_per_week=5,
            available_time_per_session=60
        )

    def _save_plan_result(
        self,
        filename: str,
        case_info: Dict[str, Any],
        plan_text: str,
        model_version: str
    ):
        """생성된 계획을 마크다운 파일로 저장"""
        filepath = TEST_RESULTS_DIR / filename
        
        content = f"""# LLM2 테스트 결과 - {case_info['name']}

## 테스트 정보
- **케이스 ID**: {case_info['case_id']}
- **테스트 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **모델 버전**: {model_version}

## 입력 조건
- **목표 유형**: {case_info['goal_type']}
- **목표 설명**: {case_info['goal_description']}
- **운동 선호도**: {case_info['preferences'] or '없음'}
- **건강 특이사항**: {case_info['health_specifics'] or '없음'}

## 생성된 주간 계획

{plan_text}

---
*이 파일은 자동 생성되었습니다.*
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 결과 저장 완료: {filepath}")

    def _verify_plan_content(
        self,
        plan_text: str,
        expected_keywords: Dict[str, List[str]]
    ) -> Tuple[bool, List[str]]:
        """
        계획 내용이 예상 키워드를 포함/제외하는지 검증
        
        Returns:
            (pass/fail, 실패 이유 리스트)
        """
        plan_lower = plan_text.lower()
        failures = []
        
        # 포함되어야 할 키워드 확인
        for keyword in expected_keywords.get("include", []):
            if keyword.lower() not in plan_lower:
                failures.append(f"포함되어야 할 키워드 누락: '{keyword}'")
        
        # 제외되어야 할 키워드 확인
        for keyword in expected_keywords.get("exclude", []):
            if keyword.lower() in plan_lower:
                failures.append(f"제외되어야 할 키워드 포함됨: '{keyword}'")
        
        return len(failures) == 0, failures

    def _generate_summary(self, results: List[Dict[str, Any]]):
        """테스트 결과 요약 파일 생성"""
        summary_path = TEST_RESULTS_DIR / "summary.md"
        
        # 테이블 행 생성
        table_rows = []
        for result in results:
            case_id = result['case_id']
            name = result['name']
            passed = result['passed']
            status = "✅ Pass" if passed else "❌ Fail"
            
            # 키워드 검증 결과 요약
            if passed:
                keyword_summary = "모든 키워드 조건 충족"
            else:
                keyword_summary = "; ".join(result['failures'][:2])  # 최대 2개만 표시
                if len(result['failures']) > 2:
                    keyword_summary += f" (외 {len(result['failures']) - 2}개)"
            
            table_rows.append(f"| {case_id} | {name} | {status} | {keyword_summary} |")
        
        # 전체 통계
        total = len(results)
        passed = sum(1 for r in results if r['passed'])
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        content = f"""# LLM2 통합 테스트 결과 요약

**테스트 실행 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 전체 통계
- **총 테스트 케이스**: {total}개
- **통과**: {passed}개
- **실패**: {failed}개
- **통과율**: {pass_rate:.1f}%

## 케이스별 검증 결과

| Case | 시나리오 | 검증 결과 | 주요 키워드 반영 여부 |
|------|----------|-----------|---------------------|
{chr(10).join(table_rows)}

## 상세 결과

"""
        
        # 각 케이스별 상세 결과
        for result in results:
            content += f"""### Case {result['case_id']}: {result['name']}

- **상태**: {"✅ 통과" if result['passed'] else "❌ 실패"}
- **결과 파일**: [{result['filename']}](./{result['filename']})
"""
            
            if result['passed']:
                content += "- **검증**: 모든 키워드 조건을 충족합니다.\n"
            else:
                content += "- **실패 이유**:\n"
                for failure in result['failures']:
                    content += f"  - {failure}\n"
            
            content += "\n"
        
        content += """---

## 테스트 케이스 설명

1. **홈트레이닝 + 무릎 통증**: 집에서 할 수 있는 운동 위주, 무릎 부담 운동 제외
2. **헬스장 + 허리 디스크**: 헬스장 기구 활용, 허리에 부담가는 운동 제외
3. **수영 + 알레르기**: 수영 중심 운동, 알레르기 식품 제외 식단
4. **러닝 + 고혈압**: 유산소 중심, 고강도 운동 제한
5. **요가/필라테스 + 임신**: 저강도 운동, 복부 압박 운동 제한
6. **기본 케이스**: 특별한 제약 없는 일반적인 계획

---
*이 요약 파일은 자동 생성되었습니다.*
"""
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\n📊 요약 파일 생성 완료: {summary_path}")

    @pytest.mark.integration
    async def test_llm2_output_varies_by_preferences_and_health(self):
        """
        동일한 InBody 데이터로 6가지 조합 테스트
        각 조합마다 실제 LLM API 호출하여 계획 생성 및 검증
        """
        print("\n" + "="*80)
        print("LLM2 통합 테스트 시작: 선호도 & 건강 특이사항 조합")
        print("="*80)
        
        # Mock DB 세션
        mock_db = Mock()
        
        # LLMService 인스턴스 생성 (실제 LLM 호출)
        llm_service = LLMService()
        
        results = []
        
        for test_case in TEST_CASES:
            print(f"\n{'='*80}")
            print(f"테스트 케이스 {test_case['case_id']}: {test_case['name']}")
            print(f"{'='*80}")
            
            # GoalPlanInput 생성
            plan_input = self._create_goal_plan_input(
                preferences=test_case['preferences'],
                health_specifics=test_case['health_specifics'],
                goal_type=test_case['goal_type'],
                goal_description=test_case['goal_description']
            )
            
            try:
                # 실제 LLM 호출하여 주간 계획 생성
                print(f"🔄 LLM2 호출 중...")
                llm_response = await llm_service.call_goal_plan_llm(mock_db, plan_input)
                
                plan_text = llm_response.get("plan_text", "")
                model_version = llm_service.model_version
                
                print(f"✅ 계획 생성 완료 (길이: {len(plan_text)} 자)")
                
                # 결과 파일 저장
                self._save_plan_result(
                    filename=test_case['filename'],
                    case_info=test_case,
                    plan_text=plan_text,
                    model_version=model_version
                )
                
                # 키워드 검증
                passed, failures = self._verify_plan_content(
                    plan_text=plan_text,
                    expected_keywords=test_case['expected_keywords']
                )
                
                if passed:
                    print(f"✅ 키워드 검증 통과")
                else:
                    print(f"❌ 키워드 검증 실패:")
                    for failure in failures:
                        print(f"   - {failure}")
                
                results.append({
                    'case_id': test_case['case_id'],
                    'name': test_case['name'],
                    'filename': test_case['filename'],
                    'passed': passed,
                    'failures': failures
                })
                
            except Exception as e:
                print(f"❌ 테스트 실패: {str(e)}")
                results.append({
                    'case_id': test_case['case_id'],
                    'name': test_case['name'],
                    'filename': test_case['filename'],
                    'passed': False,
                    'failures': [f"예외 발생: {str(e)}"]
                })
        
        # 요약 파일 생성
        self._generate_summary(results)
        
        print(f"\n{'='*80}")
        print("모든 테스트 케이스 완료")
        print(f"{'='*80}\n")
        
        # 최종 검증: 적어도 하나의 케이스는 통과해야 함
        assert any(r['passed'] for r in results), "모든 테스트 케이스가 실패했습니다"


def test_llm2_preferences_sync_wrapper():
    """동기 테스트 래퍼 (pytest가 async 테스트를 실행하도록)"""
    test_instance = TestLLM2PreferencesIntegration()
    test_instance.setup_class()
    asyncio.run(test_instance.test_llm2_output_varies_by_preferences_and_health())
