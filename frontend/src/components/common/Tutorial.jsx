import React, { useState, useEffect, useRef } from 'react';
import { X, ArrowLeft } from 'lucide-react';

const Tutorial = () => {
    const [currentStep, setCurrentStep] = useState(0);
    const [isVisible, setIsVisible] = useState(false);
    const [tooltipPosition, setTooltipPosition] = useState({});
    const [dontShowAgain, setDontShowAgain] = useState(false);
    const tooltipRef = useRef(null);

    // 튜토리얼 스텝 정의
    const tutorialSteps = [
        {
            id: 1,
            title: '대시보드 - 목표 & 분석',
            content: (
                <div>
                    <p><strong>목표 수정</strong>: 체중 목표와 재활 부위를 언제든지 수정할 수 있습니다.</p>
                    <br />
                    <p><strong>체중 변화 추이</strong>: 시작 → 현재 → 목표 체중을 그래프로 확인하세요.</p>
                    <br />
                    <p><strong>근육 & 체지방 분석</strong>: 이전 기록과 비교하여 신체 변화를 추적합니다.</p>
                </div>
            ),
            selector: '[data-tutorial-step="0"]',
            position: 'center-fixed'
        },
        {
            id: 2,
            title: '대시보드 - 운동 계획',
            content: (
                <div>
                    <p><strong>주간 운동 계획표</strong>: AI가 맞춤형 운동 스케줄을 생성합니다.</p>
                    <br />
                    <p><strong>부위별 운동 가이드</strong>: 상체, 복근, 하체 운동법을 확인하세요.</p>
                    <br />
                    <p><strong>건강 정보 & 팁</strong>: 식단, 수면, 수분 섭취 등 유용한 건강 정보를 제공합니다.</p>
                </div>
            ),
            selector: '[data-tutorial-step="3"]',
            position: 'center-fixed'
        },
        {
            id: 3,
            title: '홈',
            content: (
                <div>
                    <p><strong>홈 (대시보드)</strong></p>
                    <p>전체 요약을 한눈에 확인할 수 있는 메인 화면입니다.</p>
                </div>
            ),
            selector: 'a[href="/dashboard"]',
            position: 'top',
            targetBottomNav: 0
        },
        {
            id: 4,
            title: '신체기록',
            content: (
                <div>
                    <p><strong>신체기록 (OCR)</strong></p>
                    <p>인바디 검사지를 촬영하면 자동으로 수치를 인식하고, 이전 기록을 확인할 수 있습니다.</p>
                </div>
            ),
            selector: 'a[href="/inbody"]',
            position: 'top',
            targetBottomNav: 1
        },
        {
            id: 5,
            title: '챗봇',
            content: (
                <div>
                    <p><strong>AI 챗봇</strong></p>
                    <p>인바디 분석과 운동 플래너 질문을 할 수 있습니다.</p>
                </div>
            ),
            selector: 'a[href="/chatbot"]',
            position: 'top',
            targetBottomNav: 2
        },
        {
            id: 6,
            title: '운동법',
            content: (
                <div>
                    <p><strong>운동법 동영상</strong></p>
                    <p>부위별 운동법 동영상을 시청할 수 있습니다.</p>
                </div>
            ),
            selector: 'a[href="/exercise-guide"]',
            position: 'top',
            targetBottomNav: 3
        },
        {
            id: 7,
            title: '프로필',
            content: (
                <div>
                    <p><strong>프로필 설정</strong></p>
                    <p>계정 정보를 확인하고 설정을 변경할 수 있습니다.</p>
                </div>
            ),
            selector: 'a[href="/profile"]',
            position: 'top',
            targetBottomNav: 4
        }
    ];

    useEffect(() => {
        // localStorage에서 튜토리얼 완료 여부 확인
        const tutorialCompleted = localStorage.getItem('tutorialCompleted');
        console.log('[Tutorial] tutorialCompleted:', tutorialCompleted);

        if (!tutorialCompleted || tutorialCompleted !== 'true') {
            // 약간의 딜레이 후 튜토리얼 시작 (페이지 로드 후)
            setTimeout(() => {
                console.log('[Tutorial] Starting tutorial...');
                setIsVisible(true);
            }, 800);
        }
    }, []);

    // 타겟 요소로 스크롤
    useEffect(() => {
        if (!isVisible) return;

        const currentStepData = tutorialSteps[currentStep];
        const targetElement = currentStepData.selector
            ? document.querySelector(currentStepData.selector)
            : null;

        if (targetElement) {
            setTimeout(() => {
                // 하단 네비게이션 바가 아닌 경우에만 스크롤
                if (currentStepData.targetBottomNav === undefined) {
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start',
                        inline: 'nearest'
                    });
                }
            }, 100);
        }
    }, [currentStep, isVisible]);

    // 툴팁 위치 계산 및 업데이트
    useEffect(() => {
        if (!isVisible) return;

        const calculatePosition = () => {
            const currentStepData = tutorialSteps[currentStep];

            // center-fixed 포지션: 화면 중앙에 고정 (스크롤 무관)
            if (currentStepData.position === 'center-fixed') {
                setTooltipPosition({
                    position: 'fixed',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    maxWidth: '90%',
                    width: '450px',
                    zIndex: 1000000
                });
                return;
            }

            const targetElement = currentStepData.selector
                ? document.querySelector(currentStepData.selector)
                : null;

            if (!targetElement) {
                // 타겟 요소가 없으면 중앙에 표시
                setTooltipPosition({
                    position: 'fixed',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    maxWidth: '90%',
                    width: '400px'
                });
                return;
            }

            const rect = targetElement.getBoundingClientRect();
            const isMobile = window.innerWidth <= 768;
            const tooltipWidth = isMobile ? Math.min(window.innerWidth * 0.9, 400) : 400;
            const spacing = 15; // 간격을 좁혀서 더 가깝게 표시

            let newPosition = {
                position: 'fixed',
                maxWidth: isMobile ? '90%' : '400px',
                width: isMobile ? 'auto' : '400px'
            };

            if (currentStepData.targetBottomNav !== undefined) {
                // 하단 네비게이션 바 개별 아이템: 해당 아이템 위에 표시
                newPosition = {
                    ...newPosition,
                    bottom: `${window.innerHeight - rect.top + spacing}px`,
                    left: isMobile ? '50%' : `${rect.left + rect.width / 2}px`,
                    transform: isMobile ? 'translateX(-50%)' : 'translateX(-50%)',
                    width: isMobile ? 'auto' : '280px',
                    maxWidth: '280px'
                };
            } else if (currentStepData.position === 'right') {
                // 요소 오른쪽에 표시
                const topPosition = rect.top;
                const leftPosition = isMobile
                    ? '50%'
                    : Math.min(rect.right + spacing, window.innerWidth - tooltipWidth - 16);

                newPosition = {
                    ...newPosition,
                    top: `${topPosition}px`,
                    left: isMobile ? '50%' : `${leftPosition}px`,
                    transform: isMobile ? 'translateX(-50%)' : 'none',
                    maxWidth: isMobile ? '90%' : '320px',
                    width: isMobile ? 'auto' : '320px'
                };
            } else if (currentStepData.position === 'bottom') {
                // 요소 아래에 표시
                const topPosition = rect.bottom + spacing;
                const leftPosition = isMobile
                    ? '50%'
                    : Math.max(16, Math.min(rect.left, window.innerWidth - tooltipWidth - 16));

                newPosition = {
                    ...newPosition,
                    top: `${topPosition}px`,
                    left: isMobile ? '50%' : `${leftPosition}px`,
                    transform: isMobile ? 'translateX(-50%)' : 'none'
                };
            } else {
                // 요소 위에 표시
                const bottomPosition = window.innerHeight - rect.top + spacing;
                const leftPosition = isMobile
                    ? '50%'
                    : Math.max(16, Math.min(rect.left, window.innerWidth - tooltipWidth - 16));

                newPosition = {
                    ...newPosition,
                    bottom: `${bottomPosition}px`,
                    left: isMobile ? '50%' : `${leftPosition}px`,
                    transform: isMobile ? 'translateX(-50%)' : 'none'
                };
            }

            setTooltipPosition(newPosition);
        };

        // 초기 위치 계산 (스크롤 완료를 기다림)
        const timer1 = setTimeout(calculatePosition, 300);
        const timer2 = setTimeout(calculatePosition, 600);
        const timer3 = setTimeout(calculatePosition, 900);

        // 스크롤 및 리사이즈 시 위치 재계산
        window.addEventListener('scroll', calculatePosition, true);
        window.addEventListener('resize', calculatePosition);

        return () => {
            clearTimeout(timer1);
            clearTimeout(timer2);
            clearTimeout(timer3);
            window.removeEventListener('scroll', calculatePosition, true);
            window.removeEventListener('resize', calculatePosition);
        };
    }, [currentStep, isVisible]);

    const handleNext = () => {
        if (currentStep < tutorialSteps.length - 1) {
            setCurrentStep(currentStep + 1);
        } else {
            handleClose();
        }
    };

    const handlePrev = () => {
        if (currentStep > 0) {
            setCurrentStep(currentStep - 1);
        }
    };

    const handleClose = () => {
        if (dontShowAgain) {
            localStorage.setItem('tutorialCompleted', 'true');
        }
        setIsVisible(false);
    };

    if (!isVisible) return null;

    const currentStepData = tutorialSteps[currentStep];

    // 말풍선 꼬리 위치 계산
    const getArrowPosition = () => {
        const targetElement = currentStepData.selector
            ? document.querySelector(currentStepData.selector)
            : null;

        // 하단 네비게이션 바 아이템이면 항상 중앙
        if (currentStepData.targetBottomNav !== undefined) {
            return { left: '50%', transform: 'translateX(-50%)' };
        }

        if (!targetElement) {
            return { left: '50%', transform: 'translateX(-50%)' };
        }

        const rect = targetElement.getBoundingClientRect();
        const isMobile = window.innerWidth <= 768;

        if (isMobile) {
            return { left: '50%', transform: 'translateX(-50%)' };
        }

        // 타겟 요소의 중심에 화살표 위치
        const targetCenter = rect.left + rect.width / 2;
        const tooltipLeft = parseFloat(tooltipPosition.left) || rect.left;
        const arrowLeft = Math.max(20, Math.min(targetCenter - tooltipLeft, 380));

        return { left: `${arrowLeft}px` };
    };

    return (
        <>
            {/* 오버레이 */}
            <div
                style={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: 'rgba(0, 0, 0, 0.6)',
                    zIndex: 999998,
                    animation: 'fadeIn 0.3s ease',
                    cursor: 'pointer'
                }}
                onClick={handleNext}
            />

            {/* 말풍선 툴팁 */}
            <div
                ref={tooltipRef}
                style={{
                    ...tooltipPosition,
                    zIndex: 999999,
                    animation: 'slideIn 0.4s ease'
                }}
                onClick={(e) => e.stopPropagation()}
            >
                <div
                    style={{
                        background: 'white',
                        borderRadius: '16px',
                        padding: '24px',
                        boxShadow: '0 10px 40px rgba(0, 0, 0, 0.3)',
                        position: 'relative'
                    }}
                >
                    {/* 말풍선 꼬리 (center-fixed는 화살표 없음) */}
                    {currentStepData.position !== 'center-fixed' && (
                        <>
                            {currentStepData.position === 'bottom' ? (
                                <div
                                    style={{
                                        position: 'absolute',
                                        width: 0,
                                        height: 0,
                                        borderLeft: '12px solid transparent',
                                        borderRight: '12px solid transparent',
                                        borderBottom: '12px solid white',
                                        top: '-12px',
                                        ...getArrowPosition()
                                    }}
                                />
                            ) : currentStepData.position === 'right' ? (
                                <div
                                    style={{
                                        position: 'absolute',
                                        width: 0,
                                        height: 0,
                                        borderTop: '12px solid transparent',
                                        borderBottom: '12px solid transparent',
                                        borderRight: '12px solid white',
                                        left: '-12px',
                                        top: '30px'
                                    }}
                                />
                            ) : (
                                <div
                                    style={{
                                        position: 'absolute',
                                        width: 0,
                                        height: 0,
                                        borderLeft: '12px solid transparent',
                                        borderRight: '12px solid transparent',
                                        borderTop: '12px solid white',
                                        bottom: '-12px',
                                        ...getArrowPosition()
                                    }}
                                />
                            )}
                        </>
                    )}

                    {/* 닫기 버튼 */}
                    <button
                        onClick={handleClose}
                        style={{
                            position: 'absolute',
                            top: '16px',
                            right: '16px',
                            background: 'none',
                            border: 'none',
                            cursor: 'pointer',
                            color: '#94a3b8',
                            padding: '4px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            transition: 'color 0.2s'
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.color = '#64748b'}
                        onMouseLeave={(e) => e.currentTarget.style.color = '#94a3b8'}
                    >
                        <X size={20} />
                    </button>

                    {/* 스텝 표시 */}
                    <div
                        style={{
                            fontSize: '0.75rem',
                            color: '#6366f1',
                            fontWeight: 700,
                            marginBottom: '8px',
                            textTransform: 'uppercase',
                            letterSpacing: '0.5px'
                        }}
                    >
                        Step {currentStep + 1} / {tutorialSteps.length}
                    </div>

                    {/* 제목 */}
                    <h3
                        style={{
                            margin: '0 0 16px 0',
                            fontSize: '1.25rem',
                            fontWeight: 700,
                            color: '#1e293b',
                            paddingRight: '24px'
                        }}
                    >
                        {currentStepData.title}
                    </h3>

                    {/* 내용 */}
                    <div
                        style={{
                            fontSize: '0.95rem',
                            lineHeight: 1.6,
                            color: '#475569',
                            marginBottom: '20px'
                        }}
                    >
                        {currentStepData.content}
                    </div>

                    {/* 체크박스와 버튼 */}
                    <div
                        style={{
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '12px',
                            marginTop: '20px'
                        }}
                    >
                        {/* 다시보지 않기 체크박스 */}
                        <label
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '8px',
                                cursor: 'pointer',
                                fontSize: '0.85rem',
                                color: '#64748b',
                                userSelect: 'none'
                            }}
                        >
                            <input
                                type="checkbox"
                                checked={dontShowAgain}
                                onChange={(e) => setDontShowAgain(e.target.checked)}
                                style={{
                                    width: '16px',
                                    height: '16px',
                                    cursor: 'pointer',
                                    accentColor: '#6366f1'
                                }}
                            />
                            다시 보지 않기
                        </label>

                        {/* 버튼 그룹 */}
                        <div
                            style={{
                                display: 'flex',
                                gap: '8px'
                            }}
                        >
                            {currentStep > 0 && (
                                <button
                                    onClick={handlePrev}
                                    style={{
                                        flex: 1,
                                        padding: '10px 16px',
                                        background: '#f1f5f9',
                                        border: 'none',
                                        borderRadius: '10px',
                                        color: '#64748b',
                                        fontSize: '0.9rem',
                                        fontWeight: 600,
                                        cursor: 'pointer',
                                        transition: 'background 0.2s',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        gap: '4px'
                                    }}
                                    onMouseEnter={(e) => e.currentTarget.style.background = '#e2e8f0'}
                                    onMouseLeave={(e) => e.currentTarget.style.background = '#f1f5f9'}
                                >
                                    <ArrowLeft size={16} />
                                    이전
                                </button>
                            )}
                            <button
                                onClick={handleNext}
                                style={{
                                    flex: currentStep === 0 ? 1 : 2,
                                    padding: '10px 16px',
                                    background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
                                    border: 'none',
                                    borderRadius: '10px',
                                    color: 'white',
                                    fontSize: '0.9rem',
                                    fontWeight: 600,
                                    cursor: 'pointer',
                                    transition: 'transform 0.2s, box-shadow 0.2s',
                                    boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)'
                                }}
                                onMouseEnter={(e) => {
                                    e.currentTarget.style.transform = 'translateY(-2px)';
                                    e.currentTarget.style.boxShadow = '0 6px 16px rgba(59, 130, 246, 0.5)';
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.transform = 'translateY(0)';
                                    e.currentTarget.style.boxShadow = '0 4px 12px rgba(59, 130, 246, 0.3)';
                                }}
                            >
                                {currentStep < tutorialSteps.length - 1 ? '다음' : '완료'}
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <style>{`
                @keyframes fadeIn {
                    from {
                        opacity: 0;
                    }
                    to {
                        opacity: 1;
                    }
                }

                @keyframes slideIn {
                    from {
                        opacity: 0;
                        transform: scale(0.95);
                    }
                    to {
                        opacity: 1;
                        transform: scale(1);
                    }
                }

                @media (max-width: 768px) {
                    @keyframes slideIn {
                        from {
                            opacity: 0;
                            transform: translateX(-50%) scale(0.95);
                        }
                        to {
                            opacity: 1;
                            transform: translateX(-50%) scale(1);
                        }
                    }
                }
            `}</style>
        </>
    );
};

export default Tutorial;
