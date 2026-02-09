import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogOut, Edit2, X, Scale, CalendarDays, Dumbbell, ChevronRight } from 'lucide-react';
import ExercisePlanPopup from '../../components/common/ExercisePlanPopup';
import Tutorial from '../../components/common/Tutorial';
import '../../styles/LoginLight.css'; // 스타일 재사용

import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Tooltip, Legend, ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, BarChart, Bar, Cell } from 'recharts';
import { usePrefetch } from '../../hooks/usePrefetch';
import { getUserHealthRecords } from '../../services/inbodyService';

// ============================================
// 목업 설정
// 환경 변수로 목업 모드 관리 (.env 파일에서 설정)
const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === 'true';

// 목업 데이터: 사용자 정보 및 목표
const MOCK_USER = {
    id: 1,
    email: 'test@example.com',
    name: '김헬스',
    gender: 'male',
    start_weight: 78.5,
    target_weight: 70.0,
    goal_type: '감량',
    goal_description: '허리 재활',
    inbody_data: {
        weight: 74.2,
        skeletal_muscle: 34.5,
        body_fat_mass: 14.2
    }
};

// 목업 데이터: 인바디 기록 (과거 -> 현재)
const MOCK_RECORDS = [
    {
        id: 101,
        created_at: '2025-01-15T10:00:00',
        measurements: {
            "체중관리": { "체중": 76.5, "골격근량": 33.8, "체지방량": 16.5 },
            "비만분석": { "체지방률": 21.5, "BMI": 24.5 }
        }
    },
    {
        id: 102,
        created_at: '2025-02-02T10:00:00', // 오늘
        measurements: {
            "체중관리": { "체중": 74.2, "골격근량": 34.5, "체지방량": 14.2 }, // 근육 증가, 체지방 감소
            "비만분석": { "체지방률": 19.1, "BMI": 23.8 }
        }
    }
];

