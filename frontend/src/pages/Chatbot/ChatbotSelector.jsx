import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, ArrowRight } from 'lucide-react';
import '../../styles/LoginLight.css';

const ChatbotSelector = () => {
    const navigate = useNavigate();

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
                        onClick={() => navigate(`/chatbot/${bot.id}`)}
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
        </div>
    );
};

export default ChatbotSelector;
