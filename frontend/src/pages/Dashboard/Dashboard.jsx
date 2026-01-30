import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { LogOut, Activity, User, Home, Edit2, X, Check, Scale, CalendarDays, Dumbbell, Youtube, ChevronRight, Zap, Shield } from 'lucide-react';
import '../../styles/LoginLight.css'; // 스타일 재사용

import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, Cell, CartesianGrid } from 'recharts';

const Dashboard = () => {
    const navigate = useNavigate();
    const [userData, setUserData] = useState(null);

    // 목표 수정 모달 상태
    const [isEditing, setIsEditing] = useState(false);
    const [showRehabOptions, setShowRehabOptions] = useState(false); // 재활 부위 선택지 표시 여부
    const [editForm, setEditForm] = useState({
        start_weight: '',
        target_weight: '',
        goal_type: '',
        goal_description: ''
    });

    useEffect(() => {
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
            const parsedUser = JSON.parse(storedUser);
            setUserData(parsedUser);
            // 초기 수정 폼 데이터 설정
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
            localStorage.removeItem('user'); // 사용자 정보도 삭제
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
            setShowRehabOptions(false); // 모달 열 때 재활 선택지 숨김
            setIsEditing(true);
        }
    };

    const handleInputChange = (e) => {
        const { name, value } = e.target;

        setEditForm(prev => {
            const updated = { ...prev, [name]: value };

            // 체중 변경 시 목표 타입 자동 계산
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
                localStorage.setItem('user', JSON.stringify(updatedUser)); // 로컬 스토리지 업데이트
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

        // 사용자 데이터 (inbody_data가 있으면 사용, 없으면 start_weight만 사용)
        const myWeight = userData.inbody_data?.weight || userData.start_weight || 0;
        const myMuscle = userData.inbody_data?.skeletal_muscle || 0;
        const myFat = userData.inbody_data?.body_fat_mass || 0;

        // 평균 데이터 (Mock) - 성별에 따라 다르게 설정 가능
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

                    {/* 인바디 비교 그래프 섹션 */}
                    <div className="dashboard-card chart-card fade-in delay-2" style={{ marginTop: '24px' }}>
                        <h3>나의 인바디 분석</h3>
                        <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginBottom: '20px' }}>
                            또래 평균 대비 나의 상태를 확인해보세요.
                        </p>
                        <div style={{ width: '100%', height: 300 }}>
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart
                                    data={chartData}
                                    margin={{ top: 20, right: 30, left: 0, bottom: 5 }}
                                    barGap={8}
                                >
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.1)" />
                                    <XAxis
                                        dataKey="name"
                                        axisLine={false}
                                        tickLine={false}
                                        tick={{ fill: '#94a3b8', fontSize: 12 }}
                                        dy={10}
                                    />
                                    <YAxis
                                        hide={true}
                                    />
                                    <Tooltip
                                        cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                                        contentStyle={{ backgroundColor: '#1e293b', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '12px', padding: '12px' }}
                                        itemStyle={{ color: '#fff', fontSize: '0.9rem' }}
                                        labelStyle={{ color: '#94a3b8', marginBottom: '8px' }}
                                    />
                                    <Legend
                                        wrapperStyle={{ paddingTop: '20px' }}
                                        formatter={(value) => <span style={{ color: '#94a3b8', fontSize: '0.9rem' }}>{value === 'me' ? '내 수치' : '평균'}</span>}
                                    />
                                    <Bar
                                        dataKey="me"
                                        name="me"
                                        fill="#818cf8"
                                        radius={[6, 6, 0, 0]}
                                        animationDuration={800}
                                        animationBegin={200}
                                        animationEasing="cubic-bezier(0.175, 0.885, 0.32, 1.275)"
                                    >
                                        <Cell fill="#818cf8" />
                                    </Bar>
                                    <Bar
                                        dataKey="avg"
                                        name="avg"
                                        fill="#334155"
                                        radius={[6, 6, 0, 0]}
                                        animationDuration={800}
                                        animationBegin={400}
                                        animationEasing="cubic-bezier(0.175, 0.885, 0.32, 1.275)"
                                    />
                                </BarChart>
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
                                                        // 감량/유지/증량은 배타적 선택 (라디오 버튼처럼)
                                                        if (isSelected) {
                                                            // 이미 선택된 것을 다시 클릭하면 해제
                                                            newGoals = selectedGoals.filter(g => g !== type);
                                                        } else {
                                                            // 다른 일반 목표를 모두 제거하고 현재 선택만 추가
                                                            newGoals = selectedGoals.filter(g => !generalGoals.includes(g));
                                                            newGoals.push(type);
                                                        }
                                                    } else {
                                                        // 재활은 독립적으로 토글
                                                        if (isSelected) {
                                                            newGoals = selectedGoals.filter(g => g !== type);
                                                            setShowRehabOptions(false); // 재활 해제 시 선택지 숨김
                                                        } else {
                                                            newGoals = [...selectedGoals, type];
                                                            setShowRehabOptions(true); // 재활 선택 시 선택지 표시
                                                        }
                                                    }

                                                    // 순서 보장: 일반 목표 우선, 재활 마지막
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
                </div >
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
                <Link to="/exercise-guide?cat=상체" className="action-card">
                    <div className="icon-box" style={{ background: '#eef2ff', color: '#6366f1' }}>
                        <Zap size={24} />
                    </div>
                    <div className="text-box">
                        <h3>상체</h3>
                    </div>
                    <ChevronRight size={16} color="#cbd5e1" style={{ alignSelf: 'flex-end' }} />
                </Link>

                <Link to="/exercise-guide?cat=복근" className="action-card">
                    <div className="icon-box" style={{ background: '#fff1f2', color: '#f43f5e' }}>
                        <Shield size={24} />
                    </div>
                    <div className="text-box">
                        <h3>복근</h3>
                    </div>
                    <ChevronRight size={16} color="#cbd5e1" style={{ alignSelf: 'flex-end' }} />
                </Link>

                <Link to="/exercise-guide?cat=하체" className="action-card">
                    <div className="icon-box" style={{ background: '#f0fdf4', color: '#22c55e' }}>
                        <Activity size={24} />
                    </div>
                    <div className="text-box">
                        <h3>하체</h3>
                    </div>
                    <ChevronRight size={16} color="#cbd5e1" style={{ alignSelf: 'flex-end' }} />
                </Link>
            </div>

            <div style={{ height: '100px' }}></div> {/* Spacer for bottom nav */}

            <style>{`
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
        </div >
    );
};

export default Dashboard;
