"""
LLM 서비스
AI 분석 및 계획 생성
=========================
간단히 초안만 임의로 작성해둠.
추후 LLM 기능 개발이 완료되면, 전체 코드를 확인하고 수정해야함.
=========================
"""

from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv

load_dotenv()


class LLMService:
    """LLM API 호출 서비스"""
    
    def __init__(self):
        """LLM 클라이언트 초기화"""
        # TODO: LLM API 키 설정
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.model_version = "gpt-4"  # 또는 사용할 모델
    
    async def analyze_health_status(
        self,
        inbody_data: Dict[str, Any],
        body_type: Optional[str] = None
    ) -> str:
        """
        인바디 정보와 체형 정보를 기반으로 현재 사용자의 상태 분석 (LLM1)
        
        Args:
            inbody_data: 인바디 측정 데이터
            body_type: 체형 분류 결과
            
        Returns:
            LLM이 생성한 분석 결과 텍스트
        """
        # TODO: 실제 LLM API 호출 구현
        # 예시: OpenAI API, Anthropic Claude API 등
        
        prompt = self._create_status_analysis_prompt(inbody_data, body_type)
        
        # 임시 응답 (실제 구현 시 LLM API 호출로 대체)
        return f"""
# 건강 상태 분석 결과

## 기본 정보
- 체형: {body_type or '분석 중'}
- BMI: {inbody_data.get('BMI', 'N/A')}
- 체지방률: {inbody_data.get('체지방률', 'N/A')}%

## 분석
당신의 현재 건강 상태는 양호합니다.
(실제 LLM 분석 결과가 여기에 들어갑니다)

## 권장사항
- 규칙적인 운동
- 균형 잡힌 식단
"""
    
    async def generate_weekly_plan(
        self,
        inbody_data: Dict[str, Any],
        body_type: Optional[str],
        analysis_result: str,
        user_goal: str
    ) -> str:
        """
        사용자 목표에 맞는 주간 계획서 생성 (LLM2)
        
        Args:
            inbody_data: 인바디 측정 데이터
            body_type: 체형 분류 결과
            analysis_result: 이전 분석 결과
            user_goal: 사용자가 입력한 목표
            
        Returns:
            LLM이 생성한 주간 계획서
        """
        # TODO: 실제 LLM API 호출 구현
        
        prompt = self._create_weekly_plan_prompt(
            inbody_data, body_type, analysis_result, user_goal
        )
        
        # 임시 응답
        return f"""
# 주간 운동 및 식단 계획

## 목표
{user_goal}

## 주간 계획
### 월요일
- 운동: 상체 근력 운동 (1시간)
- 식단: 고단백 저탄수화물

### 화요일
- 운동: 유산소 운동 (30분)
- 식단: 균형 잡힌 식사

(실제 LLM 생성 계획이 여기에 들어갑니다)
"""
    
    def _create_status_analysis_prompt(
        self,
        inbody_data: Dict[str, Any],
        body_type: Optional[str]
    ) -> str:
        """상태 분석용 프롬프트 생성"""
        return f"""
당신은 전문 건강 컨설턴트입니다.
다음 인바디 데이터와 체형 정보를 분석하여 사용자의 현재 건강 상태를 평가해주세요.

인바디 데이터:
{inbody_data}

체형 분류: {body_type or '미분류'}

분석 내용:
1. 현재 건강 상태 평가
2. 강점과 개선이 필요한 부분
3. 건강 관리 권장사항
"""
    
    def _create_weekly_plan_prompt(
        self,
        inbody_data: Dict[str, Any],
        body_type: Optional[str],
        analysis_result: str,
        user_goal: str
    ) -> str:
        """주간 계획 생성용 프롬프트 생성"""
        return f"""
당신은 전문 피트니스 트레이너입니다.
다음 정보를 바탕으로 사용자의 목표 달성을 위한 주간 계획을 작성해주세요.

인바디 데이터: {inbody_data}
체형: {body_type or '미분류'}
건강 분석 결과: {analysis_result}
사용자 목표: {user_goal}

주간 계획 포함 사항:
1. 요일별 운동 계획
2. 식단 권장사항
3. 주의사항 및 팁
"""
