import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';

// Pages
import Login from './pages/Auth/Login';
import Signup from './pages/Auth/Signup';
import SignupSuccess from './pages/Auth/SignupSuccess';
import SplashScreen from './pages/Auth/SplashScreen';
import Dashboard from './pages/Dashboard/Dashboard';
import InBodyAnalysis from './pages/InBody/InBodyAnalysis';
import Chatbot from './pages/Chatbot/Chatbot';
import ChatbotSelector from './pages/Chatbot/ChatbotSelector';
import WorkoutPlan from './pages/Exercise/WorkoutPlan';
import ExerciseGuide from './pages/Exercise/ExerciseGuide';
import Profile from './pages/Profile/Profile';

// Layout
import MainLayout from './components/layout/MainLayout';

// Styles
import './styles/AppLight.css';

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
