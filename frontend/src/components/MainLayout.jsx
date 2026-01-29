import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import { Home, MessageCircle, ScanText, User, Dumbbell } from 'lucide-react';

const MainLayout = ({ children }) => {
    const location = useLocation();

    const navItems = [
        { path: '/dashboard', icon: Home, label: '홈' },
        { path: '/chatbot', icon: MessageCircle, label: '챗봇' },
        { path: '/exercise-guide', icon: Dumbbell, label: '운동법' },
        { path: '/inbody', icon: ScanText, label: 'OCR' },
        { path: '/profile', icon: User, label: '프로필' },
    ];

    return (
        <div className="app-layout">
            <main className="main-content-container">
                {children}
            </main>

            <nav className="bottom-nav fixed-nav">
                {navItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = location.pathname === item.path;
                    return (
                        <Link
                            key={item.path}
                            to={item.path}
                            className={`nav-item ${isActive ? 'active' : ''}`}
                        >
                            <Icon size={24} />
                            <span>{item.label}</span>
                        </Link>
                    );
                })}
            </nav>
        </div>
    );
};

export default MainLayout;
