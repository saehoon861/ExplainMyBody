import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import SplashScreen from './components/SplashScreen';
import Login from './components/Login';
import Signup from './components/Signup';
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
  const [showSplash, setShowSplash] = useState(false);

  if (showSplash) {
    return <SplashScreen onFinish={() => setShowSplash(false)} />;
  }

  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />

        <Route path="/dashboard" element={<MainLayout><Dashboard /></MainLayout>} />
        <Route path="/signup-success" element={<SignupSuccess />} />
        <Route path="/exercise-guide" element={<MainLayout><ExerciseGuide /></MainLayout>} />
        <Route path="/workout-plan" element={<MainLayout><WorkoutPlan /></MainLayout>} />
        <Route path="/chatbot" element={<MainLayout><ChatbotSelector /></MainLayout>} />
        <Route path="/chatbot/:botType" element={<MainLayout><Chatbot /></MainLayout>} />
        <Route path="/profile" element={<MainLayout><Profile /></MainLayout>} />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
