import React, { useState } from 'react';
import { Mail, Lock, LogIn, ArrowRight } from 'lucide-react';
import { useNavigate, Link } from 'react-router-dom';
import './Login.css';

const Login = () => {
    const navigate = useNavigate();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);

        // 목업 로그인 처리 (1초 대기 후 대시보드로 이동)
        setTimeout(() => {
            console.log('Login attempt:', { email, password });
            setIsLoading(false);
            navigate('/dashboard');
        }, 1200);
    };

    return (
        <div className="login-container">
            <div className="login-card fade-in">
                <div className="login-header">
                    <h1>Explain<span>MyBody</span></h1>
                    <p>당신의 체성분을 이해하고 변화를 시작하세요</p>
                </div>

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label>이메일</label>
                        <div className="input-wrapper">
                            <Mail size={18} />
                            <input
                                type="email"
                                placeholder="example@email.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                            />
                        </div>
                    </div>

                    <div className="form-group">
                        <label>비밀번호</label>
                        <div className="input-wrapper">
                            <Lock size={18} />
                            <input
                                type="password"
                                placeholder="••••••••"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                            />
                        </div>
                    </div>

                    <div className="form-options">
                        <a href="#reset">비밀번호를 잊으셨나요?</a>
                    </div>

                    <button type="submit" className="login-button" disabled={isLoading}>
                        {isLoading ? (
                            <span className="spinner-border animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full" />
                        ) : (
                            <>
                                로그인 <LogIn size={18} />
                            </>
                        )}
                    </button>
                </form>

                <div className="login-footer">
                    <p>계정이 없으신가요? <Link to="/signup">지금 가입하기</Link></p>
                </div>
            </div>

            {/* 배경 장식 요소 */}
            <div className="decoration-blob top-right"></div>
            <div className="decoration-blob bottom-left"></div>
        </div>
    );
};

export default Login;
