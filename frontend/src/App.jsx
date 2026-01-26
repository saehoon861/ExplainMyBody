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
            <h1>메인 대시보드</h1>
            <p>서비스 메인 화면입니다. 로그인이 성공하면 이곳으로 이동합니다.</p>
          </div>
        } />
      </Routes>
    </Router>
  );
}

export default App;
