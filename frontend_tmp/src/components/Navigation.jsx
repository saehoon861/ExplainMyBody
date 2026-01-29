import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Navigation.css';

const Navigation = () => {
    const { isAuthenticated, logout, user } = useAuth();

    if (!isAuthenticated) {
        return null;
    }

    return (
        <nav className="navigation">
            <div className="nav-container">
                <Link to="/main" className="nav-brand">
                    ExplainMyBody
                </Link>
                <div className="nav-links">
                    <Link to="/main" className="nav-link">대시보드</Link>
                    <Link to="/ocr" className="nav-link">OCR 입력</Link>
                    <Link to="/health-records" className="nav-link">건강 기록</Link>
                    <Link to="/analysis" className="nav-link">AI 분석</Link>
                    <Link to="/weekly-plan" className="nav-link">주간 계획</Link>
                </div>
                <div className="nav-user">
                    <span className="user-name">{user?.username || '사용자'}</span>
                    <button onClick={logout} className="logout-btn">로그아웃</button>
                </div>
            </div>
        </nav>
    );
};

export default Navigation;
