import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import SplashScreen from './components/SplashScreen';
import Dashboard from './components/Dashboard';
import Chatbot from './components/Chatbot';
import ChatbotSelector from './components/ChatbotSelector';
import WorkoutPlan from './components/WorkoutPlan';
import MainLayout from './components/MainLayout';
import Profile from './components/Profile';
import SignupSuccess from './components/SignupSuccess';
import ExerciseGuide from './components/ExerciseGuide';

import './AppLight.css';

function App() {
  const [showSplash, setShowSplash] = useState(false);  // SplashScreen 비활성화 유지

  if (showSplash) {
    return <SplashScreen onFinish={() => setShowSplash(false)} />;
  }

  return (
    <Router>
      <Routes>
        {/* 삭제된 Login 대신 Dashboard를 기본으로 설정 */}
        <Route path="/" element={<MainLayout><Dashboard /></MainLayout>} />
        <Route path="/dashboard" element={<MainLayout><Dashboard /></MainLayout>} />

        <Route path="/signup-success" element={<SignupSuccess />} />
        <Route path="/exercise-guide" element={<MainLayout><ExerciseGuide /></MainLayout>} />
        <Route path="/workout-plan" element={<MainLayout><WorkoutPlan /></MainLayout>} />
        <Route path="/chatbot" element={<MainLayout><ChatbotSelector /></MainLayout>} />
        <Route path="/chatbot/:botType" element={<MainLayout><Chatbot /></MainLayout>} />
        <Route path="/profile" element={<MainLayout><Profile /></MainLayout>} />

        {/* 없는 경로는 모두 대시보드로 리다이렉트 */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
