import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { useAuth } from '../context/AuthContext';
import { healthService } from '../services/healthService';
import { goalService } from '../services/goalService';
import { weeklyPlanService } from '../services/weeklyPlanService';
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

    // 챗봇 관련
    const [currentPlan, setCurrentPlan] = useState(null); // { id, thread_id }
    const [messages, setMessages] = useState([]); // [{ role: 'user'|'ai', content: string }]
    const [inputMessage, setInputMessage] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const messagesEndRef = useRef(null);

    useEffect(() => {
        loadRecords();
        loadActiveGoal();
    }, []);

    useEffect(() => {
        // 메시지가 추가될 때마다 스크롤을 맨 아래로
        scrollToBottom();
    }, [messages]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

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

    const handleGeneratePlan = async () => {
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
            console.log('주간 계획 생성 시작...');
            const plan = await weeklyPlanService.generateWeeklyPlan(user.id, {
                record_id: parseInt(selectedRecordId),
                user_goal_type: goalType || null,
                user_goal_description: goalDescription || null
            });

            console.log('주간 계획 생성 성공:', plan);

            // 생성된 계획의 thread_id 생성 (타임스탬프 기반)
            const threadId = `plan_${plan.id}_${Date.now()}`;

            setCurrentPlan({
                id: plan.id,
                thread_id: threadId
            });

            // AI 메시지 추가
            const aiContent = plan.plan_data?.content || '주간 계획이 생성되었습니다.';
            setMessages([
                { role: 'ai', content: aiContent }
            ]);

        } catch (err) {
            console.error('주간 계획 생성 실패:', err);

            let errorMessage = '주간 계획 생성 중 오류가 발생했습니다.';

            if (err.response) {
                console.error('서버 응답 에러:', err.response.data);
                if (err.response.status === 404) {
                    errorMessage = '건강 기록을 찾을 수 없습니다.';
                } else if (err.response.status === 500) {
                    errorMessage = 'LLM 주간 계획 생성 중 서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.';
                } else if (err.response.data?.detail) {
                    errorMessage = err.response.data.detail;
                }
            } else if (err.request) {
                console.error('서버 응답 없음');
                errorMessage = '서버에 연결할 수 없습니다. 네트워크 연결을 확인해주세요.';
            }

            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    const handleSendMessage = async () => {
        if (!inputMessage.trim() || !currentPlan) {
            return;
        }

        const userMessage = inputMessage.trim();
        setInputMessage('');
        setLoading(true);
        setError('');

        // 사용자 메시지 추가
        setMessages(prev => [...prev, { role: 'user', content: userMessage }]);

        try {
            console.log('AI에게 메시지 전송:', userMessage);
            const response = await weeklyPlanService.chatWithPlan(
                currentPlan.id,
                currentPlan.thread_id,
                userMessage
            );

            console.log('AI 응답 수신:', response);

            // AI 응답 추가
            setMessages(prev => [...prev, { role: 'ai', content: response.response }]);

        } catch (err) {
            console.error('메시지 전송 실패:', err);

            let errorMessage = '메시지 전송 중 오류가 발생했습니다.';

            if (err.response) {
                console.error('서버 응답 에러:', err.response.data);

                if (err.response.status === 404) {
                    errorMessage = '주간 계획을 찾을 수 없습니다.';
                } else if (err.response.status === 500) {
                    errorMessage = 'AI 응답 생성 중 서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.';
                } else if (err.response.data?.detail) {
                    errorMessage = err.response.data.detail;
                }
            } else if (err.request) {
                errorMessage = '서버에 연결할 수 없습니다. 네트워크 연결을 확인해주세요.';
            }

            setError(errorMessage);
            // 에러 발생 시 사용자 메시지 제거
            setMessages(prev => prev.slice(0, -1));
        } finally {
            setLoading(false);
        }
    };


    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    return (
        <Layout>
            <div className="weekly-plan-page">
                <h1>AI 주간 계획서 생성</h1>
                <p className="subtitle">
                    목표와 인바디 데이터를 기반으로 맞춤형 주간 운동/식단 계획을 생성하고 대화를 통해 수정할 수 있습니다
                </p>

                <div className="plan-layout">
                    {/* 좌측: 설정 패널 */}
                    <div className="plan-controls">
                        {/* 건강 기록 선택 */}
                        <div className="control-card">
                            <h2>1. 건강 기록 선택</h2>
                            <select
                                value={selectedRecordId}
                                onChange={(e) => setSelectedRecordId(e.target.value)}
                                className="record-select"
                                disabled={currentPlan !== null}
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
                                        disabled={currentPlan !== null}
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
                                            disabled={currentPlan !== null}
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
                                            disabled={currentPlan !== null}
                                        />
                                    </div>
                                </div>
                            )}
                        </div>

                        {error && <div className="error-message">{error}</div>}

                        {!currentPlan && (
                            <button
                                onClick={handleGeneratePlan}
                                disabled={loading}
                                className="generate-btn"
                            >
                                {loading ? 'AI 주간 계획 생성 중...' : '주간 계획 생성'}
                            </button>
                        )}

                        {currentPlan && (
                            <button
                                onClick={() => {
                                    setCurrentPlan(null);
                                    setMessages([]);
                                    setInputMessage('');
                                }}
                                className="new-plan-btn"
                            >
                                새로운 계획 생성
                            </button>
                        )}
                    </div>

                    {/* 우측: 챗봇 인터페이스 */}
                    <div className="plan-result">
                        {messages.length > 0 ? (
                            <div className="chat-container">
                                <div className="chat-header">
                                    <h2>AI 트레이너와 대화</h2>
                                    <span className="plan-id">계획 #{currentPlan?.id}</span>
                                </div>

                                <div className="chat-messages">
                                    {messages.map((msg, idx) => (
                                        <div key={idx} className={`message ${msg.role}`}>
                                            <div className="message-content">
                                                {msg.role === 'ai' ? (
                                                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                                                ) : (
                                                    <p>{msg.content}</p>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                    {loading && (
                                        <div className="message ai">
                                            <div className="message-content loading">
                                                <span className="typing-indicator">
                                                    <span></span>
                                                    <span></span>
                                                    <span></span>
                                                </span>
                                            </div>
                                        </div>
                                    )}
                                    <div ref={messagesEndRef} />
                                </div>

                                <div className="chat-input-area">
                                    <textarea
                                        value={inputMessage}
                                        onChange={(e) => setInputMessage(e.target.value)}
                                        onKeyPress={handleKeyPress}
                                        placeholder="운동 강도를 조정하거나 식단을 변경하고 싶으신가요? 질문해주세요..."
                                        className="chat-input"
                                        rows={2}
                                        disabled={loading}
                                    />
                                    <button
                                        onClick={handleSendMessage}
                                        disabled={loading || !inputMessage.trim()}
                                        className="send-btn"
                                    >
                                        전송
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <div className="no-result">
                                <span className="icon">💪</span>
                                <h3>AI 주간 계획서 생성</h3>
                                <p>
                                    건강 기록과 목표를 선택한 후<br />
                                    주간 계획을 생성하세요
                                </p>
                                <div className="features">
                                    <div className="feature">
                                        <span>✓</span> 맞춤형 운동 계획
                                    </div>
                                    <div className="feature">
                                        <span>✓</span> 맞춤형 식단 추천
                                    </div>
                                    <div className="feature">
                                        <span>✓</span> AI와 실시간 대화
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </Layout>
    );
};

export default WeeklyPlanPage;
