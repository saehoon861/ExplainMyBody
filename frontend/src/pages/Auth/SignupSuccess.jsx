import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, ArrowRight, PartyPopper } from 'lucide-react';
import confetti from 'canvas-confetti';
import '../../styles/LoginLight.css';

const SignupSuccess = () => {
    const navigate = useNavigate();
    const [countdown, setCountdown] = useState(5);

    useEffect(() => {
        // 폭죽 효과 실행
        const duration = 3000;
        const animationEnd = Date.now() + duration;
        const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 0 };

        const randomInRange = (min, max) => Math.random() * (max - min) + min;

        const interval = setInterval(() => {
            const timeLeft = animationEnd - Date.now();

            if (timeLeft <= 0) {
                return clearInterval(interval);
            }

            const particleCount = 50 * (timeLeft / duration);

            // 양쪽에서 폭죽 발사
            confetti({
                ...defaults,
                particleCount,
                origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 }
            });
            confetti({
                ...defaults,
                particleCount,
                origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 }
            });
        }, 250);

        // 카운트다운 및 리다이렉트
        const timer = setInterval(() => {
            setCountdown(prev => {
                if (prev <= 1) {
                    clearInterval(timer);
                    navigate('/login');
                    return 0;
                }
                return prev - 1;
            });
        }, 1000);

        return () => {
            clearInterval(interval);
            clearInterval(timer);
        };
    }, [navigate]);

    return (
        <div className="login-container">
            <div className="login-card fade-in-up" style={{ textAlign: 'center', padding: '60px 40px', maxWidth: '480px' }}>

                <div className="success-icon-wrapper">
                    <div className="success-icon-circle">
                        <Check size={48} strokeWidth={3} />
                    </div>
                    <div className="success-icon-pulse"></div>
                </div>

                <h1 style={{ fontSize: '2rem', fontWeight: 800, marginBottom: '16px', color: '#1e293b' }}>
                    회원가입 완료!
                </h1>

                <p style={{ color: '#64748b', fontSize: '1.1rem', marginBottom: '40px', lineHeight: 1.6 }}>
                    환영합니다! 이제 나만을 위한<br />
                    스마트한 피트니스 관리를 시작해보세요.
                </p>

                <div className="countdown-box" style={{
                    background: '#f1f5f9',
                    padding: '20px',
                    borderRadius: '16px',
                    marginBottom: '32px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '12px',
                    color: '#475569',
                    fontSize: '0.95rem',
                    fontWeight: 500
                }}>
                    <PartyPopper size={20} className="bounce-icon" color="#6366f1" />
                    <span>{countdown}초 후에 로그인 페이지로 이동합니다.</span>
                </div>

                <button
                    className="primary-button"
                    onClick={() => navigate('/login')}
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '8px',
                        height: '56px',
                        fontSize: '1.1rem'
                    }}
                >
                    지금 바로 로그인하기
                    <ArrowRight size={20} />
                </button>
            </div>

            <style>{`
                .fade-in-up {
                    animation: fadeInUp 0.6s ease-out forwards;
                }
                
                @keyframes fadeInUp {
                    from { transform: translateY(20px); opacity: 0; }
                    to { transform: translateY(0); opacity: 1; }
                }

                .success-icon-wrapper {
                    position: relative;
                    width: 100px;
                    height: 100px;
                    margin: 0 auto 32px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }

                .success-icon-circle {
                    width: 80px;
                    height: 80px;
                    background: #10b981;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    z-index: 2;
                    box-shadow: 0 10px 25px -5px rgba(16, 185, 129, 0.4);
                    animation: popIn 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
                }

                .success-icon-pulse {
                    position: absolute;
                    width: 100%;
                    height: 100%;
                    border-radius: 50%;
                    background: rgba(16, 185, 129, 0.2);
                    z-index: 1;
                    animation: pulseRing 2s infinite;
                }

                @keyframes popIn {
                    0% { transform: scale(0) rotate(-45deg); opacity: 0; }
                    70% { transform: scale(1.1) rotate(0deg); opacity: 1; }
                    100% { transform: scale(1) rotate(0deg); opacity: 1; }
                }

                @keyframes pulseRing {
                    0% { transform: scale(0.8); opacity: 0.8; }
                    100% { transform: scale(1.5); opacity: 0; }
                }

                .bounce-icon {
                    animation: bounce 2s infinite;
                }

                @keyframes bounce {
                    0%, 20%, 50%, 80%, 100% {transform: translateY(0);} 
                    40% {transform: translateY(-6px);} 
                    60% {transform: translateY(-3px);} 
                }
            `}</style>
        </div>
    );
};

export default SignupSuccess;
