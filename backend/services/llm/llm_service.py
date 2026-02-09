"""
LLM 서비스
AI 분석 및 계획 생성 (LangGraph 에이전트 사용)
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

from schemas.llm import StatusAnalysisInput, GoalPlanInput, LLMInteractionCreate
from repositories.llm.llm_interaction_repository import LLMInteractionRepository
from services.llm.llm_clients import create_llm_client
from .agent_graph import create_analysis_agent
from .weekly_plan_graph import create_weekly_plan_agent
from typing import AsyncGenerator
from typing import AsyncGenerator, Optional
import re

load_dotenv()


class LLMService:
    """LLM API 호출 서비스"""
    async def stream_chat_with_plan(
        self,
        thread_id: str,
        user_message: str,
        existing_plan: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        LLM2 휴먼 피드백 (Q&A) - 스트리밍 버전
        """
        print(f"--- [DEBUG] stream_chat_with_plan 진입 ---")
        print(f"--- [DEBUG] thread_id: {thread_id}")
        print(f"--- [DEBUG] raw user_message: {user_message}")

        config = {"configurable": {"thread_id": thread_id}}

        # =========================
        # 1. Category 파싱 (기존 로직 그대로)
        # =========================
        category = "qa_general"
        clean_message = user_message

        match = re.match(r"^\[Category:\s*(.*?)\]\s*(.*)$", user_message, re.DOTALL)
        if match:
            category_label = match.group(1).strip()
            clean_message = match.group(2).strip()

            if "운동" in category_label or "플랜" in category_label or "계획" in category_label:
                category = "adjust_exercise_plan"
            elif "식단" in category_label:
                category = "adjust_diet_plan"
            elif "강도" in category_label:
                category = "adjust_intensity"

        print(f"--- [DEBUG] category: {category}")
        print(f"--- [DEBUG] clean_message: {clean_message}")

        # =================================================
        # 2. LangGraph 상태에서 히스토리 가져오기 (메모리 연동)
        # =================================================
        state_snapshot = self.weekly_plan_agent.get_state(config)
        history_messages = []
        
        if state_snapshot and state_snapshot.values:
            for msg in state_snapshot.values.get("messages", []):
                role = "user" if msg.type == "human" else "assistant"
                history_messages.append((role, msg.content))

        # 시스템 프롬프트 구성
        system_prompt = """당신은 사용자의 주간 운동 및 식단 계획을 담당하는 퍼스널 트레이너입니다.
        사용자가 생성된 계획에 대해 질문하면, 전문적이고 친절하게 답변해주세요.
        이전 대화 맥락(사용자의 신체 정보, 목표, 생성된 계획)을 모두 고려해야 합니다."""
        
        if existing_plan:
            system_prompt += f"\n\n[참고: 현재 사용자의 주간 계획 정보]\n{existing_plan}\n\n사용자의 질문이나 요청이 위 계획과 관련이 있다면, 이 내용을 바탕으로 답변하거나 수정해주세요."

        # 현재 사용자 메시지 추가 (LLM 호출용)
        # history_messages에는 이미 이전 대화가 포함되어 있음
        messages_to_send = history_messages + [("user", clean_message)]

        full_text = ""

        # =================================================
        # 3. 직접 LLM 스트리밍 호출 (LangGraph 우회)
        # =================================================
        try:
            async for chunk in self.llm_client.generate_chat_with_history_stream(system_prompt, messages_to_send):
                full_text += chunk
                yield chunk
            
            # =================================================
            # 4. 대화 완료 후 LangGraph 상태 수동 업데이트 (메모리 저장)
            # =================================================
            print(f"--- [DEBUG] 스트리밍 완료. 상태 업데이트 진행 ---")
            self.weekly_plan_agent.update_state(
                config, 
                {"messages": [("human", clean_message), ("ai", full_text)]}
            )
            
        except Exception as e:
            print(f"--- [ERROR] 스트리밍 중 오류 발생: {e}")
            # 에러 발생 시에도 클라이언트에게 에러 메시지를 스트리밍으로 전달 가능
            yield f"\n[오류 발생] 죄송합니다. 응답을 생성하는 도중 문제가 발생했습니다: {str(e)}"

        # =========================
        # 4. (선택) 스트리밍 종료 후 DB 저장
        # =========================
        # 지금은 MVP라 생략
        # 나중에 필요하면 여기서 LLMInteractionRepository.create(...)

    def __init__(self):
        """LLM 에이전트 및 클라이언트 초기화"""
        self.model_version = "gpt-4o-mini"  # 또는 설정에서 가져옴
        self.llm_client = create_llm_client(self.model_version)
        self.analysis_agent = create_analysis_agent(self.llm_client)
        self.weekly_plan_agent = create_weekly_plan_agent(self.llm_client)

    # LLM1: 건강 기록 분석 및 리포트 생성 - 데이터 준비 
    # fixme : 단순히 input에 대해서 그대로 되돌려주고 있음. 
    # 필요가 없음. health_service에서 처리해야함.
    def prepare_status_analysis_input(
        self,
        record_id: int,
        user_id: int,
        measured_at: datetime,
        measurements: Dict[str, Any],
        body_type1: Optional[str],
        body_type2: Optional[str],
        prev_inbody_data: Optional[Dict[str, Any]] = None,
        prev_inbody_date: Optional[datetime] = None,
        interval_days: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        LLM1: 건강 상태 분석용 input 데이터 준비

        Args:
            record_id: 건강 기록 ID
            user_id: 사용자 ID
            measured_at: 측정 일시
            measurements: 인바디 측정 데이터(체형 분류 포함)
            body_type1: 1차 체형 분류
            body_type2: 2차 체형 분류
            prev_inbody_data: 이전 인바디 측정 데이터 (선택)
            prev_inbody_date: 이전 인바디 측정 일시 (선택)
            interval_days: 이전 InBody 측정 일시 (선택)

        Returns:
            LLM에 전달할 input 데이터 (프론트엔드에서 LLM API 호출 시 사용)
        """
        print(f"\n[DEBUG][LLMService] prepare_status_analysis_input 호출")
        print(f"[DEBUG][LLMService] prev_inbody_data is None: {prev_inbody_data is None}")
        print(f"[DEBUG][LLMService] prev_inbody_date is None: {prev_inbody_date is None}")
        print(f"[DEBUG][LLMService] interval_days is None: {interval_days is None}")
        if prev_inbody_data:
            print(f"[DEBUG][LLMService] prev_inbody_data 키: {list(prev_inbody_data.keys())[:5]}...")
        
        return {
            "record_id": record_id,
            "user_id": user_id,
            "measured_at": measured_at,
            "measurements": measurements,
            "body_type1": body_type1,
            "body_type2": body_type2,
            "prev_inbody_data": prev_inbody_data,
            "prev_inbody_date": prev_inbody_date,
            "interval_days": interval_days
        }

    def prepare_goal_plan_input(
        self,
        # 사용자 요구사항
        user_goal_type: Optional[str],
        user_goal_description: Optional[str],
        # 선택된 건강 기록
        record_id: int,
        user_id: int,
        measured_at: datetime,
        measurements: Dict[str, Any],
        # LLM1 분석 결과
        status_analysis_result: Optional[str] = None,
        status_analysis_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        LLM2: 주간 계획서 생성용 input 데이터 준비

        Args:
            user_goal_type: 사용자 목표 타입
            user_goal_description: 사용자 목표 상세
            record_id: 선택된 건강 기록 ID
            user_id: 사용자 ID
            measured_at: 측정 일시
            measurements: 인바디 측정 데이터(체형 분류 포함)
            status_analysis_result: LLM1의 분석 결과 텍스트
            status_analysis_id: LLM1 분석 결과 ID

        Returns:
            LLM에 전달할 input 데이터 (프론트엔드에서 LLM API 호출 시 사용)
        """
        return {
            "user_goal_type": user_goal_type,
            "user_goal_description": user_goal_description,
            "record_id": record_id,
            "user_id": user_id,
            "measured_at": measured_at,
            "measurements": measurements,
            "status_analysis_result": status_analysis_result,
            "status_analysis_id": status_analysis_id
        }

    # =====================================================
    # 아래는 팀원이 LLM API 연동 시 구현할 메서드들
    # =====================================================

    # LLM1: 건강 기록 분석 및 리포트 생성 - LLM 호출
    async def call_status_analysis_llm(
        self,
        input_data: StatusAnalysisInput
    ) -> Dict[str, Any]:
        """
        LangGraph 에이전트를 호출하여 건강 상태 분석 수행

        Args:
            input_data: StatusAnalysisInput 스키마 객체

        Returns:
            {
                "analysis_text": str,
                "embedding": {"embedding_1536": [...], "embedding_1024": [...]},
                "thread_id": str
            }
        """
        # 1. 각 분석 세션을 위한 고유 스레드 ID 생성
        thread_id = f"analysis_{input_data.user_id}_{input_data.record_id}_{datetime.now().timestamp()}"
        config = {"configurable": {"thread_id": thread_id}}
        print(f"\n[DEBUG][call_status_analysis_llm] 생성된 thread_id: {thread_id}")
        print(f"[DEBUG][call_status_analysis_llm] user_id: {input_data.user_id}, record_id: {input_data.record_id}")
        
        # 🔍 중요: agent에 전달하기 전 input_data 검증
        print(f"\n[DEBUG][call_status_analysis_llm] === Agent 호출 전 input_data 검증 ===")
        print(f"[DEBUG][call_status_analysis_llm] input_data 타입: {type(input_data)}")
        print(f"[DEBUG][call_status_analysis_llm] input_data.prev_inbody_data is None: {input_data.prev_inbody_data is None}")
        print(f"[DEBUG][call_status_analysis_llm] input_data.prev_inbody_date is None: {input_data.prev_inbody_date is None}")
        if input_data.prev_inbody_data:
            print(f"[DEBUG][call_status_analysis_llm] ✅ prev_inbody_data 존재!")
            print(f"[DEBUG][call_status_analysis_llm] prev_inbody_data 타입: {type(input_data.prev_inbody_data)}")
            if isinstance(input_data.prev_inbody_data, dict):
                print(f"[DEBUG][call_status_analysis_llm] prev_inbody_data 키 샘플: {list(input_data.prev_inbody_data.keys())[:3]}")
        else:
            print(f"[DEBUG][call_status_analysis_llm] ⚠️ prev_inbody_data 없음 (첫 인바디 또는 유실)")

        # 2. LangGraph 에이전트 호출 (최초 분석)
        print(f"[DEBUG][call_status_analysis_llm] === Agent 호출 시작 ===")
        initial_state = self.analysis_agent.invoke(
            {"analysis_input": input_data},
            config=config
        )

        print(f"[DEBUG][call_status_analysis_llm] initial_state keys: {list(initial_state.keys())}")
        print(f"[DEBUG][call_status_analysis_llm] has analysis_input: {'analysis_input' in initial_state}")
        if 'analysis_input' in initial_state:
            print(f"[DEBUG][call_status_analysis_llm] analysis_input is None: {initial_state['analysis_input'] is None}")

        # 3. 결과 추출
        # 🔧 수정: initial_analysis 결과만 추출 (qa_general로 넘어간 경우 방지)
        # - messages[0]: human (InBody 데이터)
        # - messages[1]: ai (initial_analysis 결과) ← 이것만 필요
        # - messages[2]: ai (qa_general 응답) ← 있으면 안 됨
        messages = initial_state['messages']
        if len(messages) >= 2:
            # 항상 두 번째 메시지(initial_analysis 결과)를 사용
            analysis_text = messages[1].content
        else:
            # 예외 상황: 메시지가 부족하면 마지막 메시지 사용
            analysis_text = messages[-1].content

        embedding = initial_state.get("embedding")

        return {"analysis_text": analysis_text, "embedding": embedding, "thread_id": thread_id}

    async def chat_with_analysis(
        self,
        thread_id: str,
        user_message: str,
        report_id: int = None,
        db: Session = None
    ) -> str:
        """
        LLM1 에 대한
        휴먼 피드백 (Q&A) 처리: 기존 스레드에 이어서 대화 수행
        checkpoint 없으면 DB에서 InBody 데이터 복원
        """
        config = {"configurable": {"thread_id": thread_id}}

        # 🔍 checkpoint 상태 확인
        print(f"\n[DEBUG][chat_with_analysis] thread_id: {thread_id}")
        checkpoint_exists = False
        try:
            checkpointer = self.analysis_agent.checkpointer
            if checkpointer:
                checkpoint = checkpointer.get(config)
                if checkpoint:
                    checkpoint_exists = True
                    print(f"[DEBUG][chat_with_analysis] ✅ checkpoint found")
                else:
                    print(f"[DEBUG][chat_with_analysis] ⚠️ checkpoint NOT FOUND")
        except Exception as e:
            print(f"[DEBUG][chat_with_analysis] checkpoint 조회 실패: {e}")

        # 📦 DB Fallback: checkpoint 없으면 InBody 데이터 복원
        initial_messages = []
        if not checkpoint_exists and report_id and db:
            print(f"[DEBUG][chat_with_analysis] 🔄 DB Fallback 시작 (report_id={report_id})")
            try:
                from repositories.llm.analysis_report_repository import AnalysisReportRepository
                from repositories.common.health_record_repository import HealthRecordRepository
                from services.llm.prompt_generator import create_inbody_analysis_prompt
                from schemas.inbody import InBodyData as InBodyMeasurements

                # 1. analysis_report에서 record_id 조회
                analysis_report = AnalysisReportRepository.get_by_id(db, report_id)
                if analysis_report and analysis_report.record_id:
                    # 2. health_record에서 measurements 조회 
                    # 이때, 가장 최신의 두개의 인바디 데이터를 가져와야함
                    # 단, 이전 인바디 데이터가 없을 경우를 대비해서 예외처리를 해야함
                    health_record = HealthRecordRepository.get_by_id(db, analysis_report.record_id)
                    
                    # 이전 인바디 데이터 조회: 같은 사용자의 현재 기록보다 이전 측정 기록
                    prev_health_record = None
                    if health_record:
                        prev_health_record = HealthRecordRepository.get_previous_record(
                            db, health_record.user_id, health_record
                        )
                    if health_record and health_record.measurements:
                        # 3. InBody 프롬프트 재생성
                        measurements = InBodyMeasurements(**health_record.measurements)
                        prev_measurements = InBodyMeasurements(**prev_health_record.measurements) if prev_health_record else None
                        system_prompt, user_prompt = create_inbody_analysis_prompt(
                            measurements,
                            body_type1=getattr(health_record, 'body_type1', None),
                            body_type2=getattr(health_record, 'body_type2', None),
                            # 이전 인바디 데이터가 없을 경우를 대비해서 예외처리를 해야함
                            prev_inbody_data=prev_measurements if prev_measurements else None,
                            # 이전 인바디 데이터가 가장 최신의 인바디 데이터와 간격 계산
                            interval_days=(health_record.created_at - prev_health_record.created_at).days if prev_health_record else None
                        )
                        initial_messages.append(("human", user_prompt))
                        print(f"[DEBUG][chat_with_analysis] ✅ InBody 데이터 복원 완료 (record_id={analysis_report.record_id})")
            except Exception as e:
                print(f"[DEBUG][chat_with_analysis] ⚠️ DB Fallback 실패: {e}")
                import traceback
                traceback.print_exc()

        # LangGraph 실행
        messages_to_send = initial_messages + [("human", user_message)]
        result = self.analysis_agent.invoke(
            {"messages": messages_to_send},
            config=config
        )

        print(f"[DEBUG][chat_with_analysis] result has analysis_input: {'analysis_input' in result}")

        # 마지막 AI 응답 반환
        return result["messages"][-1].content

    async def call_goal_plan_llm(
        self,
        db: Session,
        input_data: GoalPlanInput
    ) -> dict:
        """
        LLM2: 주간 계획서 생성 API 호출 및 초기 상호작용 저장
        """
        # 1. 스레드 ID 생성
        thread_id = f"plan_{input_data.user_id}_{input_data.record_id}_{datetime.now().timestamp()}"
        config = {"configurable": {"thread_id": thread_id}}



        # 2. LangGraph 에이전트 호출
        initial_state = self.weekly_plan_agent.invoke(
            {"plan_input": input_data},
            config=config
        )
        
        # (
        #     {"plan_input": input_data},
        #     config=config
        # )
        
        plan_text = initial_state['messages'][-1].content

        # 3. 초기 LLM 상호작용 DB에 저장
        interaction_schema = LLMInteractionCreate(
            llm_stage="llm2",
            source_type="weekly_plan_initial",
            source_id=input_data.record_id,
            output_text=plan_text,
            model_version=self.model_version
        )
        new_interaction = LLMInteractionRepository.create(db, input_data.user_id, interaction_schema)

        # 4. 결과 반환
        return {
            "plan_text": plan_text,
            "thread_id": thread_id,
            "llm_interaction_id": new_interaction.id
        }

    async def chat_with_plan(
        self,
        thread_id: str,
        user_message: str,
        existing_plan: Optional[str] = None
    ) -> str:
        """
        LLM2 휴먼 피드백 (Q&A) 처리: 주간 계획 수정 및 질의응답
        """
        import re
        print(f"--- [DEBUG] chat_with_plan 진입 ---")
        print(f"--- [DEBUG] thread_id: {thread_id}")
        print(f"--- [DEBUG] raw user_message: {user_message}")

        config = {"configurable": {"thread_id": thread_id}}
        
        # 메시지 파싱 ([Category: ...] 분리)
        category = None
        clean_message = user_message
        
        # Regex로 [Category: ...] 패턴 추출
        match = re.match(r"^\[Category:\s*(.*?)\]\s*(.*)$", user_message, re.DOTALL)
        if match:
            category_label = match.group(1).strip()
            clean_message = match.group(2).strip()
            print(f"--- [DEBUG] Parsed Category Label: {category_label}")
            print(f"--- [DEBUG] Clean Message: {clean_message}")
            
            # 카테고리 라벨을 내부 키로 매핑 (필요시)
            # 현재는 단순 매핑 또는 그대로 전달. 그래프의 router 로직에 의존.
            # 그래프에서는 "운동 플랜 조정", "식단 조정" 등을 기대함.
            # 프론트엔드 라벨: "📅 주간 계획", "🏋️ 부위별 운동" 등.
            # 여기서는 우선 매핑 없이 전달하거나, 간단한 변환 로직 추가 가능.
            
            # 임시 매핑 로직 (프론트 라벨 -> 그래프 내부 카테고리)
            if "운동" in category_label or "플랜" in category_label or "계획" in category_label: # 예: 운동 플랜 조정
                category = "adjust_exercise_plan"
            elif "식단" in category_label:
                category = "adjust_diet_plan"
            elif "강도" in category_label:
                category = "adjust_intensity"
            else:
                # 그 외 (주간 계획, 부위별 운동 등)은 일반 Q&A로 처리하되,
                # 그래프 라우터가 "qa_general"로 폴백하도록 None 또는 "qa_general" 전달
                category = "qa_general"
            
            print(f"--- [DEBUG] Mapped Category Key: {category}")
            
        else:
            print("--- [DEBUG] No Category prefix found. Treating as general message.")
            category = "qa_general"

        # 상태 업데이트 준비
        input_payload = {
            "messages": [("human", clean_message)],
            # feedback_category를 업데이트하여 라우터가 올바른 경로를 타도록 함
            "feedback_category": category,
            "existing_plan": existing_plan
        }
        
        print(f"--- [DEBUG] llm_service: existing_plan 전달 여부: {bool(existing_plan)} ---")
        if existing_plan:
            print(f"--- [DEBUG] llm_service: existing_plan preview: {existing_plan[:100]}... ---")
        print(f"--- [DEBUG] Invoking weekly_plan_agent with payload: {input_payload}")

        # LangGraph 실행 (이전 상태에서 이어서 실행)
        try:
            result = self.weekly_plan_agent.invoke(
                input_payload,
                config=config
            )
            print("--- [DEBUG] LangGraph invocation successful")
            # print(f"--- [DEBUG] Result messages: {result.get('messages')}")
            
            last_message = result["messages"][-1].content
            print(f"--- [DEBUG] Last AI Message: {last_message[:100]}...") # 길면 자름
            
            return last_message
            
        except Exception as e:
            print(f"--- [ERROR] LangGraph invocation failed: {e}")
            import traceback
            traceback.print_exc()
            raise e

    async def refine_plan(
        self,
        thread_id: str,
        state_update: dict
    ) -> str:
        """
        LLM2 휴먼 피드백: 구조화된 피드백으로 주간 계획 수정
        """
        print(f"--- [DEBUG] refine_plan 진입 ---")
        print(f"--- [DEBUG] thread_id: {thread_id}")
        print(f"--- [DEBUG] state_update: {state_update}")

        config = {"configurable": {"thread_id": thread_id}}
        
        # LangGraph 실행 (전달받은 state_update로 상태 업데이트)
        try:
            result = self.weekly_plan_agent.invoke(
                state_update,
                config=config
            )
            print("--- [DEBUG] LangGraph invocation successful")
            
            last_message = result["messages"][-1].content
            print(f"--- [DEBUG] Last AI Message: {last_message[:100]}...")
            
            return last_message
        except Exception as e:
            print(f"--- [ERROR] LangGraph invocation failed: {e}")
            import traceback
            traceback.print_exc()
            raise e
    
# NOTE:
# - 초기 주간 계획 생성은 invoke 방식 사용
# - 스트리밍은 휴먼 피드백(chat/refine)에만 사용 예정
# - stream_goal_plan_llm은 향후 UX 변경 대비용

    async def stream_goal_plan_llm(
            self,
            input_data: GoalPlanInput
            ) -> AsyncGenerator[str, None]:
        """
        LLM2: 주간 계획서 생성 (스트리밍 버전)
        """
        thread_id = f"plan_{input_data.user_id}_{input_data.record_id}_{datetime.now().timestamp()}"
        config = {"configurable": {"thread_id": thread_id}}

        full_text = ""

        # 🔥 invoke → stream
        async for event in self.weekly_plan_agent.stream(
            {"plan_input": input_data},
            config=config
        ):
            """
            LangGraph stream 이벤트는 여러 종류가 있음
            여기서는 'LLM이 말하는 텍스트'만 골라냄
            """

            # 이벤트 구조는 LangGraph 버전에 따라 조금 다를 수 있음
            # 가장 흔한 패턴 예시:
            if event.get("event") == "on_chat_model_stream":
                chunk = event["data"]["chunk"].content
                if chunk:
                    full_text += chunk
                    yield chunk

                # ❗ 하루 MVP에서는 여기서 DB 저장 안 함
                # 나중에:
                # LLMInteractionRepository.create(..., output_text=full_text)
