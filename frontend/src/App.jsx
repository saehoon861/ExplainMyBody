import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Login from './components/Login';
import Signup from './components/Signup';
import InBodyAnalysis from './components/InBodyAnalysis';
import SplashScreen from './components/SplashScreen';
import Dashboard from './components/Dashboard';
import Chatbot from './components/Chatbot';
import MainLayout from './components/MainLayout';

import './AppLight.css';

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

        {/* Protected Routes with MainLayout */}
        <Route path="/dashboard" element={<MainLayout><Dashboard /></MainLayout>} />
        <Route path="/inbody" element={<MainLayout><InBodyAnalysis /></MainLayout>} />
        <Route path="/chatbot" element={<MainLayout><Chatbot /></MainLayout>} />
        <Route path="/profile" element={<MainLayout><div className="main-content"><h1>프로필 준비 중</h1></div></MainLayout>} />
      </Routes>
    </Router>
  );
}

export default App;
