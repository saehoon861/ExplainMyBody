import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Mail, ArrowLeft, CheckCircle } from 'lucide-react';
import '../../styles/LoginLight.css';

const ForgotPassword = () => {
    const [email, setEmail] = useState('');
    const [isSubmitted, setIsSubmitted] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = (e) => {
        e.preventDefault();
        setIsLoading(true);

        // 시뮬레이션: 1.5초 후 성공 처리
        setTimeout(() => {
            setIsLoading(false);
            setIsSubmitted(true);
        }, 1500);
    };

    return (
        <div className="login-container">
            <div className="login-card" style={{ maxWidth: '450px' }}>
                {/* 헤더 */}
                <div className="login-header fade-in delay-1">
                    {!isSubmitted ? (
                        <>
                            <h1 style={{ fontSize: '1.8rem' }}>비밀번호 찾기</h1>
                            <p>가입한 이메일을 입력하시면<br />비밀번호 재설정 링크를 보내드립니다.</p>
                        </>
                    ) : (
                        <>
                            <div style={{
                                width: '60px',
                                height: '60px',
                                background: '#dcfce7',
                                borderRadius: '50%',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                margin: '0 auto 20px',
                                color: '#16a34a'
                            }}>
                                <CheckCircle size={32} />
                            </div>
                            <h1 style={{ fontSize: '1.8rem' }}>이메일 발송 완료</h1>
                            <p>입력하신 이메일로<br />재설정 링크가 발송되었습니다.</p>
                        </>
                    )}
                </div>

                {!isSubmitted ? (
                    <form onSubmit={handleSubmit}>
                        <div className="form-group fade-in delay-2">
                            <label>이메일</label>
                            <div className="input-wrapper">
                                <Mail size={20} />
                                <input
                                    type="email"
                                    placeholder="example@email.com"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                    disabled={isLoading}
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            className="primary-button fade-in delay-3"
                            disabled={isLoading}
                            style={{ marginTop: '20px' }}
                        >
                            {isLoading ? '발송 중...' : '재설정 링크 보내기'}
                        </button>
                    </form>
                ) : (
                    <div className="fade-in delay-2">
                        <div style={{
                            background: '#f8fafc',
                            padding: '16px',
                            borderRadius: '12px',
                            textAlign: 'center',
                            marginBottom: '24px',
                            border: '1px solid #e2e8f0',
                            color: '#64748b',
                            fontSize: '0.9rem'
                        }}>
                            <strong>{email}</strong><br />
                            메일함을 확인해주세요.
                        </div>
                        <button
                            onClick={() => navigate('/login')}
                            className="primary-button"
                        >
                            로그인 페이지로 돌아가기
                        </button>
                    </div>
                )}

                <div className="login-footer fade-in delay-4" style={{ marginTop: '24px' }}>
                    <Link to="/login" style={{ display: 'flex', alignItems: 'center', gap: '6px', justifyContent: 'center' }}>
                        <ArrowLeft size={16} />
                        로그인으로 돌아가기
                    </Link>
                </div>
            </div>
        </div>
    );
};

export default ForgotPassword;
