import React, { useState, useRef, useEffect } from 'react';
import { Send, User } from 'lucide-react';
import { useParams, useLocation } from 'react-router-dom';
import { sendChatbotMessage } from '../../services/chatService';

// 마크다운 렌더링을 위한 라이브러리 임포트
// (유저 요청: LLM 응답 텍스트를 예쁘게 보여주기 위함)
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

// 환경 변수로 목업 모드 관리 (.env 파일에서 설정)
const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === 'true';

const BOT_CONFIG = {
    'inbody-analyst': {
        name: '인바디 분석 전문가',
        icon: '🧑‍⚕️',
        greeting: "안녕하세요! 인바디 분석 전문가입니다. 잠시만 기다려주시면 분석 결과를 가져오겠습니다...",
        color: '#667eea',
        gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    },
    'workout-planner': {
        name: '운동 플래너 전문가',
        icon: '🏋️',
        greeting: "안녕하세요! 운동 플래너 전문가입니다. 회원님의 목표에 맞는 주간 운동 계획을 생성 중입니다...",
        color: '#f5576c',
        gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
    }
};

const Chatbot = () => {
    const { botType } = useParams();
    const location = useLocation();
    const config = BOT_CONFIG[botType] || BOT_CONFIG['inbody-analyst'];

    const [messages, setMessages] = useState([
        { id: 1, text: config.greeting, sender: 'bot' }
    ]);
    const [inputValue, setInputValue] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [threadId, setThreadId] = useState(null); // LangGraph 대화 스레드 ID (공통)
    const [reportId, setReportId] = useState(null); // 인바디 리포트 ID
    const [planId, setPlanId] = useState(null); // 운동 플랜 ID

    const [quickReplies, setQuickReplies] = useState([]); // 빠른 응답 버튼 (전역, deprecated)
    const [chatCategory, setChatCategory] = useState(null); // 현재 대화 주제 (null이면 미선택)

    // 채팅 히스토리 관련 state
    const [showHistorySidebar, setShowHistorySidebar] = useState(false); // 사이드바 표시 여부
    const [chatHistories, setChatHistories] = useState([]); // 저장된 대화 목록
    const [currentChatId, setCurrentChatId] = useState(null); // 현재 대화 ID
    const chatIdRef = useRef(null); // currentChatId를 동기적으로 추적하기 위한 Ref

    // currentChatId가 변경되면 Ref도 업데이트
    useEffect(() => {
        chatIdRef.current = currentChatId;
    }, [currentChatId]);

    // ============================================
    // 봇 타입별 고정 카테고리 버튼 설정
    // - 인바디 분석가: 근육/체지방/균형/기타
    // - 운동 플래너: 주간계획/부위별/유산소/기타
    // ============================================
    const INBODY_CATEGORIES = [
        { id: 'muscle', label: '💪 근육 분석', value: '💪 근육 상세 분석' },
        { id: 'fat', label: '💧 체지방 분석', value: '💧 체지방 상세 분석' },
        { id: 'balance', label: '⚖️ 균형/불균형', value: '⚖️ 균형/불균형 설명' },
        { id: 'general', label: '❓ 기타 질문', value: '❓ 기타 질문' }
    ];

    // 운동 플래너 카테고리
    const WORKOUT_CATEGORIES = [
        { id: 'weekly', label: '📅 주간 계획', value: '주간 운동 계획 보여줘' },
        { id: 'bodypart', label: '🏋️ 부위별 운동', value: '부위별 운동 추천해줘' },
        { id: 'cardio', label: '🏃 유산소', value: '유산소 운동 알려줘' },
        { id: 'general', label: '❓ 기타 질문', value: '❓ 기타 질문' }
    ];

    // 봇 타입에 따른 카테고리 선택
    const getCurrentCategories = () => {
        if (botType === 'workout-planner') return WORKOUT_CATEGORIES;
        return INBODY_CATEGORIES;
    };



    const messagesEndRef = useRef(null);
    const hasInitialized = useRef(false); // 초기화 중복 실행 방지

    // 현재 선택된 카테고리 라벨 가져오기 (UI 표시용)
    const getCategoryLabel = () => {
        if (!chatCategory) return null;
        const cats = getCurrentCategories();
        const cat = cats.find(c => c.id === chatCategory);
        return cat ? cat.label : null;
    };

    // 이전 페이지에서 전달받은 데이터
    const { inbodyData, userId, planRequest } = location.state || {};

    // 사용자 ID 결정: location.state > localStorage > 기본값 1
    const getUserId = () => {
        if (userId) return userId;

        const userData = JSON.parse(localStorage.getItem('user') || '{}');
        if (userData.id) return userData.id;

        console.warn('⚠️ 사용자 ID를 찾을 수 없어 기본값(1)을 사용합니다.');
        return 1;
    };

    const currentUserId = getUserId();

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, quickReplies]); // quickReplies 변경 시에도 스크롤

    // 메시지가 변경될 때마다 자동 저장
    useEffect(() => {
        if (messages.length > 1) {
            saveChatHistory();
        }
    }, [messages]);

    // 컴포넌트 마운트 시 히스토리 목록 로드
    useEffect(() => {
        const histories = getChatHistories();
        setChatHistories(histories);
    }, [botType]);

    // 초기 진입 시 자동 실행 (1회만)
    useEffect(() => {
        const initChat = async () => {
            if (USE_MOCK_DATA) {
                if (botType === 'workout-planner' && planRequest) {
                    setTimeout(() => {
                        const mockPlanResponse = `🏋️ **맞춤형 주간 운동 플랜**이 완성되었습니다!\n\n**목표**: ${planRequest.goal}\n**선호 운동**: ${planRequest.preferences.join(', ')}\n**특이사항**: ${planRequest.diseases || '없음'}`;
                        const mockPlanDetails = `
### 📅 주간 루틴 가이드

**월요일 (하체/코어)**
- 스쿼트 4세트 x 12회
- 런지 3세트 x 15회
- 플랭크 3세트 x 40초

**수요일 (상체/등)**
- 푸쉬업 4세트 x 10회
- 덤벨 로우 3세트 x 12회
- 숄더 프레스 3세트 x 12회

**금요일 (전신 유산소)**
- 버피 테스트 10분
- 인터벌 러닝 20분

💡 **질병 주의사항**: ${planRequest.diseases ? planRequest.diseases + '에 무리가 가지 않도록 중량을 낮춰서 진행하세요.' : '컨디션에 따라 강도를 조절하세요.'}`;

                        setMessages(prev => [
                            ...prev,
                            {
                                id: Date.now(),
                                text: mockPlanResponse,
                                details: mockPlanDetails,
                                sender: 'bot'
                            }
                        ]);
                    }, 1500);
                    return;
                }

                // 목업 모드: 1.5초 후 분석 결과 시뮬레이션
                setTimeout(() => {
                    const mockSummary = `[인바디 분석 요약]
✅ **체형**: **표준 체형** (BMI 23.2 / 체지방률 18.5%) - 전반적 균형 양호
✅ **근육**: 체중 대비 골격근량 약간 부족, **상체 근력 강화** 필요
✅ **지방**: 복부 지방률은 정상이지만 **내장 지방** 주의 단계
✅ **식단**: 단백질 하루 80g 섭취, 저녁 탄수화물 제한 권장
✅ **운동**: 주 3회 근력(하체 위주) + 주 2회 인터벌 러닝 추천`;

                    const mockDetail = `[상세 분석 리포트]

1. **체성분 상세 분석**
   - **체중**: 72.5kg (표준 범위 내)
   - **골격근량**: 32.8kg (표준 이하) 📉
     -> 체중은 정상이지만 근육량이 부족해 기초대사량이 낮을 수 있습니다.
   - **체지방량**: 13.4kg (표준)
     -> 체지방률 18.5%는 남성 기준 매우 이상적인 수치이나, 근육량 부족으로 인해 외관상 탄력이 떨어져 보일 수 있습니다.

2. **부위별 근육/지방 분석**
   - **상체**: 근육 발달이 더딘 편입니다. 푸쉬업, 턱걸이 등의 운동 비중을 높여주세요.
   - **하체**: 표준 수준이나, 스쿼트 중량을 늘려 근비대를 노려볼 만합니다.
   - **복부**: 내장지방 레벨이 5로, 아직 안전하지만 7 이상으로 올라가면 성인병 위험이 있습니다. 야식을 줄이세요.

3. **영양 및 대사 가이드**
   - **기초대사량**: 1650kcal (활동량 감안시 2400kcal 섭취 가능)
   - **추천 식단**: 닭가슴살 샐러드, 현미밥, 연어, 두부
   - **물 섭취**: 하루 2.5L 이상 권장 (현재 근육 내 수분 보유량 약간 부족)

4. **맞춤 솔루션**
   "지금은 체중 감량보다는 **근육량 증가(린매스업)**에 집중할 시기입니다. 
   잘 드시되 클린한 음식으로 섭취량을 늘리고, 고강도 웨이트 트레이닝을 시작하세요!"`;

                    setMessages(prev => [
                        ...prev,
                        {
                            id: Date.now(),
                            text: mockSummary,
                            details: mockDetail, // 상세 내용 추가
                            sender: 'bot'
                        }
                    ]);

                    // 인바디 분석 전문가: 분석 결과 + 안내 메시지 추가
                    if (botType === 'inbody-analyst') {
                        // 안내 메시지 추가
                        setTimeout(() => {
                            setMessages(prev => [
                                ...prev,
                                {
                                    id: Date.now() + 100,
                                    text: '💡 **분석 결과는 어떠셨나요?**\n\n궁금하신 부분을 아래 카테고리에서 선택하시거나, 직접 질문을 입력해주세요!',
                                    sender: 'bot',
                                    type: 'guidance' // 안내 메시지 타입
                                }
                            ]);
                        }, 2000);
                    }
                }, 1500);
                return;
            }

            ////////////////////////////////////////////////////////////////////////////////////////////////////////
            // 실제 API 모드
            setIsTyping(true);
            try {
                let response;
                let responseData = null;  // API 응답 데이터 저장용

                if (botType === 'inbody-analyst') {
                    // pre-fetched 데이터 확인
                    const preFetchedData = location.state?.analysisResult;

                    if (preFetchedData && !preFetchedData.mockData) {
                        // ✅ 이전에 가져온 데이터 활용
                        console.log("✅ Using Pre-fetched Analysis Data");
                        responseData = preFetchedData;
                    } else {
                        // 기존 로직: API 호출
                        // 1. 인바디 분석 전문가: 분석 결과 조회
                        // record_id가 필요함. inbodyData가 없으면 에러 처리
                        const recordId = inbodyData?.id;
                        if (!recordId) {
                            throw new Error("분석할 인바디 기록이 없습니다.");
                        }

                        // POST /api/analysis/{record_id}?user_id={user_id}
                        const res = await fetch(`/api/analysis/${recordId}?user_id=${currentUserId}`, {
                            method: 'POST'
                        });
                        if (!res.ok) throw new Error("분석 리포트 생성 실패");

                        responseData = await res.json();
                    }

                    // responseData = AnalysisReportResponse: { id, summary, content, thread_id, ... }

                    setReportId(responseData.id);  // ✅ 'id' 필드 사용
                    setThreadId(responseData.thread_id);

                    // response는 메시지 표시용 (summary 우선)
                    response = responseData.summary || responseData.llm_output;

                } else if (botType === 'workout-planner') {
                    // 2. 운동 플래너 전문가: 주간 계획 생성

                    const preFetchedData = location.state?.planResult;

                    if (preFetchedData && !preFetchedData.mockData) {
                        console.log("✅ Using Pre-fetched Workout Plan Data");
                        responseData = preFetchedData;

                        // GoalPlanResponse structure handling
                        response = responseData.weekly_plan?.plan_data?.content;
                        setPlanId(responseData.plan_id);
                        setThreadId(responseData.thread_id);

                    } else {
                        // 기존 로직: API 호출
                        // POST /api/weekly-plans/session?user_id={user_id}
                        const payload = {
                            action: "generate", // Unified API Action
                            record_id: inbodyData?.id, // 인바디 기록 ID
                            user_goal_type: planRequest?.goal || "다이어트", // 사용자 목표 연동
                            user_goal_description: planRequest ?
                                `${planRequest.goal}를 원하며, 선호하는 운동은 ${planRequest.preferences?.join(', ') || ''}입니다. 주의사항: ${planRequest.diseases || '없음'}`
                                : "체중 감량 및 근육 증가",
                            // API 스키마에 맞춰 필드명과 타입 수정 (Array -> String)
                            preferences: planRequest?.preferences?.join(', ') || "",
                            health_specifics: planRequest?.diseases || ""
                        };

                        const res = await fetch(`/api/weekly-plans/session?user_id=${currentUserId}`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(payload)
                        });
                        if (!res.ok) throw new Error("운동 계획 생성 실패");

                        responseData = await res.json();

                        // GoalPlanResponse 처리를 위한 구조 수정
                        response = responseData.weekly_plan?.plan_data?.content;
                        setPlanId(responseData.plan_id);
                        setThreadId(responseData.thread_id);
                    }
                }

                // 성공 메시지 추가
                if (response) {
                    setMessages(prev => [
                        ...prev,
                        {
                            id: Date.now(),
                            text: responseData?.summary || response,  // 요약만 표시
                            details: responseData?.content,           // 전체 내용은 펼치기로
                            sender: 'bot'
                        }
                    ]);

                    // 인바디 분석 전문가: 카테고리별 빠른 질문 버튼 추가
                    if (botType === 'inbody-analyst') {
                        setQuickReplies([
                            "💪 근육 상세 분석",
                            "💧 체지방 상세 분석",
                            "⚖️ 균형/불균형 설명",
                            "❓ 기타 질문"
                        ]);
                    }
                }

            } catch (error) {
                console.error("초기화 오류:", error);
                setMessages(prev => [
                    ...prev,
                    { id: Date.now(), text: `죄송합니다. 초기화 중 오류가 발생했습니다: ${error.message}`, sender: 'bot' }
                ]);
            } finally {
                setIsTyping(false);
            }
        };

        if (messages.length === 1 && !hasInitialized.current) { // greeting만 있고 초기화 안된 경우
            hasInitialized.current = true;
            initChat();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []); // onMount only

    // 메시지 전송 처리 (공통 함수)
    const sendMessage = async (text) => {
        if (!text.trim()) return;

        const userMessage = {
            id: Date.now(),
            text: text,
            sender: 'user'
        };

        setMessages(prev => [...prev, userMessage]);
        setIsTyping(true);
        // 빠른 응답 버튼 숨기기 (원한다면 유지할 수도 있음) -> 유저 요청으로 유지
        // setQuickReplies([]);

        try {
            if (USE_MOCK_DATA) {
                // 1. 카테고리 감지 및 상태 업데이트
                let currentCategory = chatCategory;

                // 카테고리 진입 키워드 확인
                if (text.includes("근육 상세")) currentCategory = 'muscle';
                else if (text.includes("체지방 상세")) currentCategory = 'fat';
                else if (text.includes("균형/불균형")) currentCategory = 'balance';
                else if (text.includes("기타 질문") || text.includes("메인")) currentCategory = 'general';
                // (주의: 이미 muscle 카테고리라면 '스쿼트' 등의 단어가 와도 muscle 유지)

                // "다른 주제" 또는 "메인" 관련 키워드면 강제 초기화
                if (text.includes("다른 주제") || text.includes("메인 메뉴") || text.includes("뒤로 가기")) {
                    currentCategory = 'general';
                }

                if (currentCategory !== chatCategory) {
                    setChatCategory(currentCategory);
                }

                // 2. [시뮬레이션] LLM에 전송될 데이터 로그 출력
                console.log("📤 [Mock LLM Request] Sending to Backend:", {
                    category: currentCategory,
                    message: text,
                    user_id: currentUserId,
                    thread_id: threadId
                });

                // 3. 목업 응답 생성 (컨텍스트 기반)
                let newQuickReplies = [];
                let mockResponseText = "죄송합니다. 해당 질문에 대한 답변을 준비 중입니다.";
                let mockDetails = null;

                // (1) 근육 관련 컨텍스트
                if (currentCategory === 'muscle') {
                    // 1-1. 카테고리 진입 시 (버튼 클릭 직후) -> 질문 유도
                    if (text === "💪 근육 상세 분석") {
                        mockResponseText = `💪 **근육 분석 모드**입니다.\n\n회원님의 근육 상태에 대해 무엇이든 물어보세요!\n(예: "하체 근육 늘리는 법", "스쿼트 자세", "전체 분석 결과")`;
                        newQuickReplies = ["하체 근육 늘리는 법", "스쿼트 자세 교정해줘", "전체 상세 분석 보여줘"];

                        // 1-2. 전체 분석 요청
                    } else if (text.includes("전체 상세") || text.includes("분석 결과")) {
                        mockResponseText = `📊 **근육 상세 분석 리포트**\n\n회원님의 골격근량은 32.8kg(표준)이나, 체중 대비 근육량이 부족합니다. 특히 **하지 근육** 강화를 추천합니다.`;
                        mockDetails = `
1. **하체 강화 필요성**
   - 하체 근육은 전체 근육의 70%를 차지합니다. 하체가 튼튼해야 기초대사량이 올라갑니다.
   
2. **추천 운동**
   - 스쿼트, 런지, 레그 프레스

3. **관련 질문**
   👉 "스쿼트 자세 알려줘"`;
                        newQuickReplies = ["뒤로 가기", "스쿼트 자세 교정해줘", "하체 운동 팁 더줘"];

                        // 1-3. 구체적 운동/질문 (Loop 유지)
                    } else if (text.includes("스쿼트") || text.includes("자세")) {
                        mockResponseText = `🏋️ **스쿼트 자세 팁**\n\n1. 발은 어깨너비보다 약간 넓게 벌리세요.\n2. 무릎이 발끝을 넘지 않도록 주의하며, 엉덩이를 뒤로 빼면서 앉습니다.\n3. 허리는 곧게 펴고 시선은 정면을 유지하세요.\n\n더 궁금한 운동이 있으신가요?`;
                        newQuickReplies = ["뒤로 가기", "런지 자세 알려줘", "무릎이 아파요", "전체 상세 분석 보여줘"];
                    } else {
                        // 그 외 근육 관련 일반 질문
                        mockResponseText = `[근육 하위 질문] "${text}"에 대한 답변입니다.\n근성장을 위해서는 점진적 과부하 원칙을 적용해보세요.\n\n또 궁금한 점이 있으신가요?`;
                        newQuickReplies = ["스쿼트 자세 교정해줘", "전체 상세 분석 보여줘"];
                    }

                    // (2) 체지방 관련 컨텍스트
                } else if (currentCategory === 'fat') {
                    if (text === "💧 체지방 상세 분석") {
                        mockResponseText = `💧 **체지방 분석 모드**입니다.\n\n체지방 감량, 식단, 유산소 등 궁금한 점을 입력해주세요.`;
                        newQuickReplies = ["뒤로 가기", "내장지방 빼는 법", "공복 유산소 효과", "전체 상세 분석 보여줘"];

                    } else if (text.includes("전체 상세")) {
                        mockResponseText = `📊 **체지방 상세 분석**\n\n체지방률 18.5%(표준)이며, 복부 지방률 0.85로 관리가 필요한 단계입니다.`;
                        mockDetails = `
1. **식단 가이드**
   - 정제 탄수화물 줄이기
   
2. **운동 가이드**
   - 공복 유산소 30분 추천`;
                        newQuickReplies = ["뒤로 가기", "내장지방 빼는 식단", "유산소 운동 추천"];

                    } else {
                        mockResponseText = `[체지방 하위 질문] "${text}"에 대해 답변드립니다.\n체지방 감량은 식단이 70%, 운동이 30% 입니다.\n\n더 궁금한 점은요?`;
                        newQuickReplies = ["뒤로 가기", "내장지방 빼는 식단", "전체 상세 분석 보여줘"];
                    }

                    // (3) 균형 관련 컨텍스트
                } else if (currentCategory === 'balance') {
                    if (text === "⚖️ 균형/불균형 설명") {
                        mockResponseText = `⚖️ **신체 밸런스 모드**입니다.\n\n체형 교정이나 불균형 관련 질문을 해주세요.`;
                        newQuickReplies = ["뒤로 가기", "라운드 숄더 교정", "골반 교정 스트레칭", "전체 상세 분석 보여줘"];

                    } else if (text.includes("전체 상세")) {
                        mockResponseText = `📊 **신체 균형 분석**\n\n좌우 밸런스는 좋지만(0.98), 라운드 숄더 소견이 있어 등 운동이 필요합니다.`;
                        mockDetails = `
1. **문제점**
   - 말린 어깨 (라운드 숄더)
   
2. **해결책**
   - 등 근육 강화 (광배근, 승모근)`;
                        newQuickReplies = ["뒤로 가기", "라운드 숄더 교정 운동", "어깨 넓어지는 법"];

                    } else {
                        mockResponseText = `[체형 교정 답변] "${text}"에 대한 팁입니다.\n평소 바른 자세 유지가 가장 중요합니다.\n\n다른 고민이 있으신가요?`;
                        newQuickReplies = ["뒤로 가기", "어깨 넓어지는 운동", "전체 상세 분석 보여줘"];
                    }

                    // (4) 기타/일반
                } else {
                    if (text.includes("기타") || text.includes("메인")) {
                        mockResponseText = `❓ **무엇이든 물어보세요!**\n\n인바디 결과 외에도 운동법, 식단, 영양제 등 궁금한 점이 있다면 자유롭게 질문해주세요.\n\n💡 **인기 질문 TOP 3**`;
                        mockDetails = null; // 초기화
                        newQuickReplies = ["💪 근육 상세 분석", "💧 체지방 상세 분석", "⚖️ 균형/불균형 설명", "❓ 기타 질문"];
                    } else {
                        // 일반 대화 목업
                        mockResponseText = `네, 회원님! "${text}"에 대해 알려드릴게요.\n(일반 모드 답변)`;
                        newQuickReplies = ["뒤로 가기", "더 자세히 알려줘"];
                    }
                }

                setTimeout(() => {
                    // if (result.thread_id) setThreadId(result.thread_id); // result 미정의로 인해 주석 처리 또는 제거
                    setMessages(prev => [...prev, {
                        id: Date.now() + 1,
                        text: mockResponseText,
                        details: mockDetails,
                        sender: 'bot',
                        quickReplies: newQuickReplies
                    }]);
                }, 1000); // 1초 딜레이 시뮬레이션

                return;
            }

            // 실제 API 호출 (후속 대화)
            let endpoint = '';
            let bodyPayload = {};

            if (botType === 'inbody-analyst') {
                if (!reportId) throw new Error("분석 리포트 ID가 없습니다.");
                endpoint = `/api/analysis/${reportId}/chat`;

                // 기존 APIPayload Structure
                bodyPayload = {
                    message: text, // finalMessage construction logic below might need adjustment if we move it here, but let's keep it simple
                    thread_id: threadId
                };
            } else if (botType === 'workout-planner') {
                if (!planId) throw new Error("운동 플랜 ID가 없습니다.");
                endpoint = `/api/weekly-plans/session?user_id=${currentUserId}`;

                console.log("--- [DEBUG Frontend] sendMessage check ---");
                console.log("Current chatCategory State:", chatCategory);

                // Unified API Payload Structure
                bodyPayload = {
                    action: "chat",
                    plan_id: planId,
                    thread_id: threadId,
                    message: text,
                    feedback_category: chatCategory
                };
            }

            // 카테고리 정보가 있다면 메시지에 포함 (UI엔 표시 안 함, 백엔드 전송용)
            // 주의: chatCategory는 ID값임 ('muscle', 'fat' 등). 라벨을 찾아서 보내주자.
            let finalMessage = text;
            const currentCategories = getCurrentCategories();
            const categoryObj = currentCategories.find(c => c.id === chatCategory);

            if (categoryObj) {
                // 사용자 요청대로 [Category: Label] 형식 추가
                finalMessage = `[Category: ${categoryObj.label}] ${text}`;

                // Payload update
                if (botType === 'inbody-analyst') {
                    bodyPayload.message = finalMessage;
                } else {
                    bodyPayload.message = finalMessage;
                }
            }

            const res = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(bodyPayload)
            });

            if (!res.ok) throw new Error("메시지 전송 실패");
            const data = await res.json();

            // data = { response: "...", thread_id: "..." }

            const botMessage = {
                id: Date.now() + 1,
                text: data.reply || data.response, // reply(요약) 또는 response(전체)
                details: data.details, // 상세 내용
                sender: 'bot'
            };
            setMessages(prev => [...prev, botMessage]);

        } catch (error) {
            console.error('챗봇 응답 오류:', error);
            const errorMessage = {
                id: Date.now() + 1,
                text: "죄송합니다. 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                sender: 'bot'
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsTyping(false);
        }
    };

    const handleSend = (e) => {
        e.preventDefault();
        if (inputValue.trim()) {
            sendMessage(inputValue);
            setInputValue('');
        }
    };

    const handleQuickReply = (text) => {
        // 카테고리 선택 시 chatCategory 업데이트만 수행 (바로 전송 X)
        const currentCategories = getCurrentCategories();

        // text가 value로 들어오므로, value로 매칭되는 카테고리 찾기
        const category = currentCategories.find(cat => cat.value === text);

        if (category) {
            // 이미 선택된 카테고리를 다시 누르면 해제 기능도 추가하면 좋음 (선택사항)
            if (chatCategory === category.id) {
                setChatCategory(null); // 해제
            } else {
                setChatCategory(category.id); // 선택
            }
        } else {
            // 카테고리가 아닌 일반 텍스트 퀵버튼일 경우 그냥 전송
            sendMessage(text);
        }
    };

    // ==============================================
    // 채팅 히스토리 관리 함수들
    // ==============================================

    // localStorage에서 현재 botType에 맞는 대화 목록만 조회
    const getChatHistories = () => {
        try {
            const all = JSON.parse(localStorage.getItem('chatHistories') || '[]');
            return all.filter(chat => chat.botType === botType);
        } catch (error) {
            console.error('채팅 히스토리 로드 오류:', error);
            return [];
        }
    };

    // 현재 대화를 localStorage에 저장
    const saveChatHistory = () => {
        if (messages.length <= 1) return; // 초기 메시지만 있으면 저장 안함

        // state 대신 ref를 사용하여 최신 chatId 확인
        let chatId = chatIdRef.current;
        if (!chatId) {
            // ID가 없으면 새로 생성 후 Ref 및 State 업데이트
            chatId = `chat_${Date.now()}_${botType}`;
            chatIdRef.current = chatId;
            setCurrentChatId(chatId);
        }

        const firstUserMessage = messages.find(m => m.sender === 'user');
        const title = firstUserMessage ? firstUserMessage.text.substring(0, 30) + '...' : '새 대화';
        const lastMessage = messages[messages.length - 1];

        const chatData = {
            id: chatId,
            botType: botType,
            title: title,
            timestamp: Date.now(),
            messages: messages,
            lastMessage: lastMessage.text.substring(0, 50) + '...',
            threadId: threadId // 스레드 ID 저장 (컨텍스트 유지용)
        };

        try {
            const all = JSON.parse(localStorage.getItem('chatHistories') || '[]');
            const existingIndex = all.findIndex(chat => chat.id === chatId);

            if (existingIndex >= 0) {
                all[existingIndex] = chatData; // 업데이트
            } else {
                all.push(chatData); // 새로 추가
            }

            localStorage.setItem('chatHistories', JSON.stringify(all));
        } catch (error) {
            console.error('채팅 히스토리 저장 오류:', error);
        }
    };

    // 특정 대화를 불러오기
    const loadChatHistory = (chatId) => {
        try {
            const all = JSON.parse(localStorage.getItem('chatHistories') || '[]');
            const chat = all.find(c => c.id === chatId);

            if (chat && chat.botType === botType) {
                setMessages(chat.messages);
                setCurrentChatId(chatId);
                setShowHistorySidebar(false);

                // 스레드 ID 복원 및 Ref 업데이트
                if (chat.threadId) {
                    setThreadId(chat.threadId);
                }
                chatIdRef.current = chatId;
            }
        } catch (error) {
            console.error('채팅 히스토리 불러오기 오류:', error);
        }
    };

    // 새 대화 시작
    const startNewChat = () => {
        setMessages([{ id: 1, text: config.greeting, sender: 'bot' }]);
        setCurrentChatId(null);
        setChatCategory(null);
        setShowHistorySidebar(false);
    };

    return (
        <div className="chatbot-container fade-in">
            <header className="chatbot-header" style={{ borderBottomColor: config.color }}>
                <div className="bot-info">
                    <div className="bot-avatar" style={{
                        width: '48px',
                        height: '48px',
                        borderRadius: '16px',
                        background: config.gradient,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '24px',
                        boxShadow: '0 4px 16px rgba(0,0,0,0.12)',
                        flexShrink: 0
                    }}>
                        {config.icon}
                    </div>
                    <div>
                        <h3>{config.name}</h3>
                        <span className="status-online">Online</span>
                    </div>
                </div>

                {/* 오른좍 버튼들 */}
                <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                        onClick={startNewChat}
                        style={{
                            background: 'transparent',
                            border: 'none',
                            borderRadius: '10px',
                            padding: '8px 12px',
                            fontSize: '0.9rem',
                            cursor: 'pointer',
                            transition: 'all 0.2s ease',
                            color: '#64748b',
                            fontWeight: '500',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px'
                        }}
                        onMouseEnter={(e) => {
                            e.currentTarget.style.background = '#f1f5f9';
                            e.currentTarget.style.color = '#334155';
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.background = 'transparent';
                            e.currentTarget.style.color = '#64748b';
                        }}
                    >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <line x1="12" y1="5" x2="12" y2="19"></line>
                            <line x1="5" y1="12" x2="19" y2="12"></line>
                        </svg>
                        새 대화
                    </button>
                    <button
                        onClick={() => setShowHistorySidebar(true)}
                        style={{
                            background: 'rgba(139, 92, 246, 0.08)',
                            border: 'none',
                            borderRadius: '10px',
                            padding: '8px 14px',
                            fontSize: '0.9rem',
                            cursor: 'pointer',
                            transition: 'all 0.2s ease',
                            color: '#8b5cf6',
                            fontWeight: '600',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px'
                        }}
                        onMouseEnter={(e) => {
                            e.currentTarget.style.background = '#8b5cf6';
                            e.currentTarget.style.color = 'white';
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.background = 'rgba(139, 92, 246, 0.08)';
                            e.currentTarget.style.color = '#8b5cf6';
                        }}
                    >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                        </svg>
                        대화 기록
                    </button>
                </div>
            </header >

            <div className="chat-messages">
                {messages.map((msg) => (
                    <React.Fragment key={msg.id}>
                        <div className={`message-bubble-wrapper ${msg.sender}`}>
                            {msg.sender === 'bot' ? (
                                <div className="avatar" style={{
                                    width: '36px',
                                    height: '36px',
                                    borderRadius: '12px',
                                    background: config.gradient,
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    fontSize: '18px',
                                    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                                    flexShrink: 0
                                }}>
                                    {config.icon}
                                </div>
                            ) : (
                                <div className="avatar">
                                    <User size={20} />
                                </div>
                            )}
                            <div className="message-bubble">
                                {/* =======================================================
                                [마크다운 렌더링 수정] 
                                ReactMarkdown을 사용하여 텍스트 포맷팅을 개선함.
                                remarkGfm 플러그인을 사용하여 테이블, 리스트 등 확장 문법 지원.
                                ======================================================= */}
                                <div className="markdown-content">
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                        {msg.text}
                                    </ReactMarkdown>
                                </div>

                                {/* 상세 내용 (펼치기 기능) */}
                                {msg.details && (
                                    <details style={{ marginTop: '12px', borderTop: '1px solid rgba(0,0,0,0.1)', paddingTop: '8px' }}>
                                        <summary style={{
                                            cursor: 'pointer',
                                            color: '#667eea',
                                            fontWeight: '600',
                                            fontSize: '0.9rem',
                                            outline: 'none',
                                            listStyle: 'none'
                                        }}>
                                            📋 상세 분석 결과 펼쳐보기
                                        </summary>
                                        <div style={{
                                            marginTop: '10px',
                                            fontSize: '0.9rem',
                                            color: '#334155',
                                            lineHeight: '1.6',
                                            background: 'rgba(255,255,255,0.5)',
                                            padding: '12px',
                                            borderRadius: '8px'
                                        }}>
                                            {/* 상세 내용도 마크다운으로 렌더링 */}
                                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                                {msg.details}
                                            </ReactMarkdown>
                                        </div>
                                    </details>
                                )}
                            </div>
                        </div>

                        {/* 예상질문 버튼 (말풍선 바로 아래) */}
                        {
                            msg.sender === 'bot' && msg.quickReplies && msg.quickReplies.length > 0 && (
                                <div style={{
                                    display: 'flex',
                                    gap: '6px',
                                    flexWrap: 'wrap',
                                    marginTop: '16px'
                                }}>
                                    {msg.quickReplies.map((reply, idx) => (
                                        <button
                                            key={idx}
                                            onClick={() => handleQuickReply(reply)}
                                            style={{
                                                background: 'white',
                                                border: '1px solid #e2e8f0',
                                                borderRadius: '14px',
                                                padding: '8px 16px',
                                                fontSize: '0.85rem',
                                                color: '#64748b',
                                                cursor: 'pointer',
                                                transition: 'all 0.2s',
                                                boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
                                            }}
                                            onMouseEnter={(e) => {
                                                e.target.style.background = '#f8fafc';
                                                e.target.style.borderColor = '#cbd5e1';
                                                e.target.style.color = '#475569';
                                            }}
                                            onMouseLeave={(e) => {
                                                e.target.style.background = 'white';
                                                e.target.style.borderColor = '#e2e8f0';
                                                e.target.style.color = '#64748b';
                                            }}
                                        >
                                            {reply}
                                        </button>
                                    ))}
                                </div>
                            )
                        }
                    </React.Fragment>
                ))}
                {isTyping && (
                    <div className="message-bubble-wrapper bot">
                        <div className="avatar" style={{
                            width: '36px',
                            height: '36px',
                            borderRadius: '12px',
                            background: config.gradient,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '18px',
                            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                            flexShrink: 0
                        }}>
                            {config.icon}
                        </div>
                        <div className="message-bubble typing">
                            <span className="dot"></span>
                            <span className="dot"></span>
                            <span className="dot"></span>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* 차단된 빠른 응답 버튼 영역 (사용 안 함) */}
            {/* {quickReplies.length > 0 && !isTyping && (
                <div className="quick-replies-container">
                    {quickReplies.map((reply, index) => (
                        <button
                            key={index}
                            className="quick-reply-chip"
                            onClick={() => handleQuickReply(reply)}
                        >
                            {reply}
                        </button>
                    ))}
                </div>
            )} */}

            {/* 고정 카테고리 버튼 영역 */}
            {
                <div style={{
                    position: 'fixed',
                    bottom: '90px',
                    left: 0,
                    right: 0,
                    background: 'linear-gradient(to top, #ffffff 90%, rgba(255,255,255,0))',
                    paddingTop: '20px',
                    paddingBottom: '10px',
                    borderTop: '1px solid #f1f5f9',
                    zIndex: 900
                }}>
                    <div style={{
                        textAlign: 'center',
                        fontSize: '0.75rem',
                        color: '#94a3b8',
                        marginBottom: '8px',
                        fontWeight: '500'
                    }}>
                        📋 관심있는 주제를 선택해주세요
                    </div>
                    <div style={{
                        display: 'flex',
                        gap: '8px',
                        overflowX: 'auto',
                        padding: '0 16px',
                        scrollbarWidth: 'none',
                        msOverflowStyle: 'none'
                    }}>
                        {getCurrentCategories().map((cat) => (
                            <button
                                key={cat.id}
                                onClick={() => handleQuickReply(cat.value)}
                                style={{
                                    background: chatCategory === cat.id ? '#8b5cf6' : 'white',
                                    color: chatCategory === cat.id ? 'white' : '#475569',
                                    border: chatCategory === cat.id ? '2px solid #8b5cf6' : '2px solid #e2e8f0',
                                    borderRadius: '20px',
                                    padding: '10px 16px',
                                    fontSize: '0.85rem',
                                    fontWeight: '600',
                                    cursor: 'pointer',
                                    transition: 'all 0.2s',
                                    whiteSpace: 'nowrap',
                                    boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
                                    flexShrink: 0
                                }}
                                onMouseEnter={(e) => {
                                    if (chatCategory !== cat.id) {
                                        e.target.style.borderColor = '#cbd5e1';
                                        e.target.style.background = '#f8fafc';
                                    }
                                }}
                                onMouseLeave={(e) => {
                                    if (chatCategory !== cat.id) {
                                        e.target.style.borderColor = '#e2e8f0';
                                        e.target.style.background = 'white';
                                    }
                                }}
                            >
                                {cat.label}
                            </button>
                        ))}
                    </div>
                </div>
            }

            {/* 청팅 히스토리 사이드바 */}
            {showHistorySidebar && (
                <>
                    {/* Overlay */}
                    <div
                        onClick={() => setShowHistorySidebar(false)}
                        style={{
                            position: 'fixed',
                            top: 0,
                            left: 0,
                            right: 0,
                            bottom: 0,
                            background: 'rgba(0,0,0,0.4)',
                            zIndex: 1000,
                            animation: 'fadeIn 0.3s'
                        }}
                    />


                    {/* Sidebar - 모바일/데스크탑 모두 오른싪에서 슬라이드 */}
                    <div style={{
                        position: 'fixed',
                        top: 0,
                        right: 0,
                        bottom: 0,
                        left: 'auto',
                        width: typeof window !== 'undefined' && window.innerWidth > 768 ? '400px' : '85vw',
                        maxWidth: '400px',
                        background: 'white',
                        boxShadow: '-4px 0 20px rgba(0,0,0,0.15)',
                        zIndex: 1001,
                        display: 'flex',
                        flexDirection: 'column'
                    }}>
                        {/* Header */}
                        <div style={{
                            padding: '20px',
                            borderBottom: '1px solid #e2e8f0',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center'
                        }}>
                            <h3 style={{ margin: 0, fontSize: '1.2rem', color: '#1e293b' }}>
                                📋 이전 대화
                            </h3>
                            <button
                                onClick={() => setShowHistorySidebar(false)}
                                style={{
                                    background: 'none',
                                    border: 'none',
                                    fontSize: '1.5rem',
                                    cursor: 'pointer',
                                    color: '#64748b'
                                }}
                            >
                                ×
                            </button>
                        </div>

                        {/* Chat List */}
                        <div style={{
                            flex: 1,
                            overflowY: 'auto',
                            padding: '16px'
                        }}>
                            {chatHistories.length === 0 ? (
                                <div style={{
                                    textAlign: 'center',
                                    padding: '40px 20px',
                                    color: '#94a3b8'
                                }}>
                                    아직 저장된 대화가 없습니다.
                                </div>
                            ) : (
                                chatHistories
                                    .sort((a, b) => b.timestamp - a.timestamp)
                                    .map((chat) => (
                                        <div
                                            key={chat.id}
                                            onClick={() => loadChatHistory(chat.id)}
                                            style={{
                                                padding: '14px',
                                                marginBottom: '8px',
                                                borderRadius: '12px',
                                                border: currentChatId === chat.id ? '2px solid #8b5cf6' : '1px solid #e2e8f0',
                                                background: currentChatId === chat.id ? '#f5f3ff' : 'white',
                                                cursor: 'pointer',
                                                transition: 'all 0.2s'
                                            }}
                                            onMouseEnter={(e) => {
                                                if (currentChatId !== chat.id) {
                                                    e.currentTarget.style.background = '#f8fafc';
                                                }
                                            }}
                                            onMouseLeave={(e) => {
                                                if (currentChatId !== chat.id) {
                                                    e.currentTarget.style.background = 'white';
                                                }
                                            }}
                                        >
                                            <div style={{
                                                fontSize: '0.9rem',
                                                fontWeight: '600',
                                                color: '#1e293b',
                                                marginBottom: '6px',
                                                overflow: 'hidden',
                                                textOverflow: 'ellipsis',
                                                whiteSpace: 'nowrap'
                                            }}>
                                                {chat.title}
                                            </div>
                                            <div style={{
                                                fontSize: '0.75rem',
                                                color: '#94a3b8',
                                                marginBottom: '4px'
                                            }}>
                                                {new Date(chat.timestamp).toLocaleString('ko-KR', {
                                                    month: 'short',
                                                    day: 'numeric',
                                                    hour: '2-digit',
                                                    minute: '2-digit'
                                                })}
                                            </div>
                                            <div style={{
                                                fontSize: '0.8rem',
                                                color: '#64748b',
                                                overflow: 'hidden',
                                                textOverflow: 'ellipsis',
                                                whiteSpace: 'nowrap'
                                            }}>
                                                {chat.lastMessage}
                                            </div>
                                        </div>
                                    ))
                            )}
                        </div>
                    </div>
                </>
            )}

            {/* 카테고리 선택됨 표시 UI 추가 */}
            {chatCategory && (
                <div style={{
                    position: 'fixed',
                    bottom: '80px',
                    left: '20px',
                    right: '20px',
                    maxWidth: '800px',
                    margin: '0 auto',
                    zIndex: 100,
                    display: 'flex',
                    pointerEvents: 'none'
                }}>
                    <div className="selected-category-indicator" style={{
                        padding: '6px 16px',
                        background: 'rgba(255, 255, 255, 0.9)',
                        backdropFilter: 'blur(8px)',
                        color: '#6366f1',
                        borderRadius: '20px',
                        fontSize: '0.9rem',
                        fontWeight: '600',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '8px',
                        boxShadow: '0 4px 12px rgba(99, 102, 241, 0.15)',
                        border: '1px solid rgba(99, 102, 241, 0.2)',
                        pointerEvents: 'auto'
                    }}>
                        <span>💬 대화 주제: {getCategoryLabel()}</span>
                        <button
                            type="button"
                            onClick={() => setChatCategory(null)}
                            style={{
                                border: 'none',
                                background: 'transparent',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                padding: '4px',
                                color: '#ef4444',
                                marginLeft: '4px'
                            }}
                            title="주제 취소"
                        >
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <line x1="18" y1="6" x2="6" y2="18"></line>
                                <line x1="6" y1="6" x2="18" y2="18"></line>
                            </svg>
                        </button>
                    </div>
                </div>
            )}

            <form className="chat-input-area" onSubmit={handleSend} style={{ bottom: '20px' }}>
                <input
                    type="text"
                    placeholder={chatCategory ? "메시지를 입력하세요..." : "위에서 카테고리를 먼저 선택해주세요"}
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    disabled={isTyping || !chatCategory}
                />
                <button type="submit" className="send-btn" disabled={!inputValue.trim() || isTyping || !chatCategory}>
                    <Send size={20} />
                </button>
            </form>

            <style>{`
                .quick-replies-container {
                    position: fixed;
                    bottom: 140px;
                    left: 20px;
                    right: 20px;
                    padding: 0;
                    display: flex;
                    gap: 10px; /* 간격 조금 늘림 */
                    flex-wrap: wrap;
                    animation: fadeIn 0.3s ease-out;
                    z-index: 899;
                    justify-content: center; /* 가운데 정렬 */
                }
                .quick-reply-chip {
                    background: white;
                    border: 1px solid #e2e8f0;
                    border-radius: 24px; /* 둥글기 조정 */
                    padding: 12px 20px; /* 크기 키움 */
                    font-size: 1rem; /* 글자 크기 키움 */
                    color: #475569;
                    cursor: pointer;
                    transition: all 0.2s cubic-bezier(0.18, 0.89, 0.32, 1.28);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                    white-space: nowrap;
                    font-weight: 500; /* 글자 두께 약간 추가 */
                }
                .quick-reply-chip:hover {
                    background: #f1f5f9;
                    border-color: #cbd5e1;
                    transform: translateY(-2px);
                    box-shadow: 0 6px 16px rgba(0,0,0,0.12);
                    color: #1e293b;
                }
                .quick-reply-chip:active {
                    transform: translateY(0);
                }
                /* App.css 오버라이드 */
                .chat-input-area {
                    bottom: 20px !important; 
                    transition: all 0.3s ease;
                }
                
                /* =======================================================
                   [마크다운 스타일링] 
                   LLM 응답 텍스트(헤더, 리스트, 볼드체 등)를 디자인함.
                   ======================================================= */
                .markdown-content {
                    font-size: 0.95rem;
                    line-height: 1.6;
                    color: inherit;
                }
                .markdown-content p {
                    margin: 0 0 8px 0;
                }
                .markdown-content p:last-child {
                    margin-bottom: 0;
                }
                .markdown-content strong {
                    font-weight: 700;
                    color: inherit; 
                }
                .markdown-content ul, .markdown-content ol {
                    margin: 8px 0;
                    padding-left: 10px; /* 들여쓰기 더 축소 (15px -> 10px) */
                }
                .markdown-content li {
                    margin-bottom: 4px;
                }
                .markdown-content h1, .markdown-content h2, .markdown-content h3 {
                    margin: 12px 0 8px 0;
                    font-weight: 700;
                    font-size: 1.1em;
                }
                .markdown-content h1:first-child, 
                .markdown-content h2:first-child, 
                .markdown-content h3:first-child {
                    margin-top: 0;
                }
                .markdown-content blockquote {
                    border-left: 3px solid rgba(0,0,0,0.2);
                    margin: 8px 0;
                    padding-left: 12px;
                    font-style: italic;
                }
                
                /* 봇 메시지(흰 배경)에서의 강조 색상: 인디고 */
                .message-bubble.bot .markdown-content strong {
                    color: #4f46e5;
                }

                /* 모바일 대응 */
                @media (max-width: 768px) {
                   .chat-input-area {
                        bottom: 10px !important;
                   }
                   .quick-replies-container {
                        bottom: 90px;
                        left: 0; /* 전체 너비 사용 */
                        right: 0;
                        gap: 12px; 
                        flex-wrap: nowrap; /* 줄바꿈 방지 */
                        overflow-x: auto; /* 가로 스크롤 허용 */
                        justify-content: flex-start; /* 왼쪽부터 시작 */
                        padding: 0 16px; /* 좌우 여백 */
                        -webkit-overflow-scrolling: touch; /* 부드러운 스크롤 */
                        /* 스크롤바 숨기기 */
                        scrollbar-width: none; 
                        -ms-overflow-style: none;
                   }
                   .quick-replies-container::-webkit-scrollbar {
                        display: none;
                   }
                   
                   .quick-reply-chip {
                        padding: 10px 18px;
                        font-size: 0.95rem;
                        flex-shrink: 0; /* 찌그러짐 방지 */
                   }
                   .chatbot-container {
                        height: 100vh !important; 
                   }
                }
            `}</style>
        </div >
    );
};

export default Chatbot;
