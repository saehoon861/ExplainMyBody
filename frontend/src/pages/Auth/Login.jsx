import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Mail, Lock, Chrome, Github, MessageCircle } from 'lucide-react';
import '../../styles/LoginLight.css';

// 카카오 로그인 설정 (환경 변수 사용 권장)
const KAKAO_CLIENT_ID = import.meta.env.VITE_KAKAO_CLIENT_ID || "YOUR_KAKAO_CLIENT_ID";
const KAKAO_REDIRECT_URI = import.meta.env.VITE_KAKAO_REDIRECT_URI || "http://localhost:5173/auth/kakao/callback";
const KAKAO_AUTH_URL = `https://kauth.kakao.com/oauth/authorize?client_id=${KAKAO_CLIENT_ID}&redirect_uri=${KAKAO_REDIRECT_URI}&response_type=code`;

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        let errorMessage = '이메일 또는 비밀번호가 올바르지 않습니다.';
        try {
          const errorData = await response.json();
          if (errorData.detail) {
            if (typeof errorData.detail === 'object') {
              // Pydantic validation error or complex error object
              errorMessage = JSON.stringify(errorData.detail, null, 2);
              if (Array.isArray(errorData.detail)) {
                errorMessage = errorData.detail
                  .map(err => {
                    const field = err.loc ? err.loc.join(' -> ') : 'Field';
                    return `${field}: ${err.msg}`;
                  })
                  .join('\n');
              }
            } else {
              errorMessage = errorData.detail;
            }
          }
        } catch (e) {
          console.error('Non-JSON error response:', e);
        }
        alert(errorMessage);
        return;
      }

      const data = await response.json();
      console.log('Login successful:', data);

      // 사용자 정보 저장
      localStorage.setItem('user', JSON.stringify(data));
      // signup_persist 제거 (중복 방지)
      localStorage.removeItem('signup_persist');

      navigate('/dashboard');
    } catch (error) {
      console.error('Login error:', error);
      alert('로그인 중 오류가 발생했습니다. 서버 연결을 확인해주세요.');
    }
  };

  const handleKakaoLogin = () => {
    window.location.href = KAKAO_AUTH_URL;
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header fade-in delay-1">
          <h1>ExplainMyBody</h1>
          <p>내 몸을 더 잘 이해하는 시작</p>
        </div>

        <form onSubmit={handleLogin}>
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
              />
            </div>
          </div>

          <div className="form-group fade-in delay-3">
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
          <div className="form-options fade-in delay-3">
            <Link to="/forgot-password">비밀번호 찾기</Link>
          </div>

          <button type="submit" className="primary-button fade-in delay-4">
            로그인
          </button>
        </form>

        <div className="social-login fade-in delay-5">
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
              <span style={{ fontWeight: '900', fontSize: '1.8rem' }}>N</span>
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
