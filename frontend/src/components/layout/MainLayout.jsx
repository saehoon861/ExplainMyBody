import React, { useState, useEffect } from 'react';
import { useLocation, Link } from 'react-router-dom';
import { Home, MessageCircle, ClipboardList, User, Dumbbell, Moon, Sun } from 'lucide-react';

const MainLayout = ({ children }) => {
    const location = useLocation();
    const [theme, setTheme] = useState('light');

    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
    }, [theme]);

    const toggleTheme = () => {
        setTheme((prevTheme) => (prevTheme === 'light' ? 'dark' : 'light'));
    };

    const navItems = [
        { path: '/dashboard', icon: Home, label: '홈' },
        { path: '/chatbot', icon: MessageCircle, label: '챗봇' },
        { path: '/exercise-guide', icon: Dumbbell, label: '운동법' },
        { path: '/inbody', icon: ClipboardList, label: '신체기록' },
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
                {/* Theme Toggle Button */}
                <div className="nav-item" onClick={toggleTheme} style={{ cursor: 'pointer' }}>
                    {theme === 'light' ? <Moon size={24} /> : <Sun size={24} />}
                    <span>{theme === 'light' ? '다크 모드' : '라이트 모드'}</span>
                </div>
            </nav>
        </div>
    );
};

export default MainLayout;

