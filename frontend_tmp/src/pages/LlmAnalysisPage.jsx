import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { healthService } from '../services/healthService';
import { analysisService } from '../services/analysisService';
import Layout from '../components/Layout';
import './LlmAnalysisPage.css';

const LlmAnalysisPage = () => {
    const [searchParams] = useSearchParams();
    const { user } = useAuth();
    const [records, setRecords] = useState([]);
    const [selectedRecordId, setSelectedRecordId] = useState(searchParams.get('recordId') || '');
    const [llmInput, setLlmInput] = useState(null);
    const [pastReports, setPastReports] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        if (user) {
            loadRecords();
            loadPastReports();
        }
    }, [user]);

    useEffect(() => {
        if (selectedRecordId) {
            // 기존 분석 결과가 있는지 확인
            loadExistingAnalysis(selectedRecordId);
        }
    }, [selectedRecordId]);

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
                // 기존 분석이 있으면 표시
                setLlmInput({
                    type: 'existing',
                    data: report
                });
            }
        } catch (error) {
            // 분석이 없으면 무시
            setLlmInput(null);
        }
    };

    const handlePrepareAnalysis = async () => {
        if (!selectedRecordId) {
            setError('건강 기록을 선택해주세요.');
            return;
        }

        setLoading(true);
        setError('');

        try {
            const response = await analysisService.prepareStatusAnalysis(user.id, selectedRecordId);
            setLlmInput({
                type: 'prepared',
                data: response
            });
        } catch (err) {
            setError(err.response?.data?.detail || 'LLM 데이터 준비 중 오류가 발생했습니다.');
        } finally {
            setLoading(false);
        }
    };

    const formatMeasurements = (measurements) => {
        if (!measurements) return null;

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

    const renderPreparedInput = () => {
        const inputData = llmInput?.data?.input_data;
        if (!inputData) return null;

        return (
            <div className="result-card">
                <div className="result-header">
                    <h2>LLM Input 데이터 (status_analysis)</h2>
                    <span className="result-badge prepared">준비 완료</span>
                </div>

                <div className="result-content">
                    {/* 기본 정보 */}
                    <div className="result-section">
                        <h3>기본 정보</h3>
                        <div className="info-grid">
                            <div className="info-item">
                                <span className="label">기록 ID:</span>
                                <span className="value">{inputData.record_id}</span>
                            </div>
                            <div className="info-item">
                                <span className="label">측정일:</span>
                                <span className="value">
                                    {inputData.measured_at
                                        ? new Date(inputData.measured_at).toLocaleDateString('ko-KR')
                                        : 'N/A'}
                                </span>
                            </div>
                            <div className="info-item">
                                <span className="label">체형 분류 (Stage2):</span>
                                <span className="value badge-inline">
                                    {inputData.body_type1 || 'N/A'}
                                </span>
                            </div>
                            <div className="info-item">
                                <span className="label">체형 분류 (Stage3):</span>
                                <span className="value badge-inline">
                                    {inputData.body_type2 || 'N/A'}
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* 인바디 측정 데이터 */}
                    <div className="result-section">
                        <h3>인바디 측정 데이터</h3>
                        <div className="measurements-container">
                            {formatMeasurements(inputData.measurements)}
                        </div>
                    </div>
                </div>

                <div className="result-footer">
                    <p className="message">{llmInput.data.message}</p>
                    <p className="helper">* 팀원이 LLM API 연동 완료 후, 이 데이터가 자동으로 LLM에 전달됩니다.</p>
                </div>
            </div>
        );
    };

    const renderExistingAnalysis = () => {
        const report = llmInput?.data;
        if (!report) return null;

        return (
            <div className="result-card">
                <div className="result-header">
                    <h2>분석 결과</h2>
                    <span className="result-date">
                        {new Date(report.created_at).toLocaleDateString('ko-KR')}
                    </span>
                </div>

                <div className="result-content">
                    <div className="result-section">
                        <h3>종합 요약</h3>
                        <p className="summary-text">{report.summary || 'N/A'}</p>
                    </div>

                    <div className="result-section">
                        <h3>상세 분석</h3>
                        <div className="analysis-text">
                            {report.analysis_text || 'N/A'}
                        </div>
                    </div>

                    {report.recommendations && (
                        <div className="result-section">
                            <h3>추천 사항</h3>
                            <div className="recommendations">
                                {report.recommendations}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        );
    };

    return (
        <Layout>
            <div className="analysis-page">
                <h1>AI 건강 분석</h1>
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
                                onClick={handlePrepareAnalysis}
                                disabled={!selectedRecordId || loading}
                                className="analyze-btn"
                            >
                                {loading ? 'LLM 데이터 준비 중...' : 'LLM Input 데이터 생성'}
                            </button>

                            <p className="helper-text">
                                * LLM API 연동 전 단계입니다
                            </p>
                        </div>

                        <div className="control-card past-reports">
                            <h2>과거 분석 리포트</h2>
                            {pastReports.length === 0 ? (
                                <p className="empty-text">아직 분석 리포트가 없습니다</p>
                            ) : (
                                <div className="report-list">
                                    {pastReports.map((report) => (
                                        <div
                                            key={report.report_id || report.id}
                                            className="report-item"
                                            onClick={() => setLlmInput({ type: 'existing', data: report })}
                                        >
                                            <div className="report-date">
                                                {new Date(report.created_at || report.generated_at).toLocaleDateString('ko-KR')}
                                            </div>
                                            <div className="report-preview">
                                                {report.summary?.substring(0, 50) || report.llm_output?.substring(0, 50) || 'AI 분석 결과'}...
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="analysis-result">
                        {llmInput ? (
                            llmInput.type === 'prepared' ? renderPreparedInput() : renderExistingAnalysis()
                        ) : (
                            <div className="no-result">
                                <span className="icon">🤖</span>
                                <p>건강 기록을 선택하고 AI 분석 데이터를 준비하세요</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </Layout>
    );
};

export default LlmAnalysisPage;
