import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { healthService } from '../services/healthService';
import { goalService } from '../services/goalService';
import Layout from '../components/Layout';
import './MainPage.css';

const MainPage = () => {
    const { user } = useAuth();
    const [latestRecord, setLatestRecord] = useState(null);
    const [loading, setLoading] = useState(true);

    // 목표 관련 상태
    const [activeGoal, setActiveGoal] = useState(null);
    const [goalLoading, setGoalLoading] = useState(true);
    const [isEditingGoal, setIsEditingGoal] = useState(false);
    const [isCreatingGoal, setIsCreatingGoal] = useState(false);
    const [goalForm, setGoalForm] = useState({
        goal_type: '',
        goal_description: ''
    });

    useEffect(() => {
        loadLatestRecord();
        loadActiveGoal();
    }, []);

    const loadLatestRecord = async () => {
        try {
            const record = await healthService.getLatestHealthRecord(user.id);
            setLatestRecord(record);
        } catch (error) {
            console.error('최신 기록 로드 실패:', error);
        } finally {
            setLoading(false);
        }
    };

    const loadActiveGoal = async () => {
        try {
            const goals = await goalService.getActiveGoals(user.id);
            if (goals && goals.length > 0) {
                setActiveGoal(goals[0]); // 가장 최근 활성 목표
            }
        } catch (error) {
            console.error('목표 로드 실패:', error);
        } finally {
            setGoalLoading(false);
        }
    };

    const handleCreateGoal = async (e) => {
        e.preventDefault();
        if (!goalForm.goal_type && !goalForm.goal_description) return;

        try {
            const newGoal = await goalService.createGoal(user.id, goalForm);
            setActiveGoal(newGoal);
            setIsCreatingGoal(false);
            setGoalForm({ goal_type: '', goal_description: '' });
        } catch (error) {
            console.error('목표 생성 실패:', error);
            alert('목표 생성에 실패했습니다.');
        }
    };

    const handleUpdateGoal = async (e) => {
        e.preventDefault();
        if (!activeGoal) return;

        try {
            const updatedGoal = await goalService.updateGoal(activeGoal.id, goalForm);
            setActiveGoal(updatedGoal);
            setIsEditingGoal(false);
        } catch (error) {
            console.error('목표 수정 실패:', error);
            alert('목표 수정에 실패했습니다.');
        }
    };

    const handleCompleteGoal = async () => {
        if (!activeGoal) return;

        if (window.confirm('이 목표를 완료 처리하시겠습니까?')) {
            try {
                await goalService.completeGoal(activeGoal.id);
                setActiveGoal(null);
                loadActiveGoal();
            } catch (error) {
                console.error('목표 완료 실패:', error);
                alert('목표 완료 처리에 실패했습니다.');
            }
        }
    };

    const startEditing = () => {
        setGoalForm({
            goal_type: activeGoal?.goal_type || '',
            goal_description: activeGoal?.goal_description || ''
        });
        setIsEditingGoal(true);
    };

    const cancelEditing = () => {
        setIsEditingGoal(false);
        setIsCreatingGoal(false);
        setGoalForm({ goal_type: '', goal_description: '' });
    };

    const startCreating = () => {
        setGoalForm({ goal_type: '', goal_description: '' });
        setIsCreatingGoal(true);
    };

    return (
        <Layout>
            <div className="main-page">
                <div className="welcome-section">
                    <h1>안녕하세요, {user?.username || '사용자'}님!</h1>
                    <p>오늘도 건강한 하루 보내세요</p>
                </div>

                <div className="dashboard-grid">
                    {/* 목표 카드 */}
                    <div className="card goal-card">
                        <div className="card-header">
                            <h2>나의 목표</h2>
                            {activeGoal && !isEditingGoal && (
                                <div className="goal-actions">
                                    <button onClick={startEditing} className="edit-btn">수정</button>
                                    <button onClick={handleCompleteGoal} className="complete-btn">완료</button>
                                </div>
                            )}
                        </div>

                        {goalLoading ? (
                            <p>로딩 중...</p>
                        ) : isCreatingGoal || isEditingGoal ? (
                            <form onSubmit={isEditingGoal ? handleUpdateGoal : handleCreateGoal} className="goal-form">
                                <div className="form-group">
                                    <label>목표 유형</label>
                                    <select
                                        value={goalForm.goal_type}
                                        onChange={(e) => setGoalForm({ ...goalForm, goal_type: e.target.value })}
                                        className="goal-select"
                                    >
                                        <option value="">선택하세요</option>
                                        <option value="다이어트">다이어트</option>
                                        <option value="근육 증가">근육 증가</option>
                                        <option value="체력 향상">체력 향상</option>
                                        <option value="체형 교정">체형 교정</option>
                                        <option value="건강 유지">건강 유지</option>
                                        <option value="기타">기타</option>
                                    </select>
                                </div>
                                <div className="form-group">
                                    <label>상세 목표</label>
                                    <textarea
                                        value={goalForm.goal_description}
                                        onChange={(e) => setGoalForm({ ...goalForm, goal_description: e.target.value })}
                                        placeholder="예: 3개월 내 5kg 감량, 주 3회 운동하기..."
                                        className="goal-textarea"
                                        rows={3}
                                    />
                                </div>
                                <div className="form-actions">
                                    <button type="submit" className="submit-btn">
                                        {isEditingGoal ? '수정 완료' : '목표 설정'}
                                    </button>
                                    <button type="button" onClick={cancelEditing} className="cancel-btn">
                                        취소
                                    </button>
                                </div>
                            </form>
                        ) : activeGoal ? (
                            <div className="goal-display">
                                <div className="goal-type-badge">
                                    {activeGoal.goal_type || '목표'}
                                </div>
                                <p className="goal-description">
                                    {activeGoal.goal_description || '상세 목표가 없습니다.'}
                                </p>
                                <div className="goal-meta">
                                    <span>시작일: {new Date(activeGoal.started_at).toLocaleDateString('ko-KR')}</span>
                                </div>
                            </div>
                        ) : (
                            <div className="empty-state">
                                <p>설정된 목표가 없습니다</p>
                                <button onClick={startCreating} className="link-btn">
                                    목표 설정하기
                                </button>
                            </div>
                        )}
                    </div>

                    {/* 최신 인바디 기록 카드 */}
                    <div className="card latest-record-card">
                        <h2>최신 인바디 기록</h2>
                        {loading ? (
                            <p>로딩 중...</p>
                        ) : latestRecord ? (
                            <div className="record-summary">
                                <div className="record-item">
                                    <span className="label">측정일:</span>
                                    <span className="value">
                                        {new Date(latestRecord.measured_at).toLocaleDateString('ko-KR')}
                                    </span>
                                </div>
                                <div className="record-item">
                                    <span className="label">체중:</span>
                                    <span className="value">{latestRecord.measurements?.['체중관리']?.['체중'] || 'N/A'} kg</span>
                                </div>
                                <div className="record-item">
                                    <span className="label">체지방률:</span>
                                    <span className="value">{latestRecord.measurements?.['비만분석']?.['체지방률'] || 'N/A'} %</span>
                                </div>
                                {(latestRecord.body_type1 || latestRecord.body_type2) && (
                                    <div className="record-item">
                                        <span className="label">체형 분류:</span>
                                        <div className="body-type-badges">
                                            {latestRecord.body_type1 && (
                                                <span className="value badge main">{latestRecord.body_type1}</span>
                                            )}
                                            {latestRecord.body_type2 && (
                                                <span className="value badge sub">{latestRecord.body_type2}</span>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="empty-state">
                                <p>아직 등록된 인바디 기록이 없습니다</p>
                                <Link to="/ocr" className="link-btn">첫 기록 추가하기</Link>
                            </div>
                        )}
                    </div>

                    {/* 빠른 실행 카드 */}
                    <div className="card quick-actions-card">
                        <h2>빠른 실행</h2>
                        <div className="action-buttons">
                            <Link to="/ocr" className="action-btn">
                                <span className="icon">📸</span>
                                <span className="text">인바디 사진 업로드</span>
                            </Link>
                            <Link to="/health-records" className="action-btn">
                                <span className="icon">📊</span>
                                <span className="text">건강 기록 보기</span>
                            </Link>
                            <Link to="/analysis" className="action-btn">
                                <span className="icon">🤖</span>
                                <span className="text">AI 건강 분석</span>
                            </Link>
                            <Link to="/weekly-plan" className="action-btn highlight">
                                <span className="icon">📅</span>
                                <span className="text">주간 계획서 생성</span>
                            </Link>
                        </div>
                    </div>
                </div>
            </div>
        </Layout>
    );
};

export default MainPage;
