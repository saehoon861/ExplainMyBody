import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { healthService } from '../services/healthService';
import { analysisService } from '../services/analysisService';
import Layout from '../components/Layout';
import LoadingAnimation from '../components/LoadingAnimation';
import './LlmAnalysisPage.css';

const LlmAnalysisPage = () => {
    const [searchParams] = useSearchParams();
    const { user } = useAuth();
    const [records, setRecords] = useState([]);
    const [selectedRecordId, setSelectedRecordId] = useState(searchParams.get('recordId') || '');
    const [analysisResult, setAnalysisResult] = useState(null);
    const [pastReports, setPastReports] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    // Chat state
    const [chatMessages, setChatMessages] = useState([]);
    const [chatInput, setChatInput] = useState('');
    const [chatLoading, setChatLoading] = useState(false);
    const chatEndRef = useRef(null);

    useEffect(() => {
        if (user) {
            loadRecords();
            loadPastReports();
        }
    }, [user]);

    useEffect(() => {
        if (selectedRecordId) {
            loadExistingAnalysis(selectedRecordId);
        }
    }, [selectedRecordId]);

    useEffect(() => {
        // Auto-scroll to bottom when new messages arrive
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [chatMessages]);

    const loadRecords = async () => {
        try {
            const data = await healthService.getUserHealthRecords(user.id, 20);
            setRecords(data);
        } catch (error) {
            console.error('건강 기록 로드 실패:', error);
        }
    };

    const loadPastReports = async () => {
        try {
            const reports = await analysisService.getUserAnalysisReports(user.id, 10);
            setPastReports(reports);
        } catch (error) {
            console.error('과거 리포트 로드 실패:', error);
        }
    };

    const loadExistingAnalysis = async (recordId) => {
        try {
            const report = await analysisService.getAnalysisByRecord(recordId);
            if (report) {
                setAnalysisResult(report);
                setChatMessages([]);
            }
        } catch (error) {
            setAnalysisResult(null);
            setChatMessages([]);
        }
    };

    const handleAnalyzeWithLLM = async () => {
        if (!selectedRecordId) {
            setError('건강 기록을 선택해주세요.');
            return;
        }

        setLoading(true);
        setError('');
        setChatMessages([]);

        try {
            const result = await analysisService.analyzeWithLLM(user.id, selectedRecordId);
            setAnalysisResult(result);
            await loadPastReports(); // Refresh past reports
        } catch (err) {
            setError(err.response?.data?.detail || 'AI 분석 중 오류가 발생했습니다.');
        } finally {
            setLoading(false);
        }
    };

    const handleSendMessage = async () => {
        if (!chatInput.trim() || !analysisResult) return;

        const userMessage = chatInput.trim();
        setChatInput('');
        setChatLoading(true);

        // Add user message to chat
        setChatMessages(prev => [...prev, { role: 'user', content: userMessage }]);

        try {
            const response = await analysisService.chatWithAnalysis(
                analysisResult.id,
                userMessage,
                analysisResult.thread_id
            );

            // Add AI response to chat
            setChatMessages(prev => [...prev, { role: 'assistant', content: response.response }]);
        } catch (err) {
            setError('AI와 대화 중 오류가 발생했습니다.');
            console.error('Chat error:', err);
        } finally {
            setChatLoading(false);
        }
    };

    const renderAnalysisResult = () => {
        if (!analysisResult) return null;

        return (
            <div className="result-card">
                <div className="result-header">
                    <h2>🤖 AI 분석 결과</h2>
                    <span className="result-date">
                        {new Date(analysisResult.generated_at).toLocaleDateString('ko-KR', {
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                        })}
                    </span>
                </div>

                <div className="result-content">
                    <div className="result-section">
                        <h3>종합 분석</h3>
                        <div className="analysis-text">
                            {analysisResult.llm_output}
                        </div>
                    </div>

                    {analysisResult.thread_id && (
                        <div className="result-section">
                            <h3>💬 AI와 대화하기</h3>
                            <p className="helper-text" style={{ marginBottom: '1rem', textAlign: 'left' }}>
                                분석 결과에 대해 궁금한 점을 물어보세요!
                            </p>

                            {/* Chat messages */}
                            <div className="chat-container">
                                {chatMessages.map((msg, idx) => (
                                    <div key={idx} className={`chat-message ${msg.role}`}>
                                        <div className="message-avatar">
                                            {msg.role === 'user' ? '👤' : '🤖'}
                                        </div>
                                        <div className="message-content">
                                            {msg.content}
                                        </div>
                                    </div>
                                ))}
                                {chatLoading && (
                                    <div className="chat-message assistant">
                                        <div className="message-avatar">🤖</div>
                                        <div className="message-content">
                                            <div className="typing-indicator">
                                                <span></span>
                                                <span></span>
                                                <span></span>
                                            </div>
                                        </div>
                                    </div>
                                )}
                                <div ref={chatEndRef} />
                            </div>

                            {/* Chat input */}
                            <div className="chat-input-container">
                                <input
                                    type="text"
                                    value={chatInput}
                                    onChange={(e) => setChatInput(e.target.value)}
                                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                                    placeholder="질문을 입력하세요..."
                                    className="chat-input"
                                    disabled={chatLoading}
                                />
                                <button
                                    onClick={handleSendMessage}
                                    disabled={!chatInput.trim() || chatLoading}
                                    className="chat-send-btn"
                                >
                                    전송
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        );
    };

    return (
        <Layout>
            {loading && <LoadingAnimation type="analysis" />}
            <div className="analysis-page">
                <h1>🧬 AI 건강 분석</h1>
                <p className="subtitle">인바디 데이터를 기반으로 AI가 종합적인 건강 상태를 분석합니다</p>

                <div className="analysis-layout">
                    <div className="analysis-controls">
                        <div className="control-card">
                            <h2>건강 기록 선택</h2>
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

                            {error && <div className="error-message">{error}</div>}

                            <button
                                onClick={handleAnalyzeWithLLM}
                                disabled={!selectedRecordId || loading}
                                className="analyze-btn"
                            >
                                {loading ? (
                                    <>
                                        <span className="spinner"></span>
                                        AI 분석 중...
                                    </>
                                ) : (
                                    '🚀 AI 분석 실행'
                                )}
                            </button>

                            <p className="helper-text">
                                * LLM이 건강 기록을 분석합니다
                            </p>
                        </div>

                        <div className="control-card past-reports">
                            <h2>📋 과거 분석 리포트</h2>
                            {pastReports.length === 0 ? (
                                <p className="empty-text">아직 분석 리포트가 없습니다</p>
                            ) : (
                                <div className="report-list">
                                    {pastReports.map((report) => (
                                        <div
                                            key={report.id}
                                            className={`report-item ${analysisResult?.id === report.id ? 'active' : ''}`}
                                            onClick={() => {
                                                setAnalysisResult(report);
                                                setChatMessages([]);
                                            }}
                                        >
                                            <div className="report-date">
                                                {new Date(report.generated_at).toLocaleDateString('ko-KR')}
                                            </div>
                                            <div className="report-preview">
                                                {report.llm_output?.substring(0, 60) || 'AI 분석 결과'}...
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="analysis-result">
                        {analysisResult ? renderAnalysisResult() : (
                            <div className="no-result">
                                <span className="icon">🤖</span>
                                <p>건강 기록을 선택하고 AI 분석을 실행하세요</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </Layout>
    );
};

export default LlmAnalysisPage;

