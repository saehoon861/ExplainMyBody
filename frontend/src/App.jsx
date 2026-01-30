import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Login from './components/Login';
import Signup from './components/Signup';
import InBodyAnalysis from './components/InBodyAnalysis';
import SplashScreen from './components/SplashScreen';
import Dashboard from './components/Dashboard';
import Chatbot from './components/Chatbot';
import ChatbotSelector from './components/ChatbotSelector';
import WorkoutPlan from './components/WorkoutPlan';
import MainLayout from './components/MainLayout';
import Profile from './components/Profile';
import SignupSuccess from './components/SignupSuccess';
import ExerciseGuide from './components/ExerciseGuide';
import DietPlan from './components/DietPlan';
import DailyRecord from './components/DailyRecord';

import './AppLight.css';

function App() {
  const [showSplash, setShowSplash] = useState(false);  // 임시로 false - SplashScreen 비활성화

  if (showSplash) {
    return <SplashScreen onFinish={() => setShowSplash(false)} />;
  }

  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/signup-success" element={<SignupSuccess />} />

        {/* Protected Routes with MainLayout */}
        <Route path="/dashboard" element={<MainLayout><Dashboard /></MainLayout>} />
        <Route path="/exercise-guide" element={<MainLayout><ExerciseGuide /></MainLayout>} />
        <Route path="/diet-plan" element={<MainLayout><DietPlan /></MainLayout>} />
        <Route path="/daily-record" element={<MainLayout><DailyRecord /></MainLayout>} />
        <Route path="/inbody" element={<MainLayout><InBodyAnalysis /></MainLayout>} />
        <Route path="/workout-plan" element={<MainLayout><WorkoutPlan /></MainLayout>} />
        <Route path="/chatbot" element={<MainLayout><ChatbotSelector /></MainLayout>} />
        <Route path="/chatbot/:botType" element={<MainLayout><Chatbot /></MainLayout>} />
        <Route path="/profile" element={<MainLayout><Profile /></MainLayout>} />
      </Routes>
    </Router>
  );
}

export default App;
