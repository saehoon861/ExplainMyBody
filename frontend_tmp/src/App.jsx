import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import MainPage from './pages/MainPage';
import OcrInputPage from './pages/OcrInputPage';
import HealthRecordPage from './pages/HealthRecordPage';
import LlmAnalysisPage from './pages/LlmAnalysisPage';
import WeeklyPlanPage from './pages/WeeklyPlanPage';

function App() {
    return (
        <AuthProvider>
            <Router>
                <Routes>
                    <Route path="/" element={<LoginPage />} />
                    <Route
                        path="/main"
                        element={
                            <ProtectedRoute>
                                <MainPage />
                            </ProtectedRoute>
                        }
                    />
                    <Route
                        path="/ocr"
                        element={
                            <ProtectedRoute>
                                <OcrInputPage />
                            </ProtectedRoute>
                        }
                    />
                    <Route
                        path="/health-records"
                        element={
                            <ProtectedRoute>
                                <HealthRecordPage />
                            </ProtectedRoute>
                        }
                    />
                    <Route
                        path="/analysis"
                        element={
                            <ProtectedRoute>
                                <LlmAnalysisPage />
                            </ProtectedRoute>
                        }
                    />
                    <Route
                        path="/weekly-plan"
                        element={
                            <ProtectedRoute>
                                <WeeklyPlanPage />
                            </ProtectedRoute>
                        }
                    />
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
            </Router>
        </AuthProvider>
    );
}

export default App;
