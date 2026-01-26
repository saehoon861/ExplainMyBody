import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Login from './components/Login';
import Signup from './components/Signup';
import SplashScreen from './components/SplashScreen';

import './App.css';

function App() {
  const [showSplash, setShowSplash] = useState(true);

  if (showSplash) {
    return <SplashScreen onFinish={() => setShowSplash(false)} />;
  }

  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/dashboard" element={
          <div className="main-content">
            <header className="dashboard-header">
              <h1>메인 대시보드</h1>
              <p>내 몸을 위한 스마트한 관리, 지금 시작하세요.</p>
            </header>
            <div className="dashboard-card">
              <h3>환영합니다! 👋</h3>
              <p>이곳에 당신의 운동 계획과 건강 리포트가 요약되어 표시될 예정입니다.</p>
              <div style={{ marginTop: '20px', color: '#818cf8', fontSize: '0.9rem' }}>
                기능이 차례로 구현될 예정입니다. 준비 중이니 조금만 기다려주세요!
              </div>
            </div>
          </div>
        } />
      </Routes>
    </Router>
  );
}

export default App;
