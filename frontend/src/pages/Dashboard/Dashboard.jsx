import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate, Link } from 'react-router-dom';
import { LogOut, Activity, User, Home, Edit2, X, Check, Scale, CalendarDays, Dumbbell, Youtube, ChevronRight, Zap, Shield, Heart, Coffee, Droplets, Moon, Apple, ArrowLeft } from 'lucide-react';
import '../../styles/LoginLight.css'; // 스타일 재사용

import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { usePrefetch } from '../../hooks/usePrefetch';
// import { useContainerQuery } from '../../hooks/useContainerQuery'; // Container Query Hook (선택적 사용)

// 건강 정보 카드뉴스 컴포넌트 - 간단한 버전
const HealthTipsSection = () => {
    const [selectedTip, setSelectedTip] = useState(null);

    const healthTips = [
        { id: 1, title: '균형 잡힌 식단', emoji: '🥗', color: '#a78bfa', bg: '#faf5ff', summary: '영양소 섭취 가이드', content: '매끼 채소 2가지 이상 섭취하고, 단백질 15-20%, 탄수화물 50-60%를 유지하세요. 가공식품 대신 자연식품을 선택하고 천천히 씹어먹으세요.' },
        { id: 2, title: '수면의 질 높이기', emoji: '😴', color: '#e879f9', bg: '#fdf4ff', summary: '회복력 극대화', content: '성인 권장 수면 시간은 7-9시간입니다. 매일 같은 시간에 취침하고, 자기 전 1시간은 스마트폰을 피하세요.' },
        { id: 3, title: '수분 섭취 가이드', emoji: '💧', color: '#60a5fa', bg: '#eff6ff', summary: '신진대사 활성화', content: '하루 권장 물 섭취량은 체중 × 30ml입니다. 기상 후 물 한 잔을 마시고, 운동 전후 500ml씩 섭취하세요.' },
        { id: 4, title: '운동 후 회복', emoji: '💪', color: '#f472b6', bg: '#fdf2f8', summary: '근육 성장 팁', content: '운동 후 30분 이내 단백질 20-30g을 섭취하세요. 스트레칭 5-10분, 같은 부위는 48시간 휴식하세요.' }
    ];

    return (
        <>
            {/* 가로 스크롤 카드 */}
            <div style={{
                display: 'flex',
                gap: '16px',
                overflowX: 'auto',
                padding: '8px 0 16px',
                marginLeft: '-16px',
                marginRight: '-16px',
                paddingLeft: '16px',
                paddingRight: '16px',
                scrollbarWidth: 'none',
                msOverflowStyle: 'none'
            }}>
                {healthTips.map((tip) => (
                    <div
                        key={tip.id}
                        onClick={() => setSelectedTip(tip)}
                        style={{
                            flex: '0 0 130px',
                            cursor: 'pointer',
                            textAlign: 'center'
                        }}
                    >
                        <div style={{
                            width: '130px',
                            height: '130px',
                            borderRadius: '20px',
                            border: `3px solid ${tip.color}`,
                            background: tip.bg,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            marginBottom: '10px',
                            fontSize: '48px'
                        }}>
                            {tip.emoji}
                        </div>
                        <h4 style={{
                            fontSize: '0.85rem',
                            fontWeight: 700,
                            color: '#1e293b',
                            margin: 0,
                            lineHeight: 1.4
                        }}>{tip.title}</h4>
                    </div>
                ))}
            </div>

            {/* 모달 */}
            {selectedTip && (
                <div
                    onClick={() => setSelectedTip(null)}
                    style={{
                        position: 'fixed',
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        background: 'rgba(0, 0, 0, 0.5)',
                        zIndex: 999999,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        padding: '20px'
                    }}
                >
                    <div
                        onClick={(e) => e.stopPropagation()}
                        style={{
                            width: '100%',
                            maxWidth: '500px',
                            maxHeight: '80vh',
                            background: 'white',
                            borderRadius: '24px',
                            overflow: 'hidden',
                            position: 'relative',
                            display: 'flex',
                            flexDirection: 'column',
                            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)'
                        }}
                    >
                        <div style={{
                            background: selectedTip.bg,
                            padding: '40px 24px 24px',
                            textAlign: 'center',
                            position: 'relative',
                            flexShrink: 0
                        }}>
                            <button
                                onClick={() => setSelectedTip(null)}
                                style={{
                                    position: 'absolute',
                                    top: '16px',
                                    right: '16px',
                                    background: 'rgba(255,255,255,0.6)',
                                    border: 'none',
                                    borderRadius: '50%',
                                    width: '36px',
                                    height: '36px',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    cursor: 'pointer',
                                    fontSize: '18px',
                                    color: '#475569'
                                }}
                            >✕</button>
                            <div style={{ fontSize: '64px', marginBottom: '16px' }}>{selectedTip.emoji}</div>
                            <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#1e293b', margin: '0 0 8px' }}>{selectedTip.title}</h1>
                            <p style={{ fontSize: '0.95rem', color: '#475569', margin: 0 }}>{selectedTip.summary}</p>
                        </div>
                        <div style={{
                            padding: '24px',
                            overflowY: 'auto'
                        }}>
                            <p style={{ fontSize: '1rem', color: '#334155', lineHeight: 1.6, margin: 0 }}>{selectedTip.content}</p>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};


const Dashboard = () => {
    const navigate = useNavigate();
    const [userData, setUserData] = useState(null);

    // Edge Native: Resource Prefetching for likely next routes
    usePrefetch([
        '/src/pages/Chatbot/Chatbot.jsx',
        '/src/pages/Exercise/WorkoutPlan.jsx',
        '/src/pages/Exercise/ExerciseGuide.jsx'
    ]);

    /* Container Query Hook 사용 예시 (필요시 주석 해제)
    const { ref, width, isSmall, isMedium, isLarge } = useContainerQuery();

    // 사용법:
    // 1. ref를 컨테이너에 연결
    // 2. width, isSmall, isMedium, isLarge로 조건부 렌더링
    //
    // 예시:
    // <div ref={ref} className="dashboard-section">
    //     {isSmall ? <MobileChart /> : <DesktopChart />}
    // </div>
    */

    // 비디오 모달 상태
    const [activeVideo, setActiveVideo] = useState(null);

    // 목표 수정 모달 상태
    const [isEditing, setIsEditing] = useState(false);
    const [showRehabOptions, setShowRehabOptions] = useState(false);
    const [editForm, setEditForm] = useState({
        start_weight: '',
        target_weight: '',
        goal_type: '',
        goal_description: ''
    });

    const openVideo = (type) => {
        let videoId = 'gMaB-fG4u4g'; // 기본: 전신/인트로
        if (type === '상체') videoId = 'tzN69l791VU';
        if (type === '복근') videoId = 'hR5s71aM6fw';
        if (type === '하체') videoId = 'W_VGlKk88K4';

        setActiveVideo({
            id: videoId,
            title: `${type} 운동 가이드`
        });
    };

    useEffect(() => {
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
            const parsedUser = JSON.parse(storedUser);
            setUserData(parsedUser);
            setEditForm({
                start_weight: parsedUser.start_weight || '',
                target_weight: parsedUser.target_weight || '',
                goal_type: parsedUser.goal_type || '감량',
                goal_description: parsedUser.goal_description || ''
            });
        }
    }, []);

    const handleLogout = () => {
        if (window.confirm('로그아웃 하시겠습니까?')) {
            localStorage.removeItem('signup_persist');
            localStorage.removeItem('user');
            navigate('/login');
        }
    };

    const handleEditClick = () => {
        if (userData) {
            setEditForm({
                start_weight: userData.start_weight || '',
                target_weight: userData.target_weight || '',
                goal_type: userData.goal_type || '감량',
                goal_description: userData.goal_description || ''
            });
            setShowRehabOptions(false);
            setIsEditing(true);
        }
    };

    const handleInputChange = (e) => {
        const { name, value } = e.target;

        setEditForm(prev => {
            const updated = { ...prev, [name]: value };

            if (name === 'start_weight' || name === 'target_weight') {
                const start = parseFloat(name === 'start_weight' ? value : prev.start_weight);
                const target = parseFloat(name === 'target_weight' ? value : prev.target_weight);

                if (!isNaN(start) && !isNaN(target)) {
                    if (target < start) {
                        updated.goal_type = '감량';
                    } else if (target > start) {
                        updated.goal_type = '증량';
                    } else {
                        updated.goal_type = '유지';
                    }
                }
            }
            return updated;
        });
    };

    const handleSaveGoal = async () => {
        if (!userData || !userData.id) return;

        try {
            const response = await fetch(`/api/users/${userData.id}/goal`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    start_weight: parseFloat(editForm.start_weight),
                    target_weight: parseFloat(editForm.target_weight),
                    goal_type: editForm.goal_type,
                    goal_description: editForm.goal_description
                }),
            });

            if (response.ok) {
                const updatedUser = await response.json();
                setUserData(updatedUser);
                localStorage.setItem('user', JSON.stringify(updatedUser));
                setIsEditing(false);
                alert('목표가 수정되었습니다.');
            } else {
                const errorData = await response.json();
                if (response.status === 404) {
                    alert('사용자 정보를 찾을 수 없습니다. 다시 로그인해 주세요.');
                    handleLogout();
                } else {
                    alert(`수정 실패: ${errorData.detail}`);
                }
            }
        } catch (error) {
            console.error('Error updating goal:', error);
            if (error.message.includes('404')) {
                alert('사용자 세션이 만료되었습니다. 다시 로그인해 주세요.');
                handleLogout();
            } else {
                alert('서버 통신 중 오류가 발생했습니다.');
            }
        }
    };

    // 차트 데이터 구성
    const getChartData = () => {
        if (!userData) return [];

        const myWeight = userData.inbody_data?.weight || userData.start_weight || 0;
        const myMuscle = userData.inbody_data?.skeletal_muscle || 0;
        const myFat = userData.inbody_data?.body_fat_mass || 0;

        const isMale = userData.gender === 'male';
        const avgWeight = isMale ? 74 : 58;
        const avgMuscle = isMale ? 34 : 22;
        const avgFat = isMale ? 14 : 16;

        return [
            { name: '체중', me: myWeight, avg: avgWeight },
            { name: '골격근량', me: myMuscle, avg: avgMuscle },
            { name: '체지방량', me: myFat, avg: avgFat },
        ];
    };

    const chartData = getChartData();

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
                            <div className="header-actions">
                                <button className="edit-goal-button" onClick={() => openVideo('기본')} title="가이드 영상">
                                    <Youtube size={18} color="#ef4444" />
                                    <span>사용 팁</span>
                                </button>
                                <button className="edit-goal-button" onClick={handleEditClick} title="목표 수정">
                                    <Edit2 size={14} />
                                    <span>목표 수정</span>
                                </button>
                            </div>
                        </div>

                        <div className="weight-progress-container">
                            <div className="weight-info">
                                <span className="label">시작 체중</span>
                                <span className="value">{userData.start_weight || '-'} <span className="unit">kg</span></span>
                            </div>
                            <div className="progress-arrow-container">
                                <div className="goal-badge-center">
                                    {(() => {
                                        if (!userData.goal_type) return '목표';
                                        const goals = userData.goal_type.split(',').map(g => g.trim());
                                        const generalGoals = goals.filter(g => g !== '재활');
                                        return generalGoals.length > 0 ? generalGoals.join(', ') : (goals.includes('재활') ? '건강 재활' : '목표');
                                    })()}
                                </div>
                                <div className="progress-arrow">➔</div>
                            </div>
                            <div className="weight-info target">
                                <span className="label">목표 체중</span>
                                <span className="value highlight">{userData.target_weight || '-'} <span className="unit">kg</span></span>
                            </div>
                        </div>

                        {userData.goal_description && (
                            <div className="goal-description-box fade-in">
                                <span className="rehab-label">선택 항목: </span>
                                <span className="rehab-value">{userData.goal_description}</span>
                            </div>
                        )}
                    </div>

                    <div className="dashboard-card chart-card fade-in delay-2" style={{ marginTop: '24px' }}>
                        <h3>나의 인바디 분석</h3>
                        <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginBottom: '20px' }}>
                            또래 평균 대비 나의 상태를 확인해보세요.
                        </p>
                        <div style={{ width: '100%', height: 350 }}>
                            <ResponsiveContainer width="100%" height="100%">
                                <RadarChart
                                    data={chartData}
                                    margin={{ top: 20, right: 40, bottom: 20, left: 40 }}
                                >
                                    <defs>
                                        <linearGradient id="radarGradientMe" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="0%" stopColor="#818cf8" stopOpacity={0.8} />
                                            <stop offset="100%" stopColor="#818cf8" stopOpacity={0.2} />
                                        </linearGradient>
                                        <linearGradient id="radarGradientAvg" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="0%" stopColor="#64748b" stopOpacity={0.6} />
                                            <stop offset="100%" stopColor="#64748b" stopOpacity={0.1} />
                                        </linearGradient>
                                        <filter id="glow">
                                            <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
                                            <feMerge>
                                                <feMergeNode in="coloredBlur"/>
                                                <feMergeNode in="SourceGraphic"/>
                                            </feMerge>
                                        </filter>
                                    </defs>
                                    <PolarGrid
                                        stroke="rgba(148, 163, 184, 0.2)"
                                        strokeWidth={1.5}
                                        strokeDasharray="3 3"
                                    />
                                    <PolarAngleAxis
                                        dataKey="name"
                                        tick={{ fill: '#64748b', fontSize: 13, fontWeight: 600 }}
                                        tickLine={false}
                                    />
                                    <PolarRadiusAxis
                                        angle={90}
                                        domain={[0, 'auto']}
                                        tick={{ fill: '#94a3b8', fontSize: 11 }}
                                        axisLine={false}
                                        tickCount={5}
                                    />
                                    <Tooltip
                                        contentStyle={{
                                            backgroundColor: '#1e293b',
                                            borderColor: 'rgba(129, 140, 248, 0.3)',
                                            borderRadius: '12px',
                                            padding: '12px',
                                            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.3)'
                                        }}
                                        itemStyle={{ color: '#fff', fontSize: '0.9rem', fontWeight: 500 }}
                                        labelStyle={{ color: '#94a3b8', marginBottom: '8px', fontWeight: 600 }}
                                    />
                                    <Legend
                                        wrapperStyle={{ paddingTop: '24px' }}
                                        formatter={(value) => (
                                            <span style={{
                                                color: '#64748b',
                                                fontSize: '0.9rem',
                                                fontWeight: 600
                                            }}>
                                                {value === 'me' ? '🎯 내 수치' : '📊 평균'}
                                            </span>
                                        )}
                                    />
                                    <Radar
                                        name="avg"
                                        dataKey="avg"
                                        stroke="#64748b"
                                        fill="url(#radarGradientAvg)"
                                        strokeWidth={2}
                                        fillOpacity={0.5}
                                        animationDuration={1200}
                                        animationBegin={0}
                                        animationEasing="ease-out"
                                        dot={{ fill: '#64748b', r: 4 }}
                                    />
                                    <Radar
                                        name="me"
                                        dataKey="me"
                                        stroke="#818cf8"
                                        fill="url(#radarGradientMe)"
                                        strokeWidth={3}
                                        fillOpacity={0.6}
                                        animationDuration={1400}
                                        animationBegin={200}
                                        animationEasing="cubic-bezier(0.175, 0.885, 0.32, 1.275)"
                                        dot={{ fill: '#818cf8', r: 5, filter: 'url(#glow)' }}
                                    />
                                </RadarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="dashboard-card">
                    <h3>로그인이 필요합니다</h3>
                    <p>데이터를 불러오려면 다시 로그인해주세요.</p>
                </div>
            )}

            {/* 비디오 팝업 모달 */}
            {activeVideo && (
                <div className="dashboard-modal-overlay fade-in" onClick={() => setActiveVideo(null)}>
                    <div className="video-modal-card" onClick={e => e.stopPropagation()}>
                        <div className="video-header">
                            <h3>{activeVideo.title}</h3>
                            <button className="close-button" onClick={() => setActiveVideo(null)}>
                                <X size={24} />
                            </button>
                        </div>
                        <div className="video-container">
                            <iframe
                                width="100%"
                                height="100%"
                                src={`https://www.youtube.com/embed/${activeVideo.id}?autoplay=1`}
                                title="YouTube video player"
                                frameBorder="0"
                                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                allowFullScreen
                            ></iframe>
                        </div>
                    </div>
                </div>
            )}

            {/* 목표 수정 모달 */}
            {isEditing && (
                <div className="dashboard-modal-overlay fade-in">
                    <div className="dashboard-modal-card">
                        <div className="dashboard-modal-header">
                            <h3>목표 수정하기</h3>
                            <button className="close-button" onClick={() => setIsEditing(false)}>
                                <X size={20} />
                            </button>
                        </div>
                        <div className="dashboard-modal-body">
                            <div className="form-group">
                                <label>목표 타입 (다중 선택 가능)</label>
                                <div className="gender-select">
                                    {['감량', '유지', '증량', '재활'].map(type => {
                                        const selectedGoals = editForm.goal_type ? editForm.goal_type.split(',').map(g => g.trim()).filter(g => g !== '') : [];
                                        const isSelected = selectedGoals.includes(type);
                                        return (
                                            <button
                                                key={type}
                                                type="button"
                                                className={`gender-btn ${isSelected ? 'selected' : ''}`}
                                                onClick={() => {
                                                    const generalGoals = ['감량', '유지', '증량'];
                                                    let newGoals;

                                                    if (generalGoals.includes(type)) {
                                                        if (isSelected) {
                                                            newGoals = selectedGoals.filter(g => g !== type);
                                                        } else {
                                                            newGoals = selectedGoals.filter(g => !generalGoals.includes(g));
                                                            newGoals.push(type);
                                                        }
                                                    } else {
                                                        if (isSelected) {
                                                            newGoals = selectedGoals.filter(g => g !== type);
                                                            setShowRehabOptions(false);
                                                        } else {
                                                            newGoals = [...selectedGoals, type];
                                                            setShowRehabOptions(true);
                                                        }
                                                    }

                                                    const order = ['감량', '유지', '증량', '재활'];
                                                    newGoals.sort((a, b) => order.indexOf(a) - order.indexOf(b));

                                                    setEditForm(prev => ({
                                                        ...prev,
                                                        goal_type: newGoals.join(', '),
                                                        goal_description: newGoals.includes('재활') ? prev.goal_description : ''
                                                    }));
                                                }}
                                            >
                                                {type}
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>

                            {editForm.goal_type && editForm.goal_type.includes('재활') && showRehabOptions && (
                                <div className="form-group fade-in">
                                    <label>재활 부위 (다중 선택 가능)</label>
                                    <div className="gender-select" style={{ gridTemplateColumns: 'repeat(2, 1fr)' }}>
                                        {['허리 재활', '어깨 재활', '무릎 재활', '목 재활', '발목 재활'].map(part => {
                                            const selectedParts = editForm.goal_description ? editForm.goal_description.split(',').map(p => p.trim()).filter(p => p !== '') : [];
                                            const isSelected = selectedParts.includes(part);

                                            return (
                                                <button
                                                    key={part}
                                                    type="button"
                                                    className={`gender-btn ${isSelected ? 'selected' : ''}`}
                                                    onClick={() => {
                                                        let newParts;
                                                        if (isSelected) {
                                                            newParts = selectedParts.filter(p => p !== part);
                                                        } else {
                                                            newParts = [...selectedParts, part];
                                                        }
                                                        setEditForm(prev => ({ ...prev, goal_description: newParts.join(', ') }));
                                                    }}
                                                >
                                                    {part}
                                                </button>
                                            );
                                        })}
                                        <button
                                            type="button"
                                            className={`gender-btn ${(() => {
                                                const standardParts = ['허리 재활', '어깨 재활', '무릎 재활', '목 재활', '발목 재활'];
                                                const parts = editForm.goal_description ? editForm.goal_description.split(',').map(p => p.trim()).filter(p => p !== '') : [];
                                                return parts.some(p => !standardParts.includes(p)) || (editForm.goal_description && editForm.goal_description.endsWith(' ')) || editForm.goal_description === ' ';
                                            })() ? 'selected' : ''}`}
                                            onClick={() => {
                                                const standardParts = ['허리 재활', '어깨 재활', '무릎 재활', '목 재활', '발목 재활'];
                                                const parts = editForm.goal_description ? editForm.goal_description.split(',').map(p => p.trim()).filter(p => p !== '') : [];
                                                const hasOther = parts.some(p => !standardParts.includes(p));

                                                if (hasOther || (editForm.goal_description && editForm.goal_description.endsWith(' '))) {
                                                    const newParts = parts.filter(p => standardParts.includes(p));
                                                    setEditForm(prev => ({ ...prev, goal_description: newParts.join(', ') }));
                                                } else {
                                                    const prefix = editForm.goal_description ? (editForm.goal_description.endsWith(', ') ? editForm.goal_description : editForm.goal_description + ', ') : '';
                                                    setEditForm(prev => ({ ...prev, goal_description: prefix + ' ' }));
                                                }
                                            }}
                                        >
                                            기타
                                        </button>
                                    </div>
                                    {(() => {
                                        const standardParts = ['허리 재활', '어깨 재활', '무릎 재활', '목 재활', '발목 재활'];
                                        const fullDesc = editForm.goal_description || '';
                                        const parts = fullDesc.split(',').map(p => p.trim()).filter(p => p !== '');
                                        const otherValue = parts.find(p => !standardParts.includes(p)) || (fullDesc.endsWith(' ') ? '' : null);

                                        if (otherValue !== null) {
                                            return (
                                                <input
                                                    type="text"
                                                    placeholder="그 외 재활 부위를 입력해주세요"
                                                    className="modal-input"
                                                    style={{ marginTop: '10px' }}
                                                    value={otherValue}
                                                    onChange={(e) => {
                                                        const val = e.target.value;
                                                        const baseParts = parts.filter(p => standardParts.includes(p));
                                                        if (val) {
                                                            setEditForm(prev => ({ ...prev, goal_description: [...baseParts, val].join(', ') }));
                                                        } else {
                                                            const newDesc = baseParts.join(', ') + (baseParts.length > 0 ? ', ' : '') + ' ';
                                                            setEditForm(prev => ({ ...prev, goal_description: newDesc }));
                                                        }
                                                    }}
                                                />
                                            );
                                        }
                                        return null;
                                    })()}
                                </div>
                            )}

                            <div className="form-group-row">
                                <div className="form-group">
                                    <label>시작 체중 (kg)</label>
                                    <input
                                        type="number"
                                        name="start_weight"
                                        className="modal-input"
                                        value={editForm.start_weight}
                                        onChange={handleInputChange}
                                    />
                                </div>
                                <div className="form-group">
                                    <label>목표 체중 (kg)</label>
                                    <input
                                        type="number"
                                        name="target_weight"
                                        className="modal-input"
                                        value={editForm.target_weight}
                                        onChange={handleInputChange}
                                    />
                                </div>
                            </div>
                        </div>
                        <div className="dashboard-modal-footer">
                            <button className="secondary-button" onClick={() => setIsEditing(false)}>취소</button>
                            <button className="primary-button" onClick={handleSaveGoal}>저장하기</button>
                        </div>
                    </div>
                </div>
            )}

            <div className="quick-actions-grid fade-in delay-1">
                <Link to="/workout-plan" className="action-card primary">
                    <div className="icon-box">
                        <CalendarDays size={24} />
                    </div>
                    <div className="text-box">
                        <h3>주간 운동 계획표</h3>
                        <p>이번 주 운동 스케줄 확인하기</p>
                    </div>
                </Link>

                <Link to="/chatbot" className="action-card primary">
                    <div className="icon-box">
                        <User size={24} />
                    </div>
                    <div className="text-box">
                        <h3>AI 상담소</h3>
                        <p>궁금한 점 물어보기</p>
                    </div>
                </Link>
            </div>

            <div className="section-title fade-in delay-2" style={{ marginTop: '32px', marginBottom: '16px' }}>
                <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 800 }}>부위별 운동법 가이드</h3>
            </div>

            <div className="quick-actions-grid fade-in delay-2 exercise-category-grid">
                <div onClick={() => openVideo('상체')} className="action-card" style={{ cursor: 'pointer' }}>
                    <div className="icon-box" style={{ background: '#eef2ff', color: '#6366f1' }}>
                        <Zap size={24} />
                    </div>
                    <div className="text-box">
                        <h3>상체</h3>
                    </div>
                    <ChevronRight size={16} color="#cbd5e1" style={{ alignSelf: 'flex-end' }} />
                </div>

                <div onClick={() => openVideo('복근')} className="action-card" style={{ cursor: 'pointer' }}>
                    <div className="icon-box" style={{ background: '#fff1f2', color: '#f43f5e' }}>
                        <Shield size={24} />
                    </div>
                    <div className="text-box">
                        <h3>복근</h3>
                    </div>
                    <ChevronRight size={16} color="#cbd5e1" style={{ alignSelf: 'flex-end' }} />
                </div>

                <div onClick={() => openVideo('하체')} className="action-card" style={{ cursor: 'pointer' }}>
                    <div className="icon-box" style={{ background: '#f0fdf4', color: '#22c55e' }}>
                        <Activity size={24} />
                    </div>
                    <div className="text-box">
                        <h3>하체</h3>
                    </div>
                    <ChevronRight size={16} color="#cbd5e1" style={{ alignSelf: 'flex-end' }} />
                </div>
            </div>

            {/* 건강 정보 카드뉴스 섹션 */}
            <div className="section-title fade-in delay-3" style={{ marginTop: '32px', marginBottom: '16px' }}>
                <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 800 }}>💡 건강 정보 & 팁</h3>
            </div>

            <HealthTipsSection />

            <div style={{ height: '100px' }}></div>

            <style>{`
                .video-modal-card {
                    background: black;
                    border-radius: 20px;
                    width: 100%;
                    max-width: 600px;
                    overflow: hidden;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.5);
                    animation: slideUp 0.3s ease-out;
                }
                .video-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 16px 20px;
                    background: #1a1a1a;
                }
                .video-header h3 {
                    margin: 0;
                    color: white;
                    font-size: 1.1rem;
                }
                .video-container {
                    aspect-ratio: 16 / 9;
                    width: 100%;
                    overflow: hidden;
                    background: black;
                    border-radius: 0 0 12px 12px;
                }
                .video-container iframe {
                    width: 100%;
                    height: 100%;
                    border: none;
                }

                /* Fallback for older browsers */
                @supports not (aspect-ratio: 16 / 9) {
                    .video-container {
                        position: relative;
                        padding-bottom: 56.25%;
                        height: 0;
                    }
                    .video-container iframe {
                        position: absolute;
                        top: 0;
                        left: 0;
                    }
                }
                .header-actions {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                .edit-goal-button {
                    background: white;
                    border: none;
                    border-radius: 20px;
                    padding: 8px 16px;
                    height: 36px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 6px;
                    color: #4f46e5;
                    cursor: pointer;
                    transition: all 0.2s;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                    font-size: 0.9rem;
                    font-weight: 600;
                    position: relative;
                    z-index: 10;
                }
                .edit-goal-button:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
                    background: #f8fafc;
                }
                .dashboard-modal-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0, 0, 0, 0.5);
                    backdrop-filter: blur(5px);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 99999;
                    padding: 20px;
                }
                .dashboard-modal-card {
                    background: white;
                    border-radius: 20px;
                    width: 100%;
                    max-width: 400px;
                    padding: 24px;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
                    animation: slideUp 0.3s ease-out;
                    max-height: 90vh;
                    overflow-y: auto;
                }
                .dashboard-modal-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 20px;
                }
                .dashboard-modal-header h3 {
                    margin: 0;
                    font-size: 1.25rem;
                    color: #1e293b;
                    font-weight: 700;
                }
                .close-button {
                    background: none;
                    border: none;
                    color: #64748b;
                    cursor: pointer;
                    padding: 4px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .dashboard-modal-body {
                    display: flex;
                    flex-direction: column;
                    gap: 20px;
                }
                .form-group-row {
                    display: flex;
                    gap: 12px;
                }
                .form-group-row .form-group {
                    flex: 1;
                }
                .form-group label {
                    display: block;
                    font-size: 0.9rem;
                    color: #64748b;
                    margin-bottom: 8px;
                    font-weight: 500;
                }
                .modal-input {
                    width: 100%;
                    padding: 12px;
                    border: 1px solid #e2e8f0;
                    border-radius: 12px;
                    font-size: 1rem;
                    color: #1e293b;
                    background: #f8fafc;
                    transition: all 0.2s;
                    box-sizing: border-box;
                }
                .modal-input:focus {
                    outline: none;
                    border-color: #818cf8;
                    background: white;
                    box-shadow: 0 0 0 3px rgba(129, 140, 248, 0.1);
                }
                .gender-select {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 8px;
                }
                .gender-btn {
                    padding: 10px;
                    border: 1px solid #e2e8f0;
                    border-radius: 12px;
                    background: white;
                    color: #64748b;
                    font-size: 0.9rem;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                .gender-btn:hover {
                    background: #f8fafc;
                    border-color: #cbd5e1;
                }
                .gender-btn.selected {
                    background: #e0e7ff;
                    border-color: #818cf8;
                    color: #4f46e5;
                    font-weight: 600;
                }
                .dashboard-modal-footer {
                    display: flex;
                    gap: 12px;
                    margin-top: 24px;
                }
                .dashboard-modal-footer button {
                    flex: 1;
                }
                @keyframes slideUp {
                    from { transform: translateY(20px); opacity: 0; }
                    to { transform: translateY(0); opacity: 1; }
                }
                .progress-arrow-container {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 8px;
                }
                .goal-badge-center {
                    background: rgba(255, 255, 255, 0.2);
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-size: 0.85rem;
                    color: #fff;
                    font-weight: 500;
                    backdrop-filter: blur(4px);
                }
                .exercise-category-grid {
                    grid-template-columns: repeat(3, 1fr);
                }
                @media (max-width: 768px) {
                    .exercise-category-grid {
                        grid-template-columns: 1fr;
                    }
                    .dashboard-modal-card {
                        max-width: 90%;
                        padding: 20px;
                    }
                    .form-group-row {
                        flex-direction: column;
                    }
                    .gender-select {
                        grid-template-columns: repeat(2, 1fr);
                    }
                }
                @media (max-width: 480px) {
                    .edit-goal-button span {
                        display: none;
                    }
                    .dashboard-modal-card {
                        padding: 16px;
                    }
                    .modal-input {
                        font-size: 0.95rem;
                    }
                }
            `}</style>
        </div>
    );
};

export default Dashboard;
