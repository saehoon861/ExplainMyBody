import { useState, Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LoadingSpinner from './components/common/LoadingSpinner';

// Pages - Static Loading (Critical Path)
import Login from './pages/Auth/Login';
import ForgotPassword from './pages/Auth/ForgotPassword';
import Signup from './pages/Auth/Signup';
import SignupSuccess from './pages/Auth/SignupSuccess';
import SplashScreen from './pages/Auth/SplashScreen';

// Pages - Lazy Loading (Deferred)
const Dashboard = lazy(() => import('./pages/Dashboard/Dashboard'));
const InBodyAnalysis = lazy(() => import('./pages/InBody/InBodyAnalysis'));
const Chatbot = lazy(() => import('./pages/Chatbot/Chatbot'));
const ChatbotSelector = lazy(() => import('./pages/Chatbot/ChatbotSelector'));
const WorkoutPlan = lazy(() => import('./pages/Exercise/WorkoutPlan'));
const ExerciseGuide = lazy(() => import('./pages/Exercise/ExerciseGuide'));
const Profile = lazy(() => import('./pages/Profile/Profile'));

// Layout
import MainLayout from './components/layout/MainLayout';

// PWA Install Prompt
import PWAInstallPrompt from './components/common/PWAInstallPrompt';

// Styles
import './styles/App.css';

function App() {
  // PWA 로딩 화면: 세션당 한 번만 표시 (새로고침 또는 앱 재시작시)
  const [showSplash, setShowSplash] = useState(() => {
    // sessionStorage를 사용하여 세션당 한 번만 표시
    const hasShownSplash = sessionStorage.getItem('hasShownSplash');
    return !hasShownSplash;
  });

  const handleSplashFinish = () => {
    sessionStorage.setItem('hasShownSplash', 'true');
    setShowSplash(false);
  };

  if (showSplash) {
    return <SplashScreen onFinish={handleSplashFinish} />;
  }

  return (
    <>
      <Router>
        <Suspense fallback={<LoadingSpinner />}>
          <Routes>
            <Route path="/" element={<Login />} />
            <Route path="/login" element={<Login />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
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
        </Suspense>
      </Router>

      {/* PWA 설치 프롬프트 */}
      <PWAInstallPrompt />
    </>
  );
}

export default App;
