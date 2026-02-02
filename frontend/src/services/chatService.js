/**
 * 챗봇 관련 API 서비스
 *
 * 📍 사용 위치: pages/Chatbot/ (Chatbot.jsx, ChatbotSelector.jsx)
 *
 * 백엔드 API 엔드포인트:
 * - POST /api/llm/status - 상태 분석
 * - POST /api/llm/plan - 목표 계획
 * - POST /api/llm/chat - 일반 채팅
 */

import { apiRequest } from './api';

/**
 * 상태 분석 요청 (Status Bot)
 *
 * 📍 사용 위치: pages/Chatbot/Chatbot.jsx (botType="status")
 *
 * 기능:
 * - 사용자의 현재 건강 상태를 AI가 분석
 * - 최근 인바디 데이터 기반으로 체성분, 비만도 등 평가
 * - "현재 당신의 체지방률은 표준이며..." 같은 응답 생성
 *
 * @param {Object} data - 분석 요청 데이터
 * @param {number} data.user_id - 사용자 ID
 * @param {Object} data.inbody_data - 최근 인바디 데이터
 * @param {string} [data.additional_info] - 추가 정보 (선택)
 *
 * @returns {Promise<Object>} LLM 응답
 * @returns {string} return.response - AI 생성 텍스트 (상태 분석 결과)
 * @returns {string} return.model_version - 사용된 LLM 모델 버전
 *
 * @example
 * // 챗봇에서 "내 상태 분석해줘" 선택 시
 * const userData = JSON.parse(localStorage.getItem('user'));
 * const requestData = {
 *   user_id: userData.id,
 *   inbody_data: userData.inbody_data,
 *   additional_info: "요즘 운동을 시작했어요"
 * };
 * const result = await getStatusAnalysis(requestData);
 * console.log(result.response);
 * // "현재 체중 77.7kg, 골격근량 35.2kg으로 표준 체형입니다..."
 */
export const getStatusAnalysis = async (data) => {
    return await apiRequest('/llm/status', {
        method: 'POST',
        body: JSON.stringify(data),
    });
};

/**
 * 목표 계획 요청 (Plan Bot)
 *
 * 📍 사용 위치: pages/Chatbot/Chatbot.jsx (botType="plan")
 *
 * 기능:
 * - 사용자의 목표(감량, 증량, 재활 등)에 맞는 운동 계획 생성
 * - 현재 상태와 목표 체중을 고려한 맞춤 플랜
 * - "주 3회 유산소 운동을 추천합니다..." 같은 구체적 계획 제공
 *
 * @param {Object} data - 계획 요청 데이터
 * @param {number} data.user_id - 사용자 ID
 * @param {string} data.goal_type - 목표 타입 ("감량", "유지", "증량", "재활")
 * @param {number} data.start_weight - 시작 체중 (kg)
 * @param {number} data.target_weight - 목표 체중 (kg)
 * @param {string} [data.goal_description] - 목표 상세 (예: "허리 재활")
 * @param {Object} [data.inbody_data] - 현재 인바디 데이터
 *
 * @returns {Promise<Object>} LLM 응답
 * @returns {string} return.response - AI 생성 계획 (주간 운동 계획, 식단 등)
 * @returns {string} return.model_version - 사용된 LLM 모델 버전
 *
 * @example
 * // 챗봇에서 "운동 계획 세워줘" 선택 시
 * const userData = JSON.parse(localStorage.getItem('user'));
 * const requestData = {
 *   user_id: userData.id,
 *   goal_type: "감량",
 *   start_weight: 80,
 *   target_weight: 75,
 *   goal_description: "3개월 안에 달성하고 싶어요",
 *   inbody_data: userData.inbody_data
 * };
 * const result = await getGoalPlan(requestData);
 * console.log(result.response);
 * // "80kg → 75kg 감량을 위한 12주 계획:
 * //  주 1-4: 유산소 주 3회, 근력 주 2회..."
 */
export const getGoalPlan = async (data) => {
    return await apiRequest('/llm/plan', {
        method: 'POST',
        body: JSON.stringify(data),
    });
};

/**
 * 일반 채팅 (General Chat Bot)
 *
 * 📍 사용 위치: pages/Chatbot/Chatbot.jsx (botType="general")
 *
 * 기능:
 * - 건강, 운동, 영양에 대한 일반적인 질문 응답
 * - "단백질은 하루에 얼마나 먹어야 해?" 같은 질문에 답변
 * - 대화 히스토리를 포함한 연속 대화 가능
 *
 * @param {Object} data - 채팅 데이터
 * @param {number} data.user_id - 사용자 ID
 * @param {string} data.message - 사용자 메시지
 * @param {Array<Object>} [data.history] - 이전 대화 내역 (선택)
 * @param {string} data.history[].role - 역할 ("user" | "assistant")
 * @param {string} data.history[].content - 메시지 내용
 *
 * @returns {Promise<Object>} LLM 응답
 * @returns {string} return.response - AI 응답 메시지
 * @returns {string} return.model_version - 사용된 LLM 모델 버전
 *
 * @example
 * // 챗봇에서 자유롭게 질문 입력
 * const requestData = {
 *   user_id: userData.id,
 *   message: "근육을 키우려면 단백질을 얼마나 먹어야 해?",
 *   history: [
 *     { role: "user", content: "안녕" },
 *     { role: "assistant", content: "안녕하세요!" }
 *   ]
 * };
 * const result = await sendChatMessage(requestData);
 * console.log(result.response);
 * // "일반적으로 체중 1kg당 1.6~2.2g의 단백질 섭취를 권장합니다..."
 */
export const sendChatMessage = async (data) => {
    return await apiRequest('/llm/chat', {
        method: 'POST',
        body: JSON.stringify(data),
    });
};

/**
 * 챗봇 대화 (신규 - LangGraph 기반)
 *
 * 📍 사용 위치: pages/Chatbot/Chatbot.jsx
 *
 * 기능:
 * - 인바디 분석 전문가 또는 운동 플래너 전문가와 대화
 * - LangGraph 에이전트를 사용한 지능형 대화
 * - 대화 이력 자동 추적 (thread_id 사용)
 *
 * @param {Object} data - 챗봇 대화 요청 데이터
 * @param {string} data.bot_type - 챗봇 유형 ("inbody-analyst" | "workout-planner")
 * @param {string} data.message - 사용자 메시지
 * @param {number} [data.user_id] - 사용자 ID (옵션)
 * @param {string} [data.thread_id] - 대화 스레드 ID (이전 대화 이어가기용, 옵션)
 *
 * @returns {Promise<Object>} 챗봇 응답
 * @returns {string} return.response - AI 응답 메시지
 * @returns {string} return.thread_id - 대화 스레드 ID (다음 요청에 사용)
 *
 * @example
 * // 첫 대화 시작
 * const result1 = await sendChatbotMessage({
 *   bot_type: "inbody-analyst",
 *   message: "체지방을 줄이려면 어떻게 해야 해?",
 *   user_id: 1
 * });
 * console.log(result1.response);
 * console.log(result1.thread_id); // "chatbot_inbody-analyst_1_abc123"
 *
 * // 이전 대화 이어서 하기
 * const result2 = await sendChatbotMessage({
 *   bot_type: "inbody-analyst",
 *   message: "유산소 운동은 얼마나 해야 해?",
 *   thread_id: result1.thread_id // 이전 대화 ID 전달
 * });
 * console.log(result2.response); // 이전 대화 맥락을 기억하여 답변
 */
export const sendChatbotMessage = async (data) => {
    return await apiRequest('/chatbot/chat', {
        method: 'POST',
        body: JSON.stringify(data),
    });
};
