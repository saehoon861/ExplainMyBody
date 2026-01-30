import React, { useState } from 'react';
import { User, Mail, Lock, ArrowRight, ArrowLeft, CheckCircle2 } from 'lucide-react';
import { useNavigate, Link } from 'react-router-dom';
import './Login.css'; // Signup도 Login.css의 스타일을 공유하도록 설계됨

const Signup = () => {
    const navigate = useNavigate();
    const [step, setStep] = useState(1);
    const [isLoading, setIsLoading] = useState(false);

    const [formData, setFormData] = useState({
        email: '',
        password: '',
        confirmPassword: '',
        name: ''
    });

    const handleNext = (e) => {
        e.preventDefault();
        setStep(prev => prev + 1);
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        setIsLoading(true);
        // 목업 회원가입 성공 처리
        setTimeout(() => {
            setIsLoading(false);
            navigate('/signup-success');
        }, 1500);
    };

    return (
        <div className="login-container">
            <div className="login-card signup-card fade-in">
                <div className="login-header">
                    <h1>Explain<span>MyBody</span></h1>
                    <p>새로운 시작, 당신만의 건강 파트너</p>
                </div>

                <div className="progress-indicator">
                    <div className={`progress-step ${step >= 1 ? 'active' : ''} ${step > 1 ? 'completed' : ''}`}>
                        <div className="step-number">{step > 1 ? <CheckCircle2 size={16} /> : '1'}</div>
                        <span className="step-label">정보 입력</span>
                    </div>
                    <div className={`progress-line ${step > 1 ? 'active' : ''}`}></div>
                    <div className={`progress-step ${step >= 2 ? 'active' : ''}`}>
                        <div className="step-number">2</div>
                        <span className="step-label">가입 완료</span>
                    </div>
                </div>

                <form onSubmit={step === 1 ? handleNext : handleSubmit}>
                    {step === 1 ? (
                        <div className="step-content">
                            <div className="form-group">
                                <label>이름</label>
                                <div className="input-wrapper">
                                    <User size={18} />
                                    <input type="text" placeholder="홍길동" required />
                                </div>
                            </div>
                            <div className="form-group">
                                <label>이메일</label>
                                <div className="input-wrapper">
                                    <Mail size={18} />
                                    <input type="email" placeholder="example@email.com" required />
                                </div>
                            </div>
                            <div className="form-group">
                                <label>비밀번호</label>
                                <div className="input-wrapper">
                                    <Lock size={18} />
                                    <input type="password" placeholder="••••••••" required />
                                </div>
                            </div>
                            <button type="submit" className="primary-button">
                                다음 단계 <ArrowRight size={18} />
                            </button>
                        </div>
                    ) : (
                        <div className="step-content">
                            <div style={{ textAlign: 'center', padding: '20px 0' }}>
                                <CheckCircle2 size={64} color="#818cf8" style={{ marginBottom: '20px' }} />
                                <h3 style={{ color: 'white', marginBottom: '10px' }}>거의 다 됐습니다!</h3>
                                <p style={{ color: '#94a3b8' }}>입력하신 정보로 계정을 생성할까요?</p>
                            </div>
                            <div className="button-group">
                                <button type="button" className="secondary-button" onClick={() => setStep(1)}>
                                    <ArrowLeft size={16} /> 이전
                                </button>
                                <button type="submit" className="primary-button" disabled={isLoading}>
                                    {isLoading ? '생성 중...' : '계정 만들기'}
                                </button>
                            </div>
                        </div>
                    )}
                </form>

                <div className="login-footer">
                    <p>이미 계정이 있으신가요? <Link to="/">로그인하기</Link></p>
                </div>
            </div>
        </div>
    );
};

export default Signup;
