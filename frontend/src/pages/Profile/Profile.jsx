import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Mail, LogOut, ChevronRight, Settings, Shield, Bell } from 'lucide-react';
import '../../styles/LoginLight.css';

const Profile = () => {
    const navigate = useNavigate();
    const [userData, setUserData] = useState(null);

    useEffect(() => {
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
            setUserData(JSON.parse(storedUser));
        }
    }, []);

    const handleLogout = () => {
        if (window.confirm('로그아웃 하시겠습니까?')) {
            localStorage.removeItem('user');
            navigate('/login');
        }
    };

    return (
        <div className="main-content fade-in">
            <header className="dashboard-header">
                <h1>마이 프로필</h1>
                <p>회원님의 정보를 관리하세요.</p>
            </header>

            {userData && (
                <div className="profile-card dashboard-card" style={{ padding: '32px', marginBottom: '24px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '20px', marginBottom: '32px' }}>
                        <div style={{
                            width: '80px',
                            height: '80px',
                            borderRadius: '50%',
                            background: '#e0e7ff',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: '#4f46e5'
                        }}>
                            <User size={40} />
                        </div>
                        <div>
                            <h2 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 800 }}>{userData.email.split('@')[0]}님</h2>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#94a3b8', fontSize: '0.9rem' }}>
                                <Mail size={14} />
                                {userData.email}
                            </div>
                        </div>
                    </div>

                    <div className="profile-menu" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        {[
                            { icon: Settings, label: '계정 설정', color: '#64748b' },
                            { icon: Shield, label: '보안 및 개인정보', color: '#64748b' },
                            { icon: Bell, label: '알림 설정', color: '#64748b' },
                        ].map((item, idx) => (
                            <div
                                key={idx}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'space-between',
                                    padding: '16px',
                                    borderRadius: '16px',
                                    background: '#f8fafc',
                                    cursor: 'pointer'
                                }}
                            >
                                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                    <item.icon size={20} color={item.color} />
                                    <span style={{ fontWeight: 600 }}>{item.label}</span>
                                </div>
                                <ChevronRight size={18} color="#cbd5e1" />
                            </div>
                        ))}
                    </div>
                </div>
            )}

            <button
                className="secondary-button"
                onClick={handleLogout}
                style={{
                    width: '100%',
                    padding: '18px',
                    color: '#ef4444',
                    borderColor: '#fee2e2',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '10px'
                }}
            >
                <LogOut size={20} />
                로그아웃
            </button>

            <div style={{ height: '80px' }}></div>
        </div>
    );
};

export default Profile;