// 원형 프로그레스 + 마일스톤 컴포넌트
const CircularProgress = ({ progress, currentWeight, targetWeight, startWeight, goalType }) => {
    // 모바일에서는 더 작은 사이즈 사용
    const isMobile = typeof window !== 'undefined' && window.innerWidth <= 480;
    const size = isMobile ? 140 : 160;
    const strokeWidth = isMobile ? 10 : 12;
    const radius = (size - strokeWidth) / 2;
    const circumference = radius * 2 * Math.PI;
    const offset = circumference - (progress / 100) * circumference;

    // 감량/증량에 따른 표시
    const weightChanged = Math.abs(currentWeight - startWeight).toFixed(1);
    const weightRemaining = Math.abs(targetWeight - currentWeight).toFixed(1);
    const isLoss = targetWeight < startWeight;
    const actionText = isLoss ? '감량' : (targetWeight > startWeight ? '증량' : '유지');

    // 마일스톤 정의
    const milestones = [
        { percent: 25, label: '시작', emoji: '🌱' },
        { percent: 50, label: '절반', emoji: '⭐' },
        { percent: 75, label: '거의', emoji: '🔥' },
        { percent: 100, label: '완료', emoji: '🏆' }
    ];

    // 다음 마일스톤 찾기
    const nextMilestone = milestones.find(m => m.percent > progress) || milestones[milestones.length - 1];
    const totalWeightChange = Math.abs(targetWeight - startWeight);
    const currentWeightChange = Math.abs(currentWeight - startWeight);
    const toNextMilestone = Math.max(0, (nextMilestone.percent / 100 * totalWeightChange) - currentWeightChange).toFixed(1);

    // 진행률에 따른 색상
    const getProgressColor = (p) => {
        if (p >= 100) return '#22c55e'; // 초록 - 완료
        if (p >= 75) return '#8b5cf6'; // 보라 - 거의 완료
        if (p >= 50) return '#6366f1'; // 파랑 - 절반 이상
        return '#818cf8'; // 연보라 - 시작
    };

    const progressColor = getProgressColor(progress);

    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            padding: isMobile ? '10px 0' : '16px 0'
        }}>
            {/* 원형 프로그레스 */}
            <div style={{ position: 'relative', width: size, height: size }}>
                <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
                    {/* 배경 원 */}
                    <circle
                        cx={size / 2}
                        cy={size / 2}
                        r={radius}
                        fill="none"
                        stroke="#e2e8f0"
                        strokeWidth={strokeWidth}
                    />
                    {/* 진행 원 */}
                    <circle
                        cx={size / 2}
                        cy={size / 2}
                        r={radius}
                        fill="none"
                        stroke={progressColor}
                        strokeWidth={strokeWidth}
                        strokeLinecap="round"
                        strokeDasharray={circumference}
                        strokeDashoffset={offset}
                        style={{
                            transition: 'stroke-dashoffset 1s ease-out, stroke 0.3s ease',
                            filter: `drop-shadow(0 0 6px ${progressColor}40)`
                        }}
                    />
                </svg>
                {/* 중앙 텍스트 */}
                <div style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    textAlign: 'center'
                }}>
                    <div style={{
                        fontSize: isMobile ? '1.8rem' : '2.2rem',
                        fontWeight: 800,
                        color: progressColor,
                        lineHeight: 1
                    }}>
                        {progress}%
                    </div>
                    <div style={{
                        fontSize: isMobile ? '0.7rem' : '0.8rem',
                        color: '#64748b',
                        fontWeight: 600,
                        marginTop: '2px'
                    }}>
                        목표 달성
                    </div>
                </div>
            </div>

            {/* 마일스톤 표시 */}
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                width: '100%',
                maxWidth: isMobile ? '220px' : '280px',
                marginTop: isMobile ? '10px' : '14px',
                padding: '0 4px'
            }}>
                {milestones.map((milestone) => {
                    const isAchieved = progress >= milestone.percent;
                    const isCurrent = progress >= milestone.percent - 25 && progress < milestone.percent;
                    return (
                        <div
                            key={milestone.percent}
                            style={{
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                opacity: isAchieved ? 1 : 0.4,
                                transition: 'all 0.3s ease'
                            }}
                        >
                            <div style={{
                                width: isMobile ? '28px' : '36px',
                                height: isMobile ? '28px' : '36px',
                                borderRadius: '50%',
                                background: isAchieved
                                    ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                                    : '#e2e8f0',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontSize: isMobile ? '12px' : '16px',
                                boxShadow: isAchieved ? '0 2px 8px rgba(102, 126, 234, 0.3)' : 'none',
                                border: isCurrent ? '2px solid #fbbf24' : 'none',
                                animation: isCurrent ? 'pulse 2s infinite' : 'none'
                            }}>
                                {isAchieved ? milestone.emoji : '○'}
                            </div>
                            <span style={{
                                fontSize: isMobile ? '0.6rem' : '0.65rem',
                                color: isAchieved ? '#475569' : '#94a3b8',
                                fontWeight: isAchieved ? 600 : 400,
                                marginTop: '2px'
                            }}>
                                {milestone.percent}%
                            </span>
                        </div>
                    );
                })}
            </div>

            {/* 다음 마일스톤까지 */}
            {progress < 100 && (
                <div style={{
                    marginTop: isMobile ? '10px' : '14px',
                    padding: isMobile ? '8px 12px' : '10px 16px',
                    background: 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)',
                    borderRadius: '10px',
                    textAlign: 'center',
                    border: '1px solid #fbbf24'
                }}>
                    <span style={{ fontSize: isMobile ? '0.75rem' : '0.85rem', color: '#92400e' }}>
                        다음 <strong>{nextMilestone.emoji} {nextMilestone.percent}%</strong>까지{' '}
                        <strong style={{ color: '#b45309' }}>{toNextMilestone}kg</strong>
                    </span>
                </div>
            )}

            {/* 감량/증량 완료 정보 */}
            <div style={{
                marginTop: isMobile ? '10px' : '14px',
                textAlign: 'center'
            }}>
                <div style={{
                    fontSize: isMobile ? '1.1rem' : '1.3rem',
                    fontWeight: 700,
                    color: '#1e293b',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px'
                }}>
                    <span style={{ fontSize: isMobile ? '1.2rem' : '1.4rem' }}>🔥</span>
                    <span style={{ color: progressColor }}>{weightChanged}kg</span>
                    <span>{actionText} 완료!</span>
                </div>
                <div style={{
                    fontSize: isMobile ? '0.8rem' : '0.85rem',
                    color: '#64748b',
                    marginTop: '4px'
                }}>
                    목표까지 <strong style={{ color: '#475569' }}>{weightRemaining}kg</strong> 남음
                </div>
            </div>

            {/* 체중 정보 요약 바 */}
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                width: '100%',
                maxWidth: isMobile ? '220px' : '260px',
                marginTop: isMobile ? '10px' : '14px',
                padding: isMobile ? '8px 12px' : '10px 14px',
                background: '#f8fafc',
                borderRadius: '10px',
                fontSize: isMobile ? '0.75rem' : '0.8rem'
            }}>
                <div style={{ textAlign: 'center' }}>
                    <div style={{ color: '#94a3b8', marginBottom: '1px', fontSize: isMobile ? '0.65rem' : '0.7rem' }}>시작</div>
                    <div style={{ fontWeight: 700, color: '#64748b' }}>{startWeight}kg</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                    <div style={{ color: '#94a3b8', marginBottom: '1px', fontSize: isMobile ? '0.65rem' : '0.7rem' }}>현재</div>
                    <div style={{ fontWeight: 700, color: '#6366f1' }}>{currentWeight}kg</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                    <div style={{ color: '#94a3b8', marginBottom: '1px', fontSize: isMobile ? '0.65rem' : '0.7rem' }}>목표</div>
                    <div style={{ fontWeight: 700, color: '#8b5cf6' }}>{targetWeight}kg</div>
                </div>
            </div>
        </div>
    );
};

