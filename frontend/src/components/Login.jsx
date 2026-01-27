import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Mail, Lock, Chrome, Github, MessageCircle } from 'lucide-react';
import './Login.css';

// 카카오 로그인 설정 (환경 변수 사용 권장)
const KAKAO_CLIENT_ID = import.meta.env.VITE_KAKAO_CLIENT_ID || "YOUR_KAKAO_CLIENT_ID";
const KAKAO_REDIRECT_URI = import.meta.env.VITE_KAKAO_REDIRECT_URI || "http://localhost:5173/auth/kakao/callback";
const KAKAO_AUTH_URL = `https://kauth.kakao.com/oauth/authorize?client_id=${KAKAO_CLIENT_ID}&redirect_uri=${KAKAO_REDIRECT_URI}&response_type=code`;

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleLogin = (e) => {
    e.preventDefault();
    // 로그인 로직 (현재는 목업으로 바로 메인 이동)
    console.log('Login attempt:', { email, password });
    navigate('/dashboard');
  };

  const handleKakaoLogin = () => {
    window.location.href = KAKAO_AUTH_URL;
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>ExplainMyBody</h1>
          <p>내 몸을 더 잘 이해하는 시작</p>
        </div>

        <form onSubmit={handleLogin}>
          <div className="form-group">
            <label>이메일</label>
            <div className="input-wrapper">
              <Mail size={20} />
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
              <Lock size={20} />
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
            <Link to="/forgot-password">비밀번호 찾기</Link>
          </div>

          <button type="submit" className="primary-button">
            로그인
          </button>
        </form>

        <div className="social-login">
          <div className="social-divider">
            <span>소셜 계정으로 로그인</span>
          </div>
          <div className="social-buttons">
            <button className="social-btn google" title="Google">
              <Chrome size={26} />
            </button>
            <button className="social-btn kakao" title="Kakao" onClick={handleKakaoLogin}>
              <MessageCircle size={26} />
            </button>
            <button className="social-btn naver" title="Naver">
              <span style={{ fontWeight: '900', fontSize: '1.5rem' }}>N</span>
            </button>
          </div>
        </div>

        <div className="login-footer">
          계정이 없으신가요? <Link to="/signup">회원가입</Link>
        </div>
      </div>
    </div>
  );
};

export default Login;
