import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, ArrowRight, X, TrendingUp, Activity, Zap } from 'lucide-react';
import '../../styles/LoginLight.css';
import { getUserHealthRecords } from '../../services/inbodyService';

const ChatbotSelector = () => {
    const navigate = useNavigate();
    const [showInbodyPopup, setShowInbodyPopup] = useState(false);
    const [latestInbodyData, setLatestInbodyData] = useState(null);
    const [isLoading, setIsLoading] = useState(false);

    // 인바디 데이터 로드
    useEffect(() => {
        const loadInbodyData = async () => {
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
        if (botId === 'inbody-analyst' && latestInbodyData) {
            setShowInbodyPopup(true);
        } else {
            navigate(`/chatbot/${botId}`);
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
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    borderRadius: '24px',
                    marginBottom: '20px',
                    boxShadow: '0 8px 32px rgba(102, 126, 234, 0.3)'
                }}>
                    <Sparkles size={36} color="white" />
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
                {bots.map((bot, index) => (
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
                            opacity: 0
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
                        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '18px' }}>
                            {/* Profile Icon */}
                            <div style={{
                                width: '64px',
                                height: '64px',
                                borderRadius: '20px',
                                background: bot.gradient,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontSize: '32px',
                                boxShadow: '0 8px 24px rgba(0,0,0,0.15)',
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
                                <ArrowRight size={18} color="#64748b" />
                            </div>
                        </div>
                    </div>
                ))}
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
                                background: '#f1f5f9',
                                border: 'none',
                                borderRadius: '12px',
                                width: '36px',
                                height: '36px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                cursor: 'pointer',
                                transition: 'all 0.2s'
                            }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.background = '#e2e8f0';
                                e.currentTarget.style.transform = 'rotate(90deg)';
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.background = '#f1f5f9';
                                e.currentTarget.style.transform = 'rotate(0deg)';
                            }}
                        >
                            <X size={20} color="#64748b" />
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
                                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                    padding: '16px',
                                    borderRadius: '16px',
                                    color: 'white'
                                }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                                        <Activity size={18} />
                                        <span style={{ fontSize: '0.8rem', opacity: 0.9 }}>체중</span>
                                    </div>
                                    <div style={{ fontSize: '1.8rem', fontWeight: 700 }}>
                                        {latestInbodyData.measurements["체중관리"]["체중"]}
                                        <span style={{ fontSize: '1rem', marginLeft: '4px' }}>kg</span>
                                    </div>
                                </div>
                            )}

                            {latestInbodyData.measurements?.["체중관리"]?.["골격근량"] && (
                                <div style={{
                                    background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                                    padding: '16px',
                                    borderRadius: '16px',
                                    color: 'white'
                                }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                                        <Zap size={18} />
                                        <span style={{ fontSize: '0.8rem', opacity: 0.9 }}>골격근량</span>
                                    </div>
                                    <div style={{ fontSize: '1.8rem', fontWeight: 700 }}>
                                        {latestInbodyData.measurements["체중관리"]["골격근량"]}
                                        <span style={{ fontSize: '1rem', marginLeft: '4px' }}>kg</span>
                                    </div>
                                </div>
                            )}

                            {latestInbodyData.measurements?.["비만분석"]?.["체지방률"] && (
                                <div style={{
                                    background: 'linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%)',
                                    padding: '16px',
                                    borderRadius: '16px',
                                    color: '#2d3436'
                                }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                                        <TrendingUp size={18} />
                                        <span style={{ fontSize: '0.8rem', opacity: 0.8 }}>체지방률</span>
                                    </div>
                                    <div style={{ fontSize: '1.8rem', fontWeight: 700 }}>
                                        {latestInbodyData.measurements["비만분석"]["체지방률"]}
                                        <span style={{ fontSize: '1rem', marginLeft: '4px' }}>%</span>
                                    </div>
                                </div>
                            )}

                            {latestInbodyData.measurements?.["비만분석"]?.["BMI"] && (
                                <div style={{
                                    background: 'linear-gradient(135deg, #74b9ff 0%, #0984e3 100%)',
                                    padding: '16px',
                                    borderRadius: '16px',
                                    color: 'white'
                                }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                                        <Activity size={18} />
                                        <span style={{ fontSize: '0.8rem', opacity: 0.9 }}>BMI</span>
                                    </div>
                                    <div style={{ fontSize: '1.8rem', fontWeight: 700 }}>
                                        {latestInbodyData.measurements["비만분석"]["BMI"]}
                                        <span style={{ fontSize: '0.8rem', marginLeft: '4px' }}>kg/m²</span>
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

                        {/* 인바디 분석 피드백 버튼 */}
                        <button
                            onClick={() => {
                                setShowInbodyPopup(false);
                                navigate('/chatbot/inbody-analyst');
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
                                gap: '8px',
                                transition: 'all 0.3s',
                                boxShadow: '0 4px 16px rgba(102, 126, 234, 0.3)'
                            }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.transform = 'translateY(-2px)';
                                e.currentTarget.style.boxShadow = '0 8px 24px rgba(102, 126, 234, 0.4)';
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.transform = 'translateY(0)';
                                e.currentTarget.style.boxShadow = '0 4px 16px rgba(102, 126, 234, 0.3)';
                            }}
                        >
                            <Sparkles size={20} />
                            인바디 분석 피드백 받기
                        </button>
                    </div>
                </div>
            )}

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
            `}</style>
        </div>
    );
};

export default ChatbotSelector;