// 건강 정보 카드뉴스 컴포넌트
const HealthTipsSection = () => {
    const [selectedTip, setSelectedTip] = useState(null);

    const Illustration = ({ type }) => {
        switch (type) {
            case 'diet':
                return (
                    <svg width="72" height="72" viewBox="0 0 72 72" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <rect x="6" y="8" width="60" height="56" rx="18" fill="#F0F7FF" />
                        <circle cx="28" cy="38" r="10" fill="#34D399" />
                        <circle cx="44" cy="34" r="8" fill="#FBBF24" />
                        <circle cx="42" cy="48" r="7" fill="#F472B6" />
                        <rect x="20" y="50" width="32" height="6" rx="3" fill="#60A5FA" />
                    </svg>
                );
            case 'sleep':
                return (
                    <svg width="72" height="72" viewBox="0 0 72 72" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <rect x="6" y="8" width="60" height="56" rx="18" fill="#FDF2FF" />
                        <path d="M38 24C29.7157 24 23 30.7157 23 39C23 47.2843 29.7157 54 38 54C45.1797 54 51.1686 49.1782 52.7 42.5C50.7 44.2 48.1 45.2 45.3 45.2C38.6 45.2 33.2 39.8 33.2 33.1C33.2 30.3 34.2 27.7 35.9 25.7C36.6 24.9 37.3 24.4 38 24Z" fill="#A78BFA" />
                        <circle cx="50" cy="24" r="3" fill="#FBBF24" />
                    </svg>
                );
            case 'water':
                return (
                    <svg width="72" height="72" viewBox="0 0 72 72" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <rect x="6" y="8" width="60" height="56" rx="18" fill="#EEF6FF" />
                        <path d="M36 18C36 18 20 38 20 46C20 54.8366 27.1634 62 36 62C44.8366 62 52 54.8366 52 46C52 38 36 18 36 18Z" fill="#60A5FA" />
                        <path d="M28 50C29.5 53.5 33 56 36.8 56" stroke="#E0F2FE" strokeWidth="4" strokeLinecap="round" />
                    </svg>
                );
            case 'recovery':
            default:
                return (
                    <svg width="72" height="72" viewBox="0 0 72 72" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <rect x="6" y="8" width="60" height="56" rx="18" fill="#FFF1F2" />
                        <path d="M22 46C22 39.3726 27.3726 34 34 34H50C52.2091 34 54 35.7909 54 38V40C54 42.2091 52.2091 44 50 44H36C33.7909 44 32 45.7909 32 48V50C32 52.2091 30.2091 54 28 54H26C23.7909 54 22 52.2091 22 50V46Z" fill="#FB7185" />
                        <circle cx="26" cy="32" r="6" fill="#F59E0B" />
                    </svg>
                );
        }
    };

    const healthTips = [
        {
            id: 1,
            title: '균형 잡힌 식단',
            type: 'diet',
            color: '#a78bfa',
            bg: '#faf5ff',
            summary: '탄·단·지 비율과 식사 타이밍',
            content: '한 끼 기준으로 접시의 절반은 채소, 1/4은 단백질, 1/4은 탄수화물로 구성하세요. 가공식품과 당 음료는 줄이고, 하루 단백질은 체중(kg)×1.2~1.6g을 목표로 하세요.'
        },
        {
            id: 2,
            title: '수면의 질 높이기',
            type: 'sleep',
            color: '#e879f9',
            bg: '#fdf4ff',
            summary: '회복을 좌우하는 수면 습관',
            content: '취침·기상 시간을 매일 일정하게 유지하세요. 카페인은 오후 2시 이후 피하고, 취침 60분 전에는 밝은 화면을 줄이면 수면 깊이가 좋아집니다.'
        },
        {
            id: 3,
            title: '수분 섭취 가이드',
            type: 'water',
            color: '#60a5fa',
            bg: '#eff6ff',
            summary: '체중 기반 수분 루틴',
            content: '하루 기본 물 섭취량은 체중(kg)×30ml를 기준으로 하고, 운동 전후에는 각각 300~500ml를 추가하세요. 소변 색이 연한 노란색이면 적정 수분 상태입니다.'
        },
        {
            id: 4,
            title: '운동 후 회복',
            type: 'recovery',
            color: '#f472b6',
            bg: '#fdf2f8',
            summary: '근육 회복과 부상 예방',
            content: '운동 후 30~60분 내 단백질 20~30g과 탄수화물을 함께 섭취하세요. 같은 근육군은 48시간 휴식하고, 스트레칭과 가벼운 폼롤링으로 회복을 돕습니다.'
        }
    ];

    return (
        <>
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
                            <Illustration type={tip.type} />
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
                            <div style={{ marginBottom: '12px' }}>
                                <Illustration type={selectedTip.type} />
                            </div>
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
    const [healthRecords, setHealthRecords] = useState([]);
    const [motivationMessage, setMotivationMessage] = useState('');

    // Edge Native: Resource Prefetching
    usePrefetch([
        '/src/pages/Chatbot/Chatbot.jsx',
        '/src/pages/Exercise/WorkoutPlan.jsx',
        '/src/pages/Exercise/ExerciseGuide.jsx'
    ]);

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

    // Exercise Plan Popup State
    const [isExercisePopupOpen, setIsExercisePopupOpen] = useState(false);

    // 건강 정보 섹션 토글 상태 (기본: 접힘)
    const [isHealthTipsOpen, setIsHealthTipsOpen] = useState(true);
    const [showInbodyPrompt, setShowInbodyPrompt] = useState(false);

    const handleExercisePlanSubmit = (data) => {
        setIsExercisePopupOpen(false);
        // FIX: 챗봇 페이지(/chatbot/...)가 아닌 주간 운동 계획표 페이지(/workout-plan)로 이동하도록 수정
        navigate('/workout-plan', {
            state: {
                planRequest: data,
                userId: userData?.id
            }
        });
    };

    const openVideo = (type) => {
        let videoId = 'gMaB-fG4u4g';
        if (type === '상체') videoId = 'tzN69l791VU';
        if (type === '복근') videoId = 'hR5s71aM6fw';
        if (type === '하체') videoId = 'W_VGlKk88K4';

        setActiveVideo({
            id: videoId,
            title: `${type} 운동 가이드`
        });
    };

    useEffect(() => {
        const messages = [
            '오늘도 한 걸음, 내일은 두 걸음!',
            '작은 습관이 큰 변화를 만듭니다.',
            '지금의 선택이 미래의 몸을 만듭니다.',
            '천천히 해도 괜찮아요, 멈추지만 않으면 됩니다.',
            '어제의 나보다 1%만 더!',
            '꾸준함이 가장 강력한 전략입니다.',
            '포기하지 않는 순간 변화가 시작됩니다.',
            '오늘의 노력은 내일의 자신감!',
            '몸은 정직합니다. 꾸준히 해볼까요?',
            '지금의 루틴이 목표를 가까이 데려다줘요.'
        ];
        setMotivationMessage(messages[Math.floor(Math.random() * messages.length)]);
        //
        const loadDashboardData = async () => {
            // 1. 사용자 정보 로드
            const storedUser = localStorage.getItem('user');
            let currentUser = storedUser ? JSON.parse(storedUser) : null;

            if (USE_MOCK_DATA) {
                currentUser = { ...MOCK_USER, ...currentUser }; // 로컬 스토리지 값 우선하되 목업으로 보완
                setUserData(currentUser);
                setHealthRecords(MOCK_RECORDS);
                setShowInbodyPrompt(false);
            } else if (currentUser) {
                setUserData(currentUser);
                try {
                    // API로 이전 기록 2개 가져오기
                    const records = await getUserHealthRecords(currentUser.id, 2);
                    // API는 최신순(내림차순)으로 오므로, 그래프용으로는 오름차순(과거->현재) 정렬 필요
                    setHealthRecords([...records].reverse());
                    const hasInbody =
                        (records && records.length > 0) ||
                        !!currentUser.inbody_data?.weight ||
                        !!currentUser.inbody_data?.measurements;
                    setShowInbodyPrompt(!hasInbody);
                } catch (error) {
                    console.error("Failed to fetch records:", error);
                    const hasInbody =
                        !!currentUser.inbody_data?.weight ||
                        !!currentUser.inbody_data?.measurements;
                    setShowInbodyPrompt(!hasInbody);
                }
            }

            if (currentUser) {
                setEditForm({
                    start_weight: currentUser.start_weight || '',
                    target_weight: currentUser.target_weight || '',
                    goal_type: currentUser.goal_type || '감량',
                    goal_description: currentUser.goal_description || ''
                });
            }
        };

        loadDashboardData();
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

                // exerciseSettings의 goal도 함께 업데이트
                const savedSettings = JSON.parse(localStorage.getItem('exerciseSettings') || '{}');
                savedSettings.goal = editForm.goal_type;
                localStorage.setItem('exerciseSettings', JSON.stringify(savedSettings));

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

    // 1. 체중 변화 데이터 (이전 -> 현재 -> 목표) - 정확히 3개 막대
    const getWeightChartData = () => {
        if (!userData) return [];
        const data = [];

        // 이전 체중 (첫 번째 기록 또는 시작 체중)
        if (healthRecords.length > 0) {
            const previousRecord = healthRecords[0];
            data.push({
                name: '이전체중',
                weight: previousRecord.measurements?.["체중관리"]?.["체중"] || userData.start_weight || 0,
                isGoal: false,
                color: '#94a3b8' // 회색
            });
        } else if (userData.start_weight) {
            data.push({
                name: '시작체중',
                weight: userData.start_weight,
                isGoal: false,
                color: '#94a3b8'
            });
        }

        // 현재 체중 (가장 최신 기록 또는 현재 인바디 데이터)
        if (healthRecords.length > 1) {
            const currentRecord = healthRecords[healthRecords.length - 1];
            data.push({
                name: '현재체중',
                weight: currentRecord.measurements?.["체중관리"]?.["체중"] || userData.inbody_data?.weight || 0,
                isGoal: false,
                color: '#6366f1' // 파란색
            });
        } else if (userData.inbody_data?.weight) {
            data.push({
                name: '현재체중',
                weight: userData.inbody_data.weight,
                isGoal: false,
                color: '#6366f1'
            });
        }

        // 목표 체중
        if (userData.target_weight) {
            data.push({
                name: '목표체중',
                weight: userData.target_weight,
                isGoal: true,
                color: '#8b5cf6' // 보라색
            });
        }

        return data;
    };

    // 2. 근육/체지방 분석 데이터 (현재 vs 이전)
    const getBodyCompChartData = () => {
        // 최소 2개의 기록이 필요 (이전 vs 현재 비교)
        if (healthRecords.length < 2) return [];

        // 첫 번째 기록 = 이전, 마지막 기록 = 현재
        const previousRecord = healthRecords[0];
        const currentRecord = healthRecords[healthRecords.length - 1];

        const prevMuscle = previousRecord.measurements?.["체중관리"]?.['골격근량'] || 0;
        const prevFat = previousRecord.measurements?.["체중관리"]?.['체지방량'] || 0;

        const currentMuscle = currentRecord.measurements?.["체중관리"]?.['골격근량'] || 0;
        const currentFat = currentRecord.measurements?.["체중관리"]?.['체지방량'] || 0;

        return [
            {
                name: '골격근량',
                current: currentMuscle,
                previous: prevMuscle,
                unit: 'kg',
                currentColor: '#6366f1', // 파란색 (현재 수치)
                previousColor: '#94a3b8'  // 회색 (이전 수치)
            },
            {
                name: '체지방량',
                current: currentFat,
                previous: prevFat,
                unit: 'kg',
                currentColor: '#6366f1', // 파란색 (현재 수치)
                previousColor: '#94a3b8'  // 회색 (이전 수치)
            }
        ];
    };


    const weightChartData = getWeightChartData();
    const bodyCompChartData = getBodyCompChartData();



    return (
        <div className="main-content">
            {/* 튜토리얼 컴포넌트 */}
            <Tutorial />

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
                    <div className="goal-overview-card tutorial-spotlight" data-tutorial-step="0" data-tutorial-anchor="1">
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

                    {/* 동기부여 메시지 카드 */}
                    <div className="dashboard-card chart-card fade-in delay-2" style={{ marginTop: '24px' }}>
                        <h3>🌿 오늘의 동기부여</h3>
                        <div style={{
                            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                            padding: '12px 16px',
                            borderRadius: '12px',
                            color: 'white',
                            textAlign: 'center',
                            fontWeight: 600,
                            fontSize: '0.95rem',
                            boxShadow: '0 4px 12px rgba(102, 126, 234, 0.2)'
                        }}>
                            {motivationMessage || '오늘도 한 걸음, 내일은 두 걸음!'}
                        </div>
                    </div>

                    {/* 체중 변화 차트 카드 */}
                    <div className="dashboard-card chart-card fade-in delay-2 tutorial-spotlight" style={{ marginTop: '16px' }}>
                        <h4 style={{ fontSize: '1rem', color: '#475569', margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }} data-tutorial-step="1">
                            <Scale size={18} /> 체중 변화 추이
                        </h4>
                        <div style={{ width: '100%', height: 220 }}>
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart
                                    data={weightChartData}
                                    margin={{ top: 10, right: 30, left: 0, bottom: 10 }}
                                    barSize={50}
                                >
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                                    <XAxis
                                        dataKey="name"
                                        axisLine={false}
                                        tickLine={false}
                                        tick={{ fill: '#64748b', fontSize: 13, fontWeight: 600 }}
                                    />
                                    <YAxis
                                        domain={['dataMin - 5', 'dataMax + 5']}
                                        axisLine={false}
                                        tickLine={false}
                                        tick={{ fill: '#94a3b8', fontSize: 11 }}
                                    />
                                    <Tooltip
                                        cursor={{ fill: 'transparent' }}
                                        content={({ active, payload }) => {
                                            if (active && payload && payload.length) {
                                                const data = payload[0].payload;
                                                return (
                                                    <div style={{ background: 'white', padding: '12px', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
                                                        <p style={{ margin: 0, fontWeight: 'bold', color: '#1e293b', fontSize: '0.95rem' }}>{data.name}</p>
                                                        <p style={{ margin: '4px 0 0', color: data.color, fontSize: '1.15rem', fontWeight: 'bold' }}>{data.weight} kg</p>
                                                    </div>
                                                );
                                            }
                                            return null;
                                        }}
                                    />
                                    <Bar dataKey="weight" radius={[8, 8, 0, 0]} animationDuration={1500}>
                                        {weightChartData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.color || '#6366f1'} />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>

                        {/* 2. 근육/체지방 분석 (Bar Chart) */}
                        <div style={{ marginTop: '24px' }} data-tutorial-step="1-2">
                            <h4 style={{ fontSize: '1rem', color: '#475569', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <Dumbbell size={18} /> 근육 & 체지방 분석
                            </h4>
                            <div style={{ width: '100%', height: 200 }}>
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart
                                        data={bodyCompChartData}
                                        layout="vertical"
                                        margin={{ top: 0, right: 30, left: 20, bottom: 0 }}
                                        barSize={20}
                                    >
                                        <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#e2e8f0" />
                                        <XAxis type="number" hide />
                                        <YAxis
                                            dataKey="name"
                                            type="category"
                                            axisLine={false}
                                            tickLine={false}
                                            tick={{ fill: '#475569', fontSize: 13, fontWeight: 600 }}
                                            width={70}
                                        />
                                        <Tooltip
                                            cursor={{ fill: 'transparent' }}
                                            content={({ active, payload }) => {
                                                if (active && payload && payload.length) {
                                                    const data = payload[0].payload;
                                                    return (
                                                        <div style={{ background: 'white', padding: '12px', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
                                                            <p style={{ margin: 0, fontWeight: 'bold', color: '#1e293b' }}>{data.name}</p>
                                                            <p style={{ margin: '4px 0 0', color: data.color }}>현재: {data.current} {data.unit}</p>
                                                            <p style={{ margin: 0, color: '#94a3b8', fontSize: '0.85rem' }}>권장: {data.standard} {data.unit}</p>
                                                        </div>
                                                    );
                                                }
                                                return null;
                                            }}
                                        />
                                        <Legend wrapperStyle={{ paddingTop: '10px' }} />
                                        <Bar dataKey="current" name="현재" radius={[0, 4, 4, 0]} animationDuration={1500} fill="#6366f1" />
                                        <Bar dataKey="previous" name="이전" fill="#94a3b8" radius={[0, 4, 4, 0]} animationDuration={1500} />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
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

            {showInbodyPrompt && (
                <div className="dashboard-modal-overlay fade-in" onClick={() => setShowInbodyPrompt(false)}>
                    <div className="dashboard-modal-card" onClick={(e) => e.stopPropagation()}>
                        <div className="dashboard-modal-header">
                            <h3>인바디 수치 분석이 필요해요</h3>
                        </div>
                        <div className="dashboard-modal-body">
                            <p style={{ marginTop: 0 }}>
                                회원가입 후 인바디 정보를 등록하지 않으셨습니다. 정확한 분석을 위해 인바디 수치를 먼저 입력해주세요.
                            </p>
                        </div>
                        <div className="dashboard-modal-footer">
                            <button
                                type="button"
                                className="secondary-button"
                                onClick={() => setShowInbodyPrompt(false)}
                            >
                                나중에
                            </button>
                            <button
                                type="button"
                                className="primary-button"
                                onClick={() => navigate('/inbody')}
                            >
                                인바디 등록하기
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <div className="quick-actions-grid fade-in delay-1 tutorial-spotlight" data-tutorial-anchor="2">
                <div onClick={() => {
                    const savedSettings = JSON.parse(localStorage.getItem('exerciseSettings') || 'null');
                    if (savedSettings && savedSettings.goal && savedSettings.preferences?.length > 0) {
                        handleExercisePlanSubmit(savedSettings);
                    } else {
                        setIsExercisePopupOpen(true);
                    }
                }} className="action-card primary" style={{ cursor: 'pointer' }} data-tutorial-step="3">
                    <div className="icon-box">
                        <CalendarDays size={24} />
                    </div>
                    <div className="text-box">
                        <h3>주간 운동 계획표</h3>
                        <p>이번 주 운동 스케줄 확인하기</p>
                    </div>
                </div>

                <div onClick={() => navigate('/exercise-guide')} className="action-card primary" style={{ cursor: 'pointer' }} data-tutorial-step="4">
                    <div className="icon-box">
                        <Dumbbell size={24} />
                    </div>
                    <div className="text-box">
                        <h3>부위별 운동 가이드</h3>
                        <p>상체, 복근, 하체 운동법 확인하기</p>
                    </div>
                </div>
            </div>



            {/* 건강 정보 카드뉴스 섹션 */}
            <div
                className="section-title fade-in delay-3 tutorial-spotlight"
                onClick={() => setIsHealthTipsOpen(prev => !prev)}
                style={{
                    marginTop: '32px',
                    marginBottom: '16px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between'
                }}
            >
                <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 800 }} data-tutorial-step="5">💡 건강 정보 & 팁</h3>
                <ChevronRight
                    size={20}
                    style={{
                        color: '#64748b',
                        transition: 'transform 0.3s ease',
                        transform: isHealthTipsOpen ? 'rotate(90deg)' : 'rotate(0deg)'
                    }}
                />
            </div>

            {isHealthTipsOpen && <HealthTipsSection />}

            {/* Exercise Plan Popup */}
            <ExercisePlanPopup
                isOpen={isExercisePopupOpen}
                onClose={() => setIsExercisePopupOpen(false)}
                onSubmit={handleExercisePlanSubmit}
            />

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
