import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { LogOut, Activity, User, Home } from 'lucide-react';

const Dashboard = () => {
    const navigate = useNavigate();
    const [userData, setUserData] = React.useState(null);

    React.useEffect(() => {
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
            setUserData(JSON.parse(storedUser));
        }
    }, []);

    const handleLogout = () => {
        if (window.confirm('로그아웃 하시겠습니까?')) {
            // 세션 데이터 삭제
            localStorage.removeItem('signup_persist');
            // 로그인 페이지로 이동
            navigate('/login');
        }
    };

    return (
        <div className="main-content">
            <header className="dashboard-header">
                <div className="header-top">
                    <h1>ExplainMyBody</h1>
                    <button className="logout-button" onClick={handleLogout} title="로그아웃">
                        <LogOut size={20} />
                        <span>로그아웃</span>
                    </button>
                </div>
            </header>

            {userData ? (
                <div className="dashboard-hero-section fade-in">
                    <div className="goal-overview-card">
                        <div className="goal-header">
                            <span className="user-greeting">안녕하세요, {userData.email.split('@')[0]}님!</span>
                            <span className="goal-badge">{userData.goal_type || '목표 설정 중'}</span>
                        </div>

                        <div className="weight-progress-container">
                            <div className="weight-info">
                                <span className="label">시작 체중</span>
                                <span className="value">{userData.start_weight || '-'} <span className="unit">kg</span></span>
                            </div>
                            <div className="progress-arrow">
                                ➔
                            </div>
                            <div className="weight-info target">
                                <span className="label">목표 체중</span>
                                <span className="value highlight">{userData.target_weight || '-'} <span className="unit">kg</span></span>
                            </div>
                        </div>

                        <div className="goal-description-box">
                            " {userData.goal_description || '아직 목표 다짐이 없습니다.'} "
                        </div>
                    </div>
                </div>
            ) : (
                <div className="dashboard-card">
                    <h3>로그인이 필요합니다</h3>
                    <p>데이터를 불러오려면 다시 로그인해주세요.</p>
                </div>
            )}

            <div className="quick-actions-grid fade-in delay-1">
                <Link to="/inbody" className="action-card primary">
                    <div className="icon-box">
                        <Activity size={24} />
                    </div>
                    <div className="text-box">
                        <h3>인바디 분석</h3>
                        <p>건강 상태 체크하기</p>
                    </div>
                </Link>

                <Link to="/chatbot" className="action-card">
                    <div className="icon-box">
                        <User size={24} />
                    </div>
                    <div className="text-box">
                        <h3>AI 상담소</h3>
                        <p>궁금한 점 물어보기</p>
                    </div>
                </Link>
            </div>

            <div style={{ height: '100px' }}></div> {/* Spacer for bottom nav */}
        </div>
    );
};

export default Dashboard;
