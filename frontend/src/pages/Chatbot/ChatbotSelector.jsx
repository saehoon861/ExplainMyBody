import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, ArrowRight, X, TrendingUp, Activity, Zap, FileText, AlertCircle, Loader2, Lock } from 'lucide-react';
import '../../styles/LoginLight.css';
import { getUserHealthRecords } from '../../services/inbodyService';
import ExercisePlanPopup from '../../components/common/ExercisePlanPopup';
import LoadingAnimation from '../../components/common/LoadingAnimation';

// ============================================
// 목업 설정
// 환경 변수로 목업 모드 관리 (.env 파일에서 설정)
const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === 'true';

// 목업 인바디 데이터
const MOCK_INBODY_DATA = {
    id: 1,
    created_at: new Date().toISOString(),
    body_type1: '표준 체형',
    measurements: {
        "체중관리": { "체중": 72.5, "골격근량": 32.8 },
        "비만분석": { "체지방률": 18.5, "BMI": 23.2 }
    }
};

// 목업 사용자 설정 데이터 (이미 선택된 값 시뮬레이션)
const MOCK_USER_SETTINGS = {
    goal: '다이어트',
    preferences: ['헬스장(웨이트)', '러닝/유산소'],
    diseases: '허리 디스크 약간 있음'
};

