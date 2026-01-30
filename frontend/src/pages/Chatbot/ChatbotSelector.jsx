import React from 'react';
import { useNavigate } from 'react-router-dom';
import { MessageCircle, Sparkles, ChevronRight } from 'lucide-react';
import '../../styles/LoginLight.css';

const ChatbotSelector = () => {
    const navigate = useNavigate();

    const bots = [
        {
            id: 'inbody-analyst',
            name: '인바디 분석 전문가',
            desc: '식단, 운동, 생활습관 등 전반적인 건강 상담을 도와드립니다.',
            icon: '🧑‍⚕️',
            color: '#4f46e5',
            features: ['맞춤 상담', '식단 대안', '동기 부여']
        },
        {
            id: 'workout-planner',
            name: '운동 플래너 전문가',
            desc: '개인 맞춤형 운동 루틴과 자세 교정을 도와드립니다.',
            icon: '🏋️',
            color: '#f5576c',
            features: ['운동 루틴', '자세 교정', '체력 증진']
        }
    ];

    return (
        <div className="main-content fade-in">
            <header className="dashboard-header" style={{ textAlign: 'center', marginBottom: '40px' }}>
                <div style={{ display: 'inline-flex', padding: '12px', background: '#e0e7ff', borderRadius: '20px', color: '#4f46e5', marginBottom: '16px' }}>
                    <Sparkles size={32} />
                </div>
                <h1>AI 상담소</h1>
                <p>전문 분야별 AI 코칭을 받아보세요.</p>
            </header>

            <div className="chatbot-list" style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '16px',
                padding: '16px 0',
                maxWidth: '600px',
                margin: '0 auto'
            }}>
                {bots.map((bot, index) => {
                    const Icon = bot.icon;
                    return (
                        <div
                            key={bot.id}
                            className={`bot-card-compact delay-${index + 1}`}
                            style={{
                                background: 'white',
                                borderRadius: '24px',
                                padding: '24px',
                                cursor: 'pointer',
                                transition: 'all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)',
                                overflow: 'hidden',
                                position: 'relative',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '20px',
                                boxShadow: '0 4px 20px rgba(0,0,0,0.03)',
                                opacity: 0,
                                transformOrigin: 'center',
                                animation: 'premiumFade 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards',
                                animationDelay: `${index * 0.1}s`,
                                border: '1px solid rgba(0,0,0,0.04)'
                            }}
                            onClick={() => navigate(`/chatbot/${bot.id}`)}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.transform = 'scale(1.02) translateY(-2px)';
                                e.currentTarget.style.boxShadow = `0 15px 35px -10px ${bot.color}25`;
                                e.currentTarget.style.borderColor = `${bot.color}30`;
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.transform = 'scale(1) translateY(0)';
                                e.currentTarget.style.boxShadow = '0 4px 20px rgba(0,0,0,0.03)';
                                e.currentTarget.style.borderColor = 'rgba(0,0,0,0.04)';
                            }}
                        >
                            {/* Breathing Background Blob */}
                            <div
                                className="card-bg animate-blob"
                                style={{
                                    position: 'absolute',
                                    top: '-20px',
                                    right: '-20px',
                                    width: '150px',
                                    height: '150px',
                                    borderRadius: '50%',
                                    background: bot.color,
                                    zIndex: 0,
                                    filter: 'blur(40px)',
                                    animationDelay: `${index * 2}s` // Stagger breathing
                                }}
                            ></div>

                            <div
                                className="animate-float"
                                style={{
                                    position: 'relative',
                                    zIndex: 1,
                                    minWidth: '56px',
                                    height: '56px',
                                    borderRadius: '18px',
                                    background: `${bot.color}10`,
                                    color: bot.color,
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    fontSize: '28px', // Emoji size
                                    animationDelay: `${index * 1.5}s` // Stagger float
                                }}>
                                {typeof bot.icon === 'string' ? bot.icon : <bot.icon size={28} strokeWidth={2.5} />}
                            </div>

                            <div style={{ flex: 1, position: 'relative', zIndex: 1 }}>
                                <h2 style={{
                                    fontSize: '1.25rem',
                                    fontWeight: 700,
                                    color: '#1e293b',
                                    marginBottom: '6px',
                                    letterSpacing: '-0.02em'
                                }}>
                                    {bot.name}
                                </h2>
                                <p style={{
                                    color: '#64748b',
                                    fontSize: '0.9rem',
                                    lineHeight: 1.5,
                                    marginBottom: '10px'
                                }}>
                                    {bot.desc}
                                </p>
                                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                                    {bot.features.map(f => (
                                        <span
                                            key={f}
                                            style={{
                                                padding: '4px 10px',
                                                background: '#f1f5f9',
                                                color: '#475569',
                                                borderRadius: '8px',
                                                fontSize: '0.75rem',
                                                fontWeight: 600
                                            }}
                                        >
                                            {f}
                                        </span>
                                    ))}
                                </div>
                            </div>

                            <div style={{
                                color: '#cbd5e1',
                                paddingLeft: '8px',
                                transition: 'transform 0.3s ease'
                            }} className="action-arrow">
                                <ChevronRight size={20} strokeWidth={3} />
                            </div>
                        </div>
                    );
                })}
            </div>

            <div style={{ height: '80px' }}></div>
        </div>
    );
};

export default ChatbotSelector;
