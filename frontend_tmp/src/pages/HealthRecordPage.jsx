import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { healthService } from '../services/healthService';
import Layout from '../components/Layout';
import './HealthRecordPage.css';

const HealthRecordPage = () => {
    const navigate = useNavigate();
    const { user } = useAuth();
    const [records, setRecords] = useState([]);
    const [selectedRecord, setSelectedRecord] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadRecords();
    }, []);

    const loadRecords = async () => {
        try {
            const data = await healthService.getUserHealthRecords(user.id, 20);
            setRecords(data);
        } catch (err) {
            console.error('건강 기록 로드 실패:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleRecordClick = (record) => {
        setSelectedRecord(record);
    };

    const handleAnalyzeClick = (recordId) => {
        navigate(`/analysis?recordId=${recordId}`);
    };

    return (
        <Layout>
            <div className="health-record-page">
                <div className="page-header">
                    <h1>건강 기록</h1>
                    <button onClick={() => navigate('/ocr')} className="add-btn">
                        + 새 기록 추가
                    </button>
                </div>

                {loading ? (
                    <div className="loading">로딩 중...</div>
                ) : records.length === 0 ? (
                    <div className="empty-state">
                        <p>아직 등록된 건강 기록이 없습니다</p>
                        <button onClick={() => navigate('/ocr')} className="empty-btn">
                            첫 기록 추가하기
                        </button>
                    </div>
                ) : (
                    <div className="records-layout">
                        <div className="records-list">
                            <h2>기록 목록</h2>
                            {records.map((record) => (
                                <div
                                    key={record.id}
                                    className={`record-item ${selectedRecord?.id === record.id ? 'active' : ''}`}
                                    onClick={() => handleRecordClick(record)}
                                >
                                    <div className="record-date">
                                        {new Date(record.measured_at).toLocaleDateString('ko-KR')}
                                    </div>
                                    <div className="record-info">
                                        <span>체중: {record.measurements?.['체중관리']?.['체중'] || 'N/A'} kg</span>
                                        <div className="badges">
                                            {record.body_type1 && (
                                                <span className="body-type-badge main">{record.body_type1}</span>
                                            )}
                                            {record.body_type2 && (
                                                <span className="body-type-badge sub">{record.body_type2}</span>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>

                        <div className="record-detail">
                            {selectedRecord ? (
                                <>
                                    <div className="detail-header">
                                        <h2>상세 정보</h2>
                                        <button
                                            onClick={() => handleAnalyzeClick(selectedRecord.id)}
                                            className="analyze-btn"
                                        >
                                            AI 분석 요청
                                        </button>
                                    </div>

                                    <div className="detail-content">
                                        <div className="info-section">
                                            <h3>측정 날짜</h3>
                                            <p>{new Date(selectedRecord.measured_at).toLocaleDateString('ko-KR')}</p>
                                        </div>

                                        <div className="info-section">
                                            <h3>체형 분류</h3>
                                            <div className="badges-large">
                                                {selectedRecord.body_type1 ? (
                                                    <span className="body-type-badge main large">{selectedRecord.body_type1}</span>
                                                ) : (
                                                    <span className="no-data">분류되지 않음</span>
                                                )}
                                                {selectedRecord.body_type2 && (
                                                    <span className="body-type-badge sub large">{selectedRecord.body_type2}</span>
                                                )}
                                            </div>
                                        </div>

                                        <div className="measurements-grid">
                                            <div className="measurement-item">
                                                <span className="label">체중</span>
                                                <span className="value">{selectedRecord.measurements?.['체중관리']?.['체중'] || 'N/A'} kg</span>
                                            </div>
                                            <div className="measurement-item">
                                                <span className="label">골격근량</span>
                                                <span className="value">{selectedRecord.measurements?.['체중관리']?.['골격근량'] || 'N/A'} kg</span>
                                            </div>
                                            <div className="measurement-item">
                                                <span className="label">체지방률</span>
                                                <span className="value">{selectedRecord.measurements?.['비만분석']?.['체지방률'] || 'N/A'} %</span>
                                            </div>
                                            <div className="measurement-item">
                                                <span className="label">BMI</span>
                                                <span className="value">{selectedRecord.measurements?.['비만분석']?.['BMI'] || 'N/A'}</span>
                                            </div>
                                            <div className="measurement-item">
                                                <span className="label">체지방량</span>
                                                <span className="value">{selectedRecord.measurements?.['체중관리']?.['체지방량'] || 'N/A'} kg</span>
                                            </div>
                                            <div className="measurement-item">
                                                <span className="label">제지방량</span>
                                                <span className="value">{selectedRecord.measurements?.['연구항목']?.['제지방량'] || 'N/A'} kg</span>
                                            </div>
                                        </div>
                                    </div>
                                </>
                            ) : (
                                <div className="no-selection">
                                    <p>기록을 선택하여 상세 정보를 확인하세요</p>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </Layout>
    );
};

export default HealthRecordPage;