const ChatbotSelector = () => {
    const navigate = useNavigate();
    const [showInbodyPopup, setShowInbodyPopup] = useState(false);
    const [showExercisePopup, setShowExercisePopup] = useState(false);  // 운동 설정 팝업 상태
    // OCR 검사 안내 팝업 (OCR 데이터가 없을 때)
    const [showNoDataPopup, setShowNoDataPopup] = useState(false);
    const [latestInbodyData, setLatestInbodyData] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    // 팝업 타입 상태 ('ocr': OCR 안내, 'guide': 분석가 안내)
    const [popupType, setPopupType] = useState('ocr');
    // 분석 중 상태 (로딩 애니메이션 표시용)
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [analyzeProgress, setAnalyzeProgress] = useState(0);
    const [analyzeMessage, setAnalyzeMessage] = useState('');

    // 인바디 데이터 로드
    useEffect(() => {
        const loadInbodyData = async () => {
            if (USE_MOCK_DATA) {
                // 테스트: 데이터 있음 (잠금 해제)
                setLatestInbodyData(MOCK_INBODY_DATA);

                // 테스트: 데이터 없음 (잠금 확인용)
                // setLatestInbodyData(null);

                setIsLoading(false);
                return;
            }

            const userData = JSON.parse(localStorage.getItem('user'));
            if (!userData || !userData.id) return;

            setIsLoading(true);
            try {

                const records = await getUserHealthRecords(userData.id, 1);
                if (records && records.length > 0) {
                    setLatestInbodyData(records[0]);
                }
            } catch (error) {
                console.error('인바디 데이터 로드 실패:', error);
            } finally {
                setIsLoading(false);
            }
        };

        loadInbodyData();
    }, []);

    const handleBotClick = (botId) => {
        // 데이터가 없는 경우 처리 (목업 모드 제외)
        if (!latestInbodyData && !USE_MOCK_DATA) {
            if (botId === 'workout-planner') {
                // 운동 플래너 클릭 시 -> "인바디 분석 전문가 먼저 이용하세요" 안내
                setPopupType('guide');
                setShowNoDataPopup(true);
                return;
            } else if (botId === 'inbody-analyst') {
                // 인바디 분석가 클릭 시 -> "OCR 검사 하러가기" 안내
                setPopupType('ocr');
                setShowNoDataPopup(true);
                return;
            }
        }

        if (botId === 'inbody-analyst') {
            // 데이터가 있으면 인바디 정보 팝업 표시
            setShowInbodyPopup(true);
        } else if (botId === 'workout-planner') {
            // 운동 플래너: 팝업 무조건 표시 (저장된 정보 있으면 read-only로 보여줌)
            setShowExercisePopup(true);
        } else {
            // 그 외 (예비용)
            const userData = JSON.parse(localStorage.getItem('user'));
            const userId = userData?.id || 1;

            navigate(`/chatbot/${botId}`, {
                state: {
                    inbodyData: latestInbodyData,
                    userId: userId
                }
            });
        }
    };

    const handleExercisePlanSubmit = async (data) => {
        // 팝업 닫기 및 분석 모드 시작
        setShowExercisePopup(false);
        setIsAnalyzing(true);
        setAnalyzeMessage('맞춤 플랜 생성 중...');
        setAnalyzeProgress(0);

        // 운동 설정 정보를 localStorage에 저장
        localStorage.setItem('exerciseSettings', JSON.stringify(data));

        const userData = JSON.parse(localStorage.getItem('user'));
        const userId = userData?.id || 1;

        try {
            // 1. 프로그레스 바 시뮬레이션 (최소 2초 동안 95%까지)
            let currentProgress = 0;
            const progressInterval = setInterval(() => {
                setAnalyzeProgress(prev => {
                    const next = prev + Math.floor(Math.random() * 5) + 2;
                    return next >= 95 ? 95 : next;
                });
            }, 200);

            // 2. API 호출을 즉시 시작
            const apiCall = (async () => {
                if (USE_MOCK_DATA) {
                    await new Promise(resolve => setTimeout(resolve, 2000));
                    return { mockData: true };
                } else {
                    const payload = {
                        action: "generate",
                        record_id: latestInbodyData?.id,
                        user_goal_type: data.goal || "다이어트",
                        user_goal_description: `${data.goal || '건강관리'}를 원하며, 선호하는 운동은 ${data.preferences?.join(', ') || '없음'}입니다. 특이사항: ${data.diseases || '없음'}`,
                        preferences: data.preferences?.join(', ') || "",
                        health_specifics: data.diseases || ""
                    };

                    const res = await fetch(`/api/weekly-plans/session?user_id=${userId}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });

                    if (!res.ok) {
                        const errorMsg = await res.text();
                        throw new Error(`운동 계획 생성 실패: ${errorMsg}`);
                    }
                    return await res.json();
                }
            })();

            // 3. API 응답 대기
            const responseData = await apiCall;

            // 4. 완료 처리 (100% 채우기)
            clearInterval(progressInterval);
            setAnalyzeProgress(100);
            setAnalyzeMessage('생성 완료!');

            // 100%를 보여주기 위한 짧은 대기 후 네비게이션
            await new Promise(r => setTimeout(r, 600));

            // 네비게이션 직전에 분석 상태 해제 (필요시)
            // setIsAnalyzing(false); // 페이지 이동 중에는 로딩 상태를 유지하는 것이 좋습니다

            navigate('/chatbot/workout-planner', {
                state: {
                    planRequest: data,
                    userId: userId,
                    inbodyData: latestInbodyData,
                    planResult: responseData
                },
                replace: true // 뒤로가기 방지 및 스택 관리
            });

        } catch (error) {
            console.error('운동 계획 생성 실패:', error);
            setIsAnalyzing(false);
            alert('운동 계획 생성 중 문제가 발생했습니다. 다시 시도해주세요.');
        }
    };

    const handleExercisePlanSubmit = (data) => {
        setShowExercisePopup(false);

        // 운동 설정 정보를 localStorage에 저장 (다음번에 바로 사용)
        localStorage.setItem('exerciseSettings', JSON.stringify(data));

        // localStorage에서 사용자 정보 가져오기
        const userData = JSON.parse(localStorage.getItem('user'));
        const userId = userData?.id || 1; // 로그인된 사용자 ID

        navigate('/chatbot/workout-plan', {
            state: {
                planRequest: data,
                userId: userId,
                inbodyData: latestInbodyData
            }
        });
    };

    /**
     * AI 정밀분석 버튼 클릭 핸들러
     */
    /**
     * AI 정밀분석 버튼 클릭 핸들러
     * - 버튼 클릭 시 즉시 API 요청 시작
     * - 로딩 중 실제 데이터 대기
     * - 데이터 수신 후 채팅 페이지로 이동
     */
    /**
     * AI 정밀분석 버튼 클릭 핸들러
     * - 버튼 클릭 시 즉시 API 요청 시작
     * - 로딩 중 실제 데이터 대기
     * - 데이터 수신 후 채팅 페이지로 이동
     */
    const handleStartAnalysis = async () => {
        setIsAnalyzing(true);
        setAnalyzeProgress(0);
        setAnalyzeMessage('분석 요청 중...');

        // 사용자 정보
        const userData = JSON.parse(localStorage.getItem('user'));
        const userId = userData?.id || 1;

        try {
            // 1. 프로그레스 바 시작 (90%까지 천천히 증가)
            const progressInterval = setInterval(() => {
                setAnalyzeProgress(prev => {
                    if (prev >= 90) return prev;
                    return prev + 10; // 10%씩 증가
                });
            }, 500); // 0.5초마다 증가

            let responseData = null;

            if (USE_MOCK_DATA) {
                // 목업 데이터 시뮬레이션 (2초 대기)
                await new Promise(resolve => setTimeout(resolve, 2000));

                // 목업 응답 데이터 구성 (Chatbot.jsx에서 사용하는 구조와 동일하게)
                responseData = {
                    mockData: true // 목업임을 표시
                };
            } else {
                // 실제 API 호출
                const recordId = latestInbodyData?.id;
                if (!recordId) throw new Error("분석할 인바디 기록이 없습니다.");

                const res = await fetch(`/api/analysis/${recordId}?user_id=${userId}`, {
                    method: 'POST'
                });

                if (!res.ok) throw new Error("분석 리포트 생성 실패");
                responseData = await res.json();
            }

            // 완료 처리
            clearInterval(progressInterval);
            setAnalyzeProgress(100);
            setAnalyzeMessage('분석 완료!');

            await new Promise(resolve => setTimeout(resolve, 500)); // 100% 보여주기 위한 짧은 대기

            setShowInbodyPopup(false);
            setIsAnalyzing(false);

            // 데이터와 함께 이동
            navigate('/chatbot/inbody-analyst', {
                state: {
                    inbodyData: latestInbodyData,
                    userId: userId,
                    analysisResult: responseData // ✅ 미리 가져온 분석 결과 전달
                }
            });

        } catch (error) {
            console.error('분석 요청 실패:', error);
            setAnalyzeMessage('오류 발생');
            setIsAnalyzing(false);
            alert('분석 요청 중 오류가 발생했습니다. 다시 시도해주세요.');
        }
    };

    const bots = [
        {
            id: 'inbody-analyst',
            name: '인바디 분석 전문가',
            desc: '식단, 운동, 생활습관 등 전반적인 건강 상담을 도와드립니다.',
            icon: '🧑‍⚕️',
            gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            features: ['맞춤 상담', '식단 대안', '동기 부여']
        },
        {
            id: 'workout-planner',
            name: '운동 플래너 전문가',
            desc: '개인 맞춤형 운동 루틴과 자세 교정을 도와드립니다.',
            icon: '🏋️',
            gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
            features: ['운동 루틴', '자세 교정', '체력 증진']
        }
    ];

    return (
        <div className="main-content fade-in" style={{ padding: '24px 20px', minHeight: '100vh', background: 'linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%)' }}>
            <header style={{ textAlign: 'center', marginBottom: '48px', paddingTop: '20px' }}>
                <div style={{
                    display: 'inline-flex',
                    padding: '16px',
                    background: 'linear-gradient(135deg, #e0e7ff 0%, #f3e8ff 100%)', // 부드러운 파스텔 그라디언트
                    borderRadius: '24px',
                    marginBottom: '20px',
                    boxShadow: '0 8px 32px rgba(99, 102, 241, 0.15)',
                    border: '1px solid rgba(255,255,255,0.5)'
                }}>
                    <Sparkles size={32} color="#6366f1" />
                </div>
                <h1 style={{
                    fontSize: '2rem',
                    fontWeight: 800,
                    color: '#1e293b',
                    marginBottom: '8px',
                    letterSpacing: '-0.03em'
                }}>AI 상담소</h1>
                <p style={{ color: '#64748b', fontSize: '1rem' }}>전문 분야별 AI 코칭을 받아보세요</p>
            </header>

            <div style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '20px',
                maxWidth: '480px',
                margin: '0 auto'
            }}>
                {bots.map((bot, index) => {
                    // workout-planner인 경우 데이터 없으면 잠김 처리 (목업 모드 제외)
                    const isLocked = bot.id === 'workout-planner' && !latestInbodyData && !USE_MOCK_DATA;

                    return (
                        <div
                            key={bot.id}
                            onClick={() => handleBotClick(bot.id)}
                            style={{
                                background: 'rgba(255, 255, 255, 0.9)',
                                backdropFilter: 'blur(20px)',
                                borderRadius: '28px',
                                padding: '28px',
                                cursor: 'pointer',
                                transition: 'all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)',
                                border: '1px solid rgba(255, 255, 255, 0.8)',
                                boxShadow: '0 4px 24px rgba(0,0,0,0.06)',
                                animation: 'premiumFade 0.5s ease-out forwards',
                                animationDelay: `${index * 0.1}s`,
                                opacity: 0,
                                position: 'relative',
                                overflow: 'hidden'
                            }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.transform = 'translateY(-4px) scale(1.01)';
                                e.currentTarget.style.boxShadow = '0 20px 40px rgba(0,0,0,0.12)';
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.transform = 'translateY(0) scale(1)';
                                e.currentTarget.style.boxShadow = '0 4px 24px rgba(0,0,0,0.06)';
                            }}
                        >

                            {/* 잠금 오버레이 */}
                            {isLocked && (
                                <div style={{
                                    position: 'absolute',
                                    top: 0,
                                    left: 0,
                                    right: 0,
                                    bottom: 0,
                                    background: 'rgba(255, 255, 255, 0.4)',
                                    zIndex: 10,
                                    display: 'flex',
                                    flexDirection: 'column',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    backdropFilter: 'blur(12px)',
                                    transition: 'all 0.3s ease'
                                }}>
                                    <div style={{
                                        background: 'linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 100%)',
                                        borderRadius: '20px',
                                        padding: '16px',
                                        marginBottom: '12px',
                                        boxShadow: '0 8px 16px rgba(0,0,0,0.1)',
                                        border: '1px solid rgba(255,255,255,0.5)'
                                    }}>
                                        <Lock size={28} color="#64748b" />
                                    </div>
                                    <span style={{
                                        fontSize: '0.95rem',
                                        fontWeight: 800,
                                        color: '#475569',
                                        background: 'rgba(255, 255, 255, 0.9)',
                                        padding: '8px 16px',
                                        borderRadius: '16px',
                                        boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                                        border: '1px solid rgba(255,255,255,0.8)',
                                        letterSpacing: '-0.02em'
                                    }}>
                                        인바디 분석 필요
                                    </span>
                                </div>
                            )}

                            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '18px', opacity: isLocked ? 0.5 : 1 }}>
                                {/* Profile Icon */}
                                <div style={{
                                    width: '64px',
                                    height: '64px',
                                    borderRadius: '20px',
                                    background: index === 0
                                        ? 'linear-gradient(135deg, #e0e7ff 0%, #eef2ff 100%)'
                                        : 'linear-gradient(135deg, #fce7f3 0%, #fdf2f8 100%)',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    fontSize: '32px',
                                    boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
                                    flexShrink: 0
                                }}>
                                    {bot.icon}
                                </div>

                                {/* Content */}
                                <div style={{ flex: 1, minWidth: 0 }}>
                                    <h2 style={{
                                        fontSize: '1.2rem',
                                        fontWeight: 700,
                                        color: '#1e293b',
                                        marginBottom: '6px',
                                        letterSpacing: '-0.02em'
                                    }}>
                                        {bot.name}
                                    </h2>
                                    <p style={{
                                        color: '#64748b',
                                        fontSize: '0.88rem',
                                        lineHeight: 1.5,
                                        marginBottom: '14px'
                                    }}>
                                        {bot.desc}
                                    </p>

                                    {/* Feature Tags */}
                                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                                        {bot.features.map(f => (
                                            <span
                                                key={f}
                                                style={{
                                                    padding: '6px 12px',
                                                    background: 'linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%)',
                                                    color: '#475569',
                                                    borderRadius: '20px',
                                                    fontSize: '0.75rem',
                                                    fontWeight: 600
                                                }}
                                            >
                                                {f}
                                            </span>
                                        ))}
                                    </div>
                                </div>

                                {/* Arrow */}
                                <div style={{
                                    width: '36px',
                                    height: '36px',
                                    borderRadius: '12px',
                                    background: 'linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%)',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    flexShrink: 0,
                                    marginTop: '14px'
                                }}>
                                    {isLocked ? <Lock size={18} color="#94a3b8" /> : <ArrowRight size={18} color="#64748b" />}
                                </div>
                            </div>
                        </div>
                    )
                })}
            </div>

            <div style={{ height: '100px' }}></div>

            {/* 인바디 분석 결과 팝업 */}
            {showInbodyPopup && latestInbodyData && (
                <div
                    style={{
                        position: 'fixed',
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        background: 'rgba(0, 0, 0, 0.5)',
                        backdropFilter: 'blur(4px)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        zIndex: 1000,
                        padding: '20px',
                        animation: 'fadeIn 0.2s ease-out'
                    }}
                    onClick={() => setShowInbodyPopup(false)}
                >
                    <div
                        style={{
                            background: 'white',
                            borderRadius: '24px',
                            padding: '32px',
                            maxWidth: '500px',
                            width: '100%',
                            maxHeight: '80vh',
                            overflow: 'auto',
                            position: 'relative',
                            boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
                            animation: 'slideUp 0.3s ease-out'
                        }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        {/* 닫기 버튼 */}
                        <button
                            onClick={() => setShowInbodyPopup(false)}
                            style={{
                                position: 'absolute',
                                top: '16px',
                                right: '16px',
                                background: '#1e293b', // 완전 불투명한 진한 색상 (가장 잘 보임)
                                border: '2px solid white', // 흰색 테두리 추가로 대비 극대화
                                borderRadius: '50%',
                                width: '36px',
                                height: '36px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                cursor: 'pointer',
                                transition: 'all 0.2s',
                                zIndex: 9999, // 최상위 보장
                                boxShadow: '0 4px 12px rgba(0,0,0,0.3)' // 그림자 강조
                            }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.transform = 'scale(1.1)';
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.transform = 'scale(1)';
                            }}
                        >
                            <X size={20} color="white" strokeWidth={3} />
                        </button>

                        {/* 헤더 */}
                        <div style={{ marginBottom: '24px', paddingRight: '40px' }}>
                            <h2 style={{
                                fontSize: '1.5rem',
                                fontWeight: 800,
                                color: '#1e293b',
                                marginBottom: '8px',
                                letterSpacing: '-0.03em'
                            }}>
                                현재 인바디 분석 결과
                            </h2>
                            <p style={{ color: '#64748b', fontSize: '0.9rem' }}>
                                {new Date(latestInbodyData.created_at).toLocaleDateString('ko-KR', {
                                    year: 'numeric',
                                    month: 'long',
                                    day: 'numeric'
                                })} 기록
                            </p>
                        </div>

                        {/* 주요 지표 */}
                        <div style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(2, 1fr)',
                            gap: '12px',
                            marginBottom: '24px'
                        }}>
                            {latestInbodyData.measurements?.["체중관리"]?.["체중"] && (
                                <div style={{
                                    background: 'linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%)', // 파스텔 블루
                                    padding: '16px',
                                    borderRadius: '16px',
                                    color: '#1e40af',
                                    border: '1px solid rgba(255,255,255,0.6)'
                                }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                                        <Activity size={18} color="#2563eb" />
                                        <span style={{ fontSize: '0.8rem', opacity: 0.8, fontWeight: 600 }}>체중</span>
                                    </div>
                                    <div style={{ fontSize: '1.6rem', fontWeight: 700, color: '#172554' }}>
                                        {latestInbodyData.measurements["체중관리"]["체중"]}
                                        <span style={{ fontSize: '1rem', marginLeft: '4px', fontWeight: 600, opacity: 0.7 }}>kg</span>
                                    </div>
                                </div>
                            )}

                            {latestInbodyData.measurements?.["체중관리"]?.["골격근량"] && (
                                <div style={{
                                    background: 'linear-gradient(135deg, #fdf2f8 0%, #fce7f3 100%)', // 파스텔 핑크
                                    padding: '16px',
                                    borderRadius: '16px',
                                    color: '#9d174d',
                                    border: '1px solid rgba(255,255,255,0.6)'
                                }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                                        <Zap size={18} color="#db2777" />
                                        <span style={{ fontSize: '0.8rem', opacity: 0.8, fontWeight: 600 }}>골격근량</span>
                                    </div>
                                    <div style={{ fontSize: '1.6rem', fontWeight: 700, color: '#831843' }}>
                                        {latestInbodyData.measurements["체중관리"]["골격근량"]}
                                        <span style={{ fontSize: '1rem', marginLeft: '4px', fontWeight: 600, opacity: 0.7 }}>kg</span>
                                    </div>
                                </div>
                            )}

                            {latestInbodyData.measurements?.["비만분석"]?.["체지방률"] && (
                                <div style={{
                                    background: 'linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%)', // 파스텔 옐로우
                                    padding: '16px',
                                    borderRadius: '16px',
                                    color: '#92400e',
                                    border: '1px solid rgba(255,255,255,0.6)'
                                }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                                        <TrendingUp size={18} color="#d97706" />
                                        <span style={{ fontSize: '0.8rem', opacity: 0.8, fontWeight: 600 }}>체지방률</span>
                                    </div>
                                    <div style={{ fontSize: '1.6rem', fontWeight: 700, color: '#78350f' }}>
                                        {latestInbodyData.measurements["비만분석"]["체지방률"]}
                                        <span style={{ fontSize: '1rem', marginLeft: '4px', fontWeight: 600, opacity: 0.7 }}>%</span>
                                    </div>
                                </div>
                            )}

                            {latestInbodyData.measurements?.["비만분석"]?.["BMI"] && (
                                <div style={{
                                    background: 'linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%)', // 파스텔 스카이
                                    padding: '16px',
                                    borderRadius: '16px',
                                    color: '#075985',
                                    border: '1px solid rgba(255,255,255,0.6)'
                                }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                                        <Activity size={18} color="#0284c7" />
                                        <span style={{ fontSize: '0.8rem', opacity: 0.8, fontWeight: 600 }}>BMI</span>
                                    </div>
                                    <div style={{ fontSize: '1.6rem', fontWeight: 700, color: '#0c4a6e' }}>
                                        {latestInbodyData.measurements["비만분석"]["BMI"]}
                                        <span style={{ fontSize: '0.8rem', marginLeft: '4px', fontWeight: 600, opacity: 0.7 }}>kg/m²</span>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* 체형 타입 */}
                        {latestInbodyData.body_type1 && (
                            <div style={{
                                background: '#f8fafc',
                                padding: '16px',
                                borderRadius: '16px',
                                marginBottom: '24px',
                                textAlign: 'center'
                            }}>
                                <span style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: '4px', display: 'block' }}>
                                    현재 체형
                                </span>
                                <span style={{
                                    fontSize: '1.2rem',
                                    fontWeight: 700,
                                    color: '#667eea'
                                }}>
                                    {latestInbodyData.body_type1}
                                </span>
                            </div>
                        )}

                        {/* AI 정밀분석 버튼 */}
                        <button
                            onClick={handleStartAnalysis}
                            disabled={isAnalyzing}
                            style={{
                                width: '100%',
                                padding: '16px',
                                position: 'relative',
                                overflow: 'hidden',
                                background: isAnalyzing
                                    ? 'rgba(100, 116, 139, 0.2)'
                                    : '#1e293b', // 단색 (검정/남색 계열)
                                color: 'white',
                                border: 'none',
                                borderRadius: '16px',
                                fontSize: '1rem',
                                fontWeight: 700,
                                cursor: isAnalyzing ? 'default' : 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '8px',
                                transition: 'all 0.3s',
                                boxShadow: isAnalyzing
                                    ? 'none'
                                    : '0 4px 12px rgba(15, 23, 42, 0.2)'
                            }}
                            onMouseEnter={(e) => {
                                if (!isAnalyzing) {
                                    e.currentTarget.style.transform = 'translateY(-2px)';
                                    e.currentTarget.style.boxShadow = '0 8px 24px rgba(102, 126, 234, 0.4)';
                                }
                            }}
                            onMouseLeave={(e) => {
                                if (!isAnalyzing) {
                                    e.currentTarget.style.transform = 'translateY(0)';
                                    e.currentTarget.style.boxShadow = '0 4px 16px rgba(102, 126, 234, 0.3)';
                                }
                            }}
                        >
                            {/* 진행바 */}
                            {isAnalyzing && (
                                <div style={{
                                    position: 'absolute',
                                    top: 0,
                                    left: 0,
                                    height: '100%',
                                    width: `${analyzeProgress}%`,
                                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)',
                                    transition: 'width 0.15s ease-out',
                                    borderRadius: '16px'
                                }} />
                            )}
                            <span style={{ position: 'relative', zIndex: 1, display: 'flex', alignItems: 'center', gap: '8px' }}>
                                {isAnalyzing ? (
                                    <>
                                        <Loader2 size={20} style={{ animation: 'spin 1s linear infinite' }} />
                                        {analyzeProgress < 100 ? `${analyzeMessage} ${analyzeProgress}%` : '완료!'}
                                    </>
                                ) : (
                                    <>
                                        <Sparkles size={20} />
                                        AI 정밀분석
                                    </>
                                )}
                            </span>
                        </button>
                    </div>
                </div>
            )}

            {/* 안내 팝업 (OCR 안내 OR 분석가 이용 안내) */}
            {showNoDataPopup && (
                <div
                    style={{
                        position: 'fixed',
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        background: 'rgba(0, 0, 0, 0.5)',
                        backdropFilter: 'blur(4px)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        zIndex: 1000,
                        padding: '20px',
                        animation: 'fadeIn 0.2s ease-out'
                    }}
                    onClick={() => setShowNoDataPopup(false)}
                >
                    <div
                        style={{
                            background: 'white',
                            borderRadius: '24px',
                            padding: '32px',
                            maxWidth: '400px',
                            width: '100%',
                            position: 'relative',
                            boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
                            animation: 'slideUp 0.3s ease-out'
                        }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <button
                            onClick={() => setShowNoDataPopup(false)}
                            style={{
                                position: 'absolute',
                                top: '16px',
                                right: '16px',
                                background: 'rgba(0, 0, 0, 0.6)',
                                border: 'none',
                                borderRadius: '50%',
                                width: '32px',
                                height: '32px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                cursor: 'pointer',
                                transition: 'all 0.2s',
                                zIndex: 100,
                                backdropFilter: 'blur(4px)'
                            }}
                        >
                            <X size={18} color="white" />
                        </button>

                        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
                            <div style={{
                                width: '80px',
                                height: '80px',
                                borderRadius: '24px',
                                background: popupType === 'ocr'
                                    ? 'linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)'
                                    : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                margin: '0 auto 16px',
                                boxShadow: popupType === 'ocr'
                                    ? '0 8px 24px rgba(251, 191, 36, 0.3)'
                                    : '0 8px 24px rgba(102, 126, 234, 0.3)'
                            }}>
                                {popupType === 'ocr' ? (
                                    <AlertCircle size={40} color="white" />
                                ) : (
                                    <Sparkles size={40} color="white" />
                                )}
                            </div>
                            <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#1e293b', marginBottom: '8px', wordKeepAll: 'break-word' }}>
                                {popupType === 'ocr' ? '인바디 검사가 필요해요' : '순서가 중요해요!'}
                            </h2>
                            <p style={{ color: '#64748b', fontSize: '0.9rem', lineHeight: 1.6, wordKeepAll: 'break-word' }}>
                                {popupType === 'ocr' ? (
                                    <>아직 인바디 검사 결과가 없습니다.<br />먼저 인바디 검사지를 등록해주세요.</>
                                ) : (
                                    <>정확한 운동 추천을 위해서는<br /><b>인바디 분석 전문가</b>와의 상담이 선행되어야 합니다.</>
                                )}
                            </p>
                        </div>

                        {popupType === 'ocr' ? (
                            <button
                                onClick={() => {
                                    setShowNoDataPopup(false);
                                    navigate('/inbody');
                                }}
                                style={{
                                    width: '100%',
                                    padding: '16px',
                                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '16px',
                                    fontSize: '1rem',
                                    fontWeight: 700,
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    gap: '10px',
                                    transition: 'all 0.3s',
                                    boxShadow: '0 4px 16px rgba(102, 126, 234, 0.3)'
                                }}
                            >
                                <FileText size={20} />
                                인바디 검사하러 가기
                            </button>
                        ) : (
                            <button
                                onClick={() => setShowNoDataPopup(false)}
                                style={{
                                    width: '100%',
                                    padding: '16px',
                                    background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '16px',
                                    fontSize: '1rem',
                                    fontWeight: 700,
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    gap: '10px',
                                    transition: 'all 0.3s',
                                    boxShadow: '0 4px 16px rgba(240, 147, 251, 0.3)'
                                }}
                            >
                                <Sparkles size={20} />
                                네, 알겠습니다
                            </button>
                        )}

                        {popupType === 'ocr' && (
                            <p style={{ marginTop: '16px', fontSize: '0.8rem', color: '#94a3b8', textAlign: 'center', lineHeight: 1.5 }}>
                                검사지를 촬영하면 OCR로 자동 분석됩니다.
                            </p>
                        )}
                    </div>
                </div>
            )}

            {/* 글로벌 로딩 오버레이 */}
            {isAnalyzing && (
                <div style={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: 'rgba(255, 255, 255, 0.9)',
                    backdropFilter: 'blur(8px)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    zIndex: 10000,
                    animation: 'fadeIn 0.3s ease-out'
                }}>
                    <div style={{ width: '100%', maxWidth: '400px', padding: '20px' }}>
                        <LoadingAnimation
                            message={analyzeMessage}
                            progress={analyzeProgress}
                        />
                    </div>
                </div>
            )}

            {/* 운동 플랜 설정 팝업 */}
            <ExercisePlanPopup
                isOpen={showExercisePopup}
                onClose={() => setShowExercisePopup(false)}
                onSubmit={handleExercisePlanSubmit}
                initialData={
                    USE_MOCK_DATA
                        ? MOCK_USER_SETTINGS
                        : JSON.parse(localStorage.getItem('exerciseSettings') || 'null')
                }
            />

            <style>{`
                @keyframes fadeIn {
                    from {
                        opacity: 0;
                    }
                    to {
                        opacity: 1;
                    }
                }

                @keyframes slideUp {
                    from {
                        transform: translateY(20px);
                        opacity: 0;
                    }
                    to {
                        transform: translateY(0);
                        opacity: 1;
                    }
                }

                @keyframes premiumFade {
                    from {
                        opacity: 0;
                        transform: translateY(10px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }
                @keyframes spin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }

                @keyframes pulse {
                    0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 1; }
                    50% { transform: translate(-50%, -50%) scale(1.1); opacity: 0.8; }
                }
            `}</style>
        </div>
    );
};

export default ChatbotSelector;
