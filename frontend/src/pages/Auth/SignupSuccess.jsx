import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle2, PartyPopper, ArrowRight } from 'lucide-react';
import '../../styles/LoginLight.css';

const SignupSuccess = () => {
    const navigate = useNavigate();
    const [countdown, setCountdown] = useState(5);

    useEffect(() => {
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

        return () => clearInterval(timer);
    }, [navigate]);

    return (
        <div className="login-container fade-in">
            <div className="login-card" style={{ textAlign: 'center', padding: '60px 40px' }}>
                <div style={{
                    display: 'inline-flex',
                    padding: '24px',
                    background: '#ecfdf5',
                    color: '#10b981',
                    borderRadius: '50%',
                    marginBottom: '32px',
                    animation: 'scaleUp 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards'
                }}>
                    <CheckCircle2 size={64} />
                </div>

                <h1 style={{ fontSize: '2rem', fontWeight: 800, marginBottom: '12px' }}>회원가입 완료!</h1>
                <p style={{ color: '#64748b', fontSize: '1.1rem', marginBottom: '40px', lineHeight: 1.6 }}>
                    환영합니다! 이제 나만을 위한<br />
                    스마트한 피트니스 관리를 시작해보세요.
                </p>

                <div className="countdown-box" style={{
                    background: '#f8fafc',
                    padding: '20px',
                    borderRadius: '20px',
                    marginBottom: '32px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '12px',
                    color: '#64748b',
                    fontSize: '0.95rem'
                }}>
                    <PartyPopper size={20} color="#4f46e5" />
                    <span>{countdown}초 후에 로그인 페이지로 이동합니다.</span>
                </div>

                <button
                    className="primary-button"
                    onClick={() => navigate('/login')}
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '12px'
                    }}
                >
                    지금 바로 로그인하기
                    <ArrowRight size={20} />
                </button>
            </div>

            <style>{`
                @keyframes scaleUp {
                    from { transform: scale(0); opacity: 0; }
                    to { transform: scale(1); opacity: 1; }
                }
            `}</style>
        </div>
    );
};

export default SignupSuccess;
