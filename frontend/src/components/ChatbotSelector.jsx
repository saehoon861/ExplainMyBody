import React from 'react';
import { useNavigate } from 'react-router-dom';
import { MessageCircle, Brain, Target, Sparkles, ChevronRight } from 'lucide-react';
import './LoginLight.css';

const ChatbotSelector = () => {
    const navigate = useNavigate();

    const bots = [
        {
            id: 'general',
            name: 'AI 피트니스 코치',
            desc: '식단, 운동, 생활습관 등 전반적인 건강 상담을 도와드립니다.',
            icon: Brain,
            color: '#4f46e5',
            features: ['맞춤 상담', '식단 대안', '동기 부여']
        },
        {
            id: 'rehab',
            name: '재활 전문 상담사',
            desc: '부상 부위 관리 및 체형 교정을 위한 전문적인 조언을 제공합니다.',
            icon: Target,
            color: '#f43f5e',
            features: ['통증 케어', '자세 교정', '스트레칭']
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

            <div className="chatbot-cards" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                {bots.map((bot) => {
                    const Icon = bot.icon;
                    return (
                        <div
                            key={bot.id}
                            className="dashboard-card"
                            style={{
                                padding: '32px',
                                cursor: 'pointer',
                                transition: 'all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
                                overflow: 'hidden',
                                position: 'relative'
                            }}
                            onClick={() => navigate(`/chatbot/${bot.id}`)}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.transform = 'translateY(-6px)';
                                e.currentTarget.style.borderColor = bot.color;
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.transform = 'translateY(0)';
                                e.currentTarget.style.borderColor = 'rgba(0,0,0,0.05)';
                            }}
                        >
                            <div style={{
                                position: 'absolute',
                                top: '-20px',
                                right: '-20px',
                                background: bot.color,
                                width: '100px',
                                height: '100px',
                                borderRadius: '50%',
                                opacity: 0.05
                            }}></div>

                            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '20px' }}>
                                <div style={{
                                    padding: '16px',
                                    background: `${bot.color}15`,
                                    color: bot.color,
                                    borderRadius: '16px'
                                }}>
                                    <Icon size={32} />
                                </div>
                                <div style={{ flex: 1 }}>
                                    <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#1e293b', marginBottom: '8px' }}>{bot.name}</h2>
                                    <p style={{ color: '#64748b', fontSize: '0.95rem', lineHeight: 1.6, marginBottom: '20px' }}>{bot.desc}</p>

                                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                                        {bot.features.map(f => (
                                            <span
                                                key={f}
                                                style={{
                                                    padding: '4px 12px',
                                                    background: '#f1f5f9',
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
                                <div style={{ height: '100%', display: 'flex', alignItems: 'center' }}>
                                    <ChevronRight size={24} color="#cbd5e1" />
                                </div>
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
