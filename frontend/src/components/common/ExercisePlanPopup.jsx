import React, { useState, useEffect } from 'react';
import { X, Check, Activity, Heart, AlertCircle, Dumbbell, Target } from 'lucide-react';
import '../../styles/LoginLight.css';
import LoadingAnimation from './LoadingAnimation';

const ExercisePlanPopup = ({ isOpen, onClose, onSubmit, initialData }) => {
    const [step, setStep] = useState(1); // 1: Info, 2: Loading
    const [loadingProgress, setLoadingProgress] = useState(0);

    // Read-only data (default to defaults if missing)
    const { goal, preferences, diseases } = initialData || {
        goal: '다이어트',
        preferences: ['헬스장(웨이트)', '러닝/유산소'],
        diseases: '없음'
    };

    useEffect(() => {
        if (isOpen) {
            setStep(1);
            setLoadingProgress(0);
        }
    }, [isOpen]);

    const handleSubmit = () => {
        setStep(2);

        // 부모 컴포넌트의 onSubmit(API 호출)을 즉시 실행
        onSubmit({ goal, preferences, diseases });

        // 시뮬레이션은 시각적 효과를 위해 유지하되, 실제 제어권은 부모에게 있음
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress >= 100) {
                progress = 100;
                clearInterval(interval);
            }
            setLoadingProgress(progress);
        }, 500);
    };

    if (!isOpen) return null;

    const isLoading = step === 2;

    return (
        <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.5)',
            backdropFilter: 'blur(4px)',
            zIndex: 9999,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px',
            animation: 'fadeIn 0.2s ease-out'
        }}
            onClick={!isLoading ? onClose : undefined}
        >
            <div
                onClick={(e) => e.stopPropagation()}
                style={{
                    background: 'white',
                    borderRadius: '24px',
                    padding: '32px',
                    maxWidth: '500px',
                    width: '100%',
                    position: 'relative',
                    boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
                    animation: 'slideUp 0.3s ease-out'
                }}
            >
                <button
                    onClick={!isLoading ? onClose : undefined}
                    style={{
                        position: 'absolute',
                        top: '16px',
                        right: '16px',
                        background: '#1e293b', // 완전 불투명한 진한 색상 (InBody 팝업과 통일)
                        border: '2px solid white',
                        borderRadius: '50%',
                        width: '36px',
                        height: '36px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        cursor: isLoading ? 'default' : 'pointer',
                        transition: 'all 0.2s',
                        zIndex: 9999,
                        boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                        opacity: isLoading ? 0.5 : 1
                    }}
                    onMouseEnter={(e) => {
                        if (!isLoading) e.currentTarget.style.transform = 'scale(1.1)';
                    }}
                    onMouseLeave={(e) => {
                        if (!isLoading) e.currentTarget.style.transform = 'scale(1)';
                    }}
                >
                    <X size={20} color="white" strokeWidth={3} />
                </button>

                <div style={{ textAlign: 'center', marginBottom: '32px' }}>
                    <div style={{
                        width: '80px',
                        height: '80px',
                        borderRadius: '24px',
                        background: 'linear-gradient(135deg, #fdf2f8 0%, #fce7f3 100%)', // 파스텔 핑크
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        margin: '0 auto 16px',
                        border: '1px solid rgba(255,255,255,0.6)'
                    }}>
                        <Dumbbell color="#db2777" size={32} />
                    </div>
                    <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#1e293b', marginBottom: '8px', wordKeepAll: 'break-word' }}>
                        맞춤 운동 플랜 설계
                    </h2>
                    <p style={{ color: '#64748b', fontSize: '0.95rem', lineHeight: 1.6 }}>
                        저장된 고객 정보를 바탕으로<br />
                        AI가 최적의 운동 루틴을 생성합니다.
                    </p>
                </div>

                {/* 정보 요약 카드 (Read-Only) */}
                <div style={{
                    background: '#f8fafc',
                    borderRadius: '16px',
                    padding: '24px',
                    marginBottom: '32px',
                    border: '1px solid #e2e8f0'
                }}>
                    <div style={{ marginBottom: '20px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                            <Target size={18} color="#f5576c" />
                            <span style={{ fontSize: '0.9rem', fontWeight: 600, color: '#475569' }}>나의 목표</span>
                        </div>
                        <div style={{
                            fontSize: '1.1rem',
                            fontWeight: 700,
                            color: '#1e293b',
                            background: 'white',
                            padding: '12px',
                            borderRadius: '12px',
                            border: '1px solid #e2e8f0',
                            display: 'inline-block'
                        }}>
                            {goal || '설정된 목표 없음'}
                        </div>
                    </div>

                    <div style={{ marginBottom: '20px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                            <Activity size={18} color="#f5576c" />
                            <span style={{ fontSize: '0.9rem', fontWeight: 600, color: '#475569' }}>선호하는 운동</span>
                        </div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                            {preferences && preferences.length > 0 ? preferences.map((pref, idx) => (
                                <span key={idx} style={{
                                    padding: '8px 14px',
                                    borderRadius: '20px',
                                    background: 'white',
                                    border: '1px solid #e2e8f0',
                                    color: '#64748b',
                                    fontSize: '0.9rem',
                                    fontWeight: 500
                                }}>
                                    {pref}
                                </span>
                            )) : (
                                <span style={{ color: '#94a3b8', fontSize: '0.9rem' }}>선택된 운동 없음</span>
                            )}
                        </div>
                    </div>

                    <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                            <AlertCircle size={18} color="#f5576c" />
                            <span style={{ fontSize: '0.9rem', fontWeight: 600, color: '#475569' }}>특이사항</span>
                        </div>
                        <div style={{
                            background: 'white',
                            padding: '12px',
                            borderRadius: '12px',
                            border: '1px solid #e2e8f0',
                            color: diseases ? '#1e293b' : '#94a3b8',
                            fontSize: '0.95rem',
                            minHeight: '48px',
                            display: 'flex',
                            alignItems: 'center'
                        }}>
                            {diseases || '없음'}
                        </div>
                    </div>
                </div>

                {!isLoading ? (
                    <button
                        onClick={handleSubmit}
                        style={{
                            width: '100%',
                            padding: '16px',
                            background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                            color: 'white',
                            border: 'none',
                            borderRadius: '16px',
                            fontSize: '1rem',
                            fontWeight: 700,
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: '10px',
                            transition: 'all 0.3s',
                            boxShadow: '0 4px 16px rgba(245, 87, 108, 0.4)'
                        }}
                        onMouseEnter={(e) => {
                            e.currentTarget.style.transform = 'translateY(-2px)';
                            e.currentTarget.style.boxShadow = '0 8px 24px rgba(245, 87, 108, 0.5)';
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.transform = 'translateY(0)';
                            e.currentTarget.style.boxShadow = '0 4px 16px rgba(245, 87, 108, 0.4)';
                        }}
                    >
                        <Dumbbell size={20} />
                        AI 맞춤 운동 플랜 생성하기
                    </button>
                ) : (
                    <div className="loading-bar-container" style={{ marginTop: '20px' }}>
                        <div style={{
                            display: 'flex',
                            justifyContent: 'center',
                            marginBottom: '12px',
                            fontSize: '1rem',
                            color: '#f5576c',
                            fontWeight: 700,
                            gap: '8px',
                            alignItems: 'center'
                        }}>
                            <span>💪 최적의 루틴을 짜는 중입니다...</span>
                            <span>{Math.round(loadingProgress)}%</span>
                        </div>
                        <div style={{
                            width: '100%',
                            height: '12px',
                            background: '#f1f5f9',
                            borderRadius: '6px',
                            overflow: 'hidden'
                        }}>
                            <div style={{
                                width: `${loadingProgress}%`,
                                height: '100%',
                                background: 'linear-gradient(90deg, #f093fb, #f5576c)',
                                transition: 'width 0.2s ease-out'
                            }} />
                        </div>
                        <p style={{ textAlign: 'center', color: '#94a3b8', fontSize: '0.85rem', marginTop: '12px' }}>
                            잠시만 기다려주세요, AI 트레이너가 분석 중입니다.
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ExercisePlanPopup;
