import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Mail, LogOut, ChevronRight, Settings, Shield, Bell } from 'lucide-react';
import './LoginLight.css';

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

                    <div className="profile-info-grid">
                        <div className="info-item">
                            <span className="info-label">성별</span>
                            <span className="info-value">{userData.gender === 'male' ? '남성' : '여성'}</span>
                        </div>
                        <div className="info-item">
                            <span className="info-label">나이</span>
                            <span className="info-value">{userData.age}세</span>
                        </div>
                        <div className="info-item">
                            <span className="info-label">키</span>
                            <span className="info-value">{userData.height}cm</span>
                        </div>
                        <div className="info-item">
                            <span className="info-label">목표</span>
                            <span className="info-value">{userData.goal_type || '설정 전'}</span>
                        </div>
                    </div>
                </div>
            )}

            {userData && userData.inbody_data && (
                <div className="dashboard-card fade-in delay-1" style={{ marginBottom: '24px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
                        <div style={{ background: '#f0fdf4', color: '#22c55e', padding: '8px', borderRadius: '12px' }}>
                            <Activity size={20} />
                        </div>
                        <h3 style={{ margin: 0 }}>최근 인바디 리포트</h3>
                    </div>

                    <div className="inbody-stats-grid">
                        {(() => {
                            const d = userData.inbody_data || {};
                            const metrics = [
                                { label: '체중', value: d["체중관리"]?.["체중"] || d.weight || userData.start_weight, unit: 'kg' },
                                { label: '골격근량', value: d["체중관리"]?.["골격근량"] || d.skeletal_muscle, unit: 'kg' },
                                { label: '체지방량', value: d["체중관리"]?.["체지방량"] || d.body_fat_mass, unit: 'kg' },
                                { label: 'BMI', value: d["비만분석"]?.["BMI"] || d.bmi, unit: '' },
                                { label: '체지방률', value: d["비만분석"]?.["체지방률"] || d.body_fat_percentage, unit: '%' },
                                { label: '기초대사량', value: d["연구항목"]?.["기초대사량"] || d.bmr, unit: 'kcal' },
                            ];

                            return metrics.map((m, idx) => (
                                <div key={idx} className="inbody-stat-card">
                                    <span className="stat-label">{m.label}</span>
                                    <div className="stat-value-row">
                                        <span className="stat-number">{m.value || '-'}</span>
                                        <span className="stat-unit">{m.unit}</span>
                                    </div>
                                </div>
                            ));
                        })()}
                    </div>
                </div>
            )}

            <div className="profile-menu-container fade-in delay-2">
                {[
                    { icon: Settings, label: '계정 설정', color: '#64748b' },
                    { icon: Shield, label: '보안 및 개인정보', color: '#64748b' },
                    { icon: Bell, label: '알림 설정', color: '#64748b' },
                ].map((item, idx) => (
                    <div
                        key={idx}
                        className="profile-menu-item"
                    >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <item.icon size={20} color={item.color} />
                            <span style={{ fontWeight: 600 }}>{item.label}</span>
                        </div>
                        <ChevronRight size={18} color="#cbd5e1" />
                    </div>
                ))}
            </div>

            <button
                className="secondary-button logout-btn fade-in delay-3"
                onClick={handleLogout}
            >
                <LogOut size={20} />
                로그아웃
            </button>

            <style>{`
                .profile-info-grid {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 16px;
                    padding-top: 24px;
                    border-top: 1px solid #f1f5f9;
                }
                .info-item {
                    display: flex;
                    flex-direction: column;
                    gap: 4px;
                }
                .info-label {
                    font-size: 0.85rem;
                    color: #94a3b8;
                    font-weight: 500;
                }
                .info-value {
                    font-size: 1.1rem;
                    color: #1e293b;
                    font-weight: 700;
                }
                .inbody-stats-grid {
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 12px;
                }
                .inbody-stat-card {
                    background: #f8fafc;
                    padding: 16px;
                    border-radius: 20px;
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                    border: 1px solid #f1f5f9;
                }
                .stat-label {
                    font-size: 0.8rem;
                    color: #64748b;
                    font-weight: 600;
                }
                .stat-value-row {
                    display: flex;
                    align-items: baseline;
                    gap: 2px;
                }
                .stat-number {
                    font-size: 1.2rem;
                    font-weight: 800;
                    color: #4f46e5;
                }
                .stat-unit {
                    font-size: 0.75rem;
                    color: #94a3b8;
                    font-weight: 600;
                }
                .profile-menu-container {
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                    margin-bottom: 24px;
                }
                .profile-menu-item {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: 20px;
                    border-radius: 20px;
                    background: white;
                    border: 1px solid #e2e8f0;
                    cursor: pointer;
                    transition: all 0.2s;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.02);
                }
                .profile-menu-item:hover {
                    transform: translateX(4px);
                    border-color: #cbd5e1;
                    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
                }
                .logout-btn {
                    width: 100%;
                    padding: 20px;
                    color: #ef4444;
                    border-color: #fee2e2;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 10px;
                    border-radius: 20px;
                    font-weight: 800;
                    background: white;
                }
                .logout-btn:hover {
                    background: #fff1f2;
                    border-color: #fecaca;
                }

                @media (max-width: 480px) {
                    .inbody-stats-grid {
                        grid-template-columns: repeat(2, 1fr);
                    }
                }
            `}</style>

            <div style={{ height: '80px' }}></div>
        </div>
    );
};

export default Profile;
