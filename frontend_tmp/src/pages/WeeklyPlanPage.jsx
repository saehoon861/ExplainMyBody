import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { healthService } from '../services/healthService';
import { goalService } from '../services/goalService';
import Layout from '../components/Layout';
import './WeeklyPlanPage.css';

const WeeklyPlanPage = () => {
    const { user } = useAuth();

    // 건강 기록 관련
    const [records, setRecords] = useState([]);
    const [selectedRecordId, setSelectedRecordId] = useState('');

    // 목표 관련
    const [activeGoal, setActiveGoal] = useState(null);
    const [customGoalType, setCustomGoalType] = useState('');
    const [customGoalDescription, setCustomGoalDescription] = useState('');
    const [useCustomGoal, setUseCustomGoal] = useState(false);

    // LLM 결과
    const [llmInput, setLlmInput] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        loadRecords();
        loadActiveGoal();
    }, []);

    const loadRecords = async () => {
        try {
            const data = await healthService.getUserHealthRecords(user.id, 20);
            setRecords(data);
            // 가장 최신 기록 자동 선택
            if (data.length > 0) {
                setSelectedRecordId(data[0].id.toString());
            }
        } catch (error) {
            console.error('건강 기록 로드 실패:', error);
        }
    };

    const loadActiveGoal = async () => {
        try {
            const goals = await goalService.getActiveGoals(user.id);
            if (goals && goals.length > 0) {
                setActiveGoal(goals[0]);
            }
        } catch (error) {
            console.error('목표 로드 실패:', error);
        }
    };

    const handlePrepareInput = async () => {
        if (!selectedRecordId) {
            setError('건강 기록을 선택해주세요.');
            return;
        }

        const goalType = useCustomGoal ? customGoalType : activeGoal?.goal_type;
        const goalDescription = useCustomGoal ? customGoalDescription : activeGoal?.goal_description;

        if (!goalType && !goalDescription) {
            setError('목표를 설정해주세요. 대시보드에서 목표를 설정하거나 아래에서 직접 입력하세요.');
            return;
        }

        setLoading(true);
        setError('');

        try {
            const response = await goalService.prepareGoalPlan(user.id, {
                record_id: parseInt(selectedRecordId),
                user_goal_type: goalType || null,
                user_goal_description: goalDescription || null
            });

            setLlmInput(response);
        } catch (err) {
            setError(err.response?.data?.detail || 'LLM 데이터 준비 중 오류가 발생했습니다.');
        } finally {
            setLoading(false);
        }
    };

    const formatMeasurements = (measurements) => {
        if (!measurements) return 'N/A';

        return Object.entries(measurements).map(([category, values]) => (
            <div key={category} className="measurement-category">
                <h4>{category}</h4>
                <div className="measurement-items">
                    {typeof values === 'object' ? (
                        Object.entries(values).map(([key, value]) => (
                            <div key={key} className="measurement-item">
                                <span className="key">{key}:</span>
                                <span className="value">{value}</span>
                            </div>
                        ))
                    ) : (
                        <span>{values}</span>
                    )}
                </div>
            </div>
        ));
    };

    return (
        <Layout>
            <div className="weekly-plan-page">
                <h1>AI 주간 계획서 생성</h1>
                <p className="subtitle">
                    목표와 인바디 데이터를 기반으로 맞춤형 주간 운동/식단 계획을 생성합니다
                </p>

                <div className="plan-layout">
                    <div className="plan-controls">
                        {/* 건강 기록 선택 */}
                        <div className="control-card">
                            <h2>1. 건강 기록 선택</h2>
                            <select
                                value={selectedRecordId}
                                onChange={(e) => setSelectedRecordId(e.target.value)}
                                className="record-select"
                            >
                                <option value="">-- 기록 선택 --</option>
                                {records.map((record) => (
                                    <option key={record.id} value={record.id}>
                                        {new Date(record.measured_at).toLocaleDateString('ko-KR')} -
                                        체중: {record.measurements?.['체중관리']?.['체중'] || 'N/A'} kg
                                        {record.body_type1 && ` (${record.body_type1})`}
                                    </option>
                                ))}
                            </select>
                        </div>

                        {/* 목표 설정 */}
                        <div className="control-card">
                            <h2>2. 목표 설정</h2>

                            {activeGoal && (
                                <div className="active-goal-info">
                                    <div className="goal-badge">현재 활성 목표</div>
                                    <div className="goal-content">
                                        <strong>{activeGoal.goal_type}</strong>
                                        <p>{activeGoal.goal_description}</p>
                                    </div>
                                </div>
                            )}

                            <div className="goal-toggle">
                                <label className="toggle-label">
                                    <input
                                        type="checkbox"
                                        checked={useCustomGoal}
                                        onChange={(e) => setUseCustomGoal(e.target.checked)}
                                    />
                                    <span>다른 목표로 계획서 생성</span>
                                </label>
                            </div>

                            {(useCustomGoal || !activeGoal) && (
                                <div className="custom-goal-form">
                                    <div className="form-group">
                                        <label>목표 유형</label>
                                        <select
                                            value={customGoalType}
                                            onChange={(e) => setCustomGoalType(e.target.value)}
                                            className="goal-select"
                                        >
                                            <option value="">선택하세요</option>
                                            <option value="다이어트">다이어트</option>
                                            <option value="근육 증가">근육 증가</option>
                                            <option value="체력 향상">체력 향상</option>
                                            <option value="체형 교정">체형 교정</option>
                                            <option value="건강 유지">건강 유지</option>
                                        </select>
                                    </div>
                                    <div className="form-group">
                                        <label>상세 목표</label>
                                        <textarea
                                            value={customGoalDescription}
                                            onChange={(e) => setCustomGoalDescription(e.target.value)}
                                            placeholder="예: 3개월 내 5kg 감량하고 싶어요. 주 3회 운동 가능합니다."
                                            className="goal-textarea"
                                            rows={3}
                                        />
                                    </div>
                                </div>
                            )}
                        </div>

                        {error && <div className="error-message">{error}</div>}

                        <button
                            onClick={handlePrepareInput}
                            disabled={loading}
                            className="generate-btn"
                        >
                            {loading ? 'LLM 데이터 준비 중...' : 'LLM Input 데이터 생성'}
                        </button>

                        <p className="helper-text">
                            * 현재 LLM API 연동 전 단계입니다. 아래에서 LLM에 전달될 데이터를 확인할 수 있습니다.
                        </p>
                    </div>

                    {/* LLM Input 결과 표시 */}
                    <div className="plan-result">
                        {llmInput ? (
                            <div className="result-card">
                                <div className="result-header">
                                    <h2>LLM Input 데이터</h2>
                                    <span className="status-badge success">준비 완료</span>
                                </div>

                                <div className="result-content">
                                    {/* 목표 정보 */}
                                    <div className="result-section">
                                        <h3>사용자 목표</h3>
                                        <div className="info-grid">
                                            <div className="info-item">
                                                <span className="label">목표 유형:</span>
                                                <span className="value">
                                                    {llmInput.input_data?.user_goal_type || 'N/A'}
                                                </span>
                                            </div>
                                            <div className="info-item full-width">
                                                <span className="label">상세 목표:</span>
                                                <span className="value">
                                                    {llmInput.input_data?.user_goal_description || 'N/A'}
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    {/* 건강 기록 정보 */}
                                    <div className="result-section">
                                        <h3>건강 기록 정보</h3>
                                        <div className="info-grid">
                                            <div className="info-item">
                                                <span className="label">기록 ID:</span>
                                                <span className="value">{llmInput.input_data?.record_id}</span>
                                            </div>
                                            <div className="info-item">
                                                <span className="label">측정일:</span>
                                                <span className="value">
                                                    {llmInput.input_data?.measured_at
                                                        ? new Date(llmInput.input_data.measured_at).toLocaleDateString('ko-KR')
                                                        : 'N/A'}
                                                </span>
                                            </div>
                                            <div className="info-item">
                                                <span className="label">체형 분류 (Stage2):</span>
                                                <span className="value badge">
                                                    {llmInput.input_data?.body_type1 || 'N/A'}
                                                </span>
                                            </div>
                                            <div className="info-item">
                                                <span className="label">체형 분류 (Stage3):</span>
                                                <span className="value badge">
                                                    {llmInput.input_data?.body_type2 || 'N/A'}
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    {/* 인바디 측정 데이터 */}
                                    <div className="result-section">
                                        <h3>인바디 측정 데이터</h3>
                                        <div className="measurements-container">
                                            {formatMeasurements(llmInput.input_data?.measurements)}
                                        </div>
                                    </div>

                                    {/* 이전 분석 결과 */}
                                    <div className="result-section">
                                        <h3>이전 건강 분석 결과 (LLM1)</h3>
                                        {llmInput.input_data?.status_analysis_result ? (
                                            <div className="analysis-preview">
                                                <div className="analysis-id">
                                                    분석 ID: {llmInput.input_data.status_analysis_id}
                                                </div>
                                                <pre className="analysis-text">
                                                    {llmInput.input_data.status_analysis_result}
                                                </pre>
                                            </div>
                                        ) : (
                                            <p className="empty-text">
                                                아직 이 건강 기록에 대한 AI 분석이 없습니다.
                                                먼저 "AI 건강 분석" 메뉴에서 분석을 진행해주세요.
                                            </p>
                                        )}
                                    </div>
                                </div>

                                <div className="result-footer">
                                    <p className="message">{llmInput.message}</p>
                                </div>
                            </div>
                        ) : (
                            <div className="no-result">
                                <span className="icon">📅</span>
                                <h3>주간 계획서 생성</h3>
                                <p>건강 기록과 목표를 선택한 후<br />LLM Input 데이터를 생성하세요</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </Layout>
    );
};

export default WeeklyPlanPage;
