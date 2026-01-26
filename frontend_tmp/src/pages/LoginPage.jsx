import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { authService } from '../services/authService';
import './LoginPage.css';

const LoginPage = () => {
    const navigate = useNavigate();
    const { login } = useAuth();
    const [isLogin, setIsLogin] = useState(true);
    const [formData, setFormData] = useState({
        username: '',
        email: '',
        password: '',
    });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value,
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            if (isLogin) {
                // 로그인
                const userData = await authService.login({
                    email: formData.email,
                    password: formData.password,
                });
                login(userData);
                navigate('/main');
            } else {
                // 회원가입
                const userData = await authService.register({
                    username: formData.username,
                    email: formData.email,
                    password: formData.password,
                });
                login(userData);
                navigate('/main');
            }
        } catch (err) {
            setError(err.response?.data?.detail || '오류가 발생했습니다.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-page">
            <div className="login-container">
                <div className="login-header">
                    <h1>ExplainMyBody</h1>
                    <p>인바디 데이터 분석 및 건강 관리</p>
                </div>

                <div className="tab-container">
                    <button
                        className={`tab ${isLogin ? 'active' : ''}`}
                        onClick={() => setIsLogin(true)}
                    >
                        로그인
                    </button>
                    <button
                        className={`tab ${!isLogin ? 'active' : ''}`}
                        onClick={() => setIsLogin(false)}
                    >
                        회원가입
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="login-form">
                    {!isLogin && (
                        <div className="form-group">
                            <label>사용자 이름</label>
                            <input
                                type="text"
                                name="username"
                                value={formData.username}
                                onChange={handleChange}
                                required
                                placeholder="홍길동"
                            />
                        </div>
                    )}

                    <div className="form-group">
                        <label>이메일</label>
                        <input
                            type="email"
                            name="email"
                            value={formData.email}
                            onChange={handleChange}
                            required
                            placeholder="email@example.com"
                        />
                    </div>

                    <div className="form-group">
                        <label>비밀번호</label>
                        <input
                            type="password"
                            name="password"
                            value={formData.password}
                            onChange={handleChange}
                            required
                            placeholder="비밀번호 입력"
                        />
                    </div>

                    {error && <div className="error-message">{error}</div>}

                    <button type="submit" className="submit-btn" disabled={loading}>
                        {loading ? '처리 중...' : isLogin ? '로그인' : '회원가입'}
                    </button>
                </form>
            </div>
        </div>
    );
};

export default LoginPage;
