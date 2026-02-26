import React, { useEffect, useMemo, useState } from 'react';
import { ChevronRight, CheckCircle2, Clock, Dumbbell } from 'lucide-react';
import { useLocation } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import '../../styles/LoginLight.css';

const WorkoutPlan = () => {
    const location = useLocation();
    const days = ['월', '화', '수', '목', '금', '토', '일'];
    const currentDay = new Date().getDay(); // 0 is Sunday
    const adjustedDay = currentDay === 0 ? 6 : currentDay - 1;

    const [planText, setPlanText] = useState(
        location.state?.planResult?.weekly_plan?.plan_data?.content ||
        location.state?.planResult?.weekly_plan?.plan_data?.raw_response ||
        ''
    );
    const [isLoading, setIsLoading] = useState(false);
    const [loadError, setLoadError] = useState('');
    const [expandedDay, setExpandedDay] = useState(null);

    useEffect(() => {
        const loadLatestPlan = async () => {
            if (planText) return;
            const storedUser = localStorage.getItem('user');
            const user = storedUser ? JSON.parse(storedUser) : null;
            const userId = location.state?.userId || user?.id;
            if (!userId) return;

            setIsLoading(true);
            setLoadError('');
            try {
                const res = await fetch(`/api/weekly-plans/user/${userId}?limit=1`);
                if (!res.ok) throw new Error('주간 운동 계획을 불러오지 못했습니다.');
                const data = await res.json();
                const latest = Array.isArray(data) && data.length > 0 ? data[0] : null;
                const text = latest?.plan_data?.content || latest?.plan_data?.raw_response || '';
                setPlanText(text);
            } catch (e) {
                setLoadError(e.message || '주간 운동 계획을 불러오지 못했습니다.');
            } finally {
                setIsLoading(false);
            }
        };

        loadLatestPlan();
    }, [location.state?.userId, planText]);

    const planByDay = useMemo(() => {
        if (!planText) return {};
        const dayMap = {
            '월요일': '월', '화요일': '화', '수요일': '수', '목요일': '목', '금요일': '금', '토요일': '토', '일요일': '일',
            '월': '월', '화': '화', '수': '수', '목': '목', '금': '금', '토': '토', '일': '일'
        };
        const sections = { '월': '', '화': '', '수': '', '목': '', '금': '', '토': '', '일': '' };
        const lines = planText.split('\n');
        let currentDays = [];

        const extractDays = (line) => {
            const found = [];
            Object.keys(dayMap).forEach((token) => {
                if (line.includes(token)) found.push(dayMap[token]);
            });
            return Array.from(new Set(found));
        };

        lines.forEach((line) => {
            const daysInLine = extractDays(line);
            if (daysInLine.length > 0) {
                currentDays = daysInLine;
                const cleaned = line.replace(/(월요일|화요일|수요일|목요일|금요일|토요일|일요일|월|화|수|목|금|토|일)\s*[,:-]*/g, '').trim();
                if (cleaned) {
                    currentDays.forEach((d) => {
                        sections[d] += (sections[d] ? '\n' : '') + cleaned;
                    });
                }
            } else if (currentDays.length > 0) {
                currentDays.forEach((d) => {
                    sections[d] += (sections[d] ? '\n' : '') + line;
                });
            }
        });

        return sections;
    }, [planText]);

    const filterExerciseOnly = (text) => {
        if (!text) return '';
        const dietKeywords = ['식단', '식사', '아침', '점심', '저녁', '간식', '칼로리', '단백질', '탄수화물', '지방', '수분', '물'];
        const exerciseKeywords = ['운동', '유산소', '근력', '스트레칭', '루틴', '세트', '회', '분', '걷기', '달리기', '자전거', '스쿼트', '푸쉬업', '플랭크', '요가', '필라테스'];
        const lines = text.split('\n');
        const kept = lines.filter((line) => {
            const trimmed = line.trim();
            if (!trimmed) return false;
            if (dietKeywords.some((k) => trimmed.includes(k))) return false;
            return exerciseKeywords.some((k) => trimmed.includes(k));
        });
        return kept.join('\n');
    };

    const getSummary = (text) => {
        const filtered = filterExerciseOnly(text);
        if (!filtered) return '운동 계획 없음';
        const firstLine = filtered
            .split('\n')
            .map(line => line.trim())
            .find(line => line.length > 0) || '운동 루틴';
        return firstLine.length > 42 ? `${firstLine.slice(0, 42)}...` : firstLine;
    };

    const fallbackWorkouts = [
        { day: '월', title: '상체 근력 강화', focus: '가슴, 어깨', duration: '60분', status: 'completed' },
        { day: '화', title: '코어 & 유산소', focus: '복부, 전신', duration: '45분', status: 'completed' },
        { day: '수', title: '하체 기초 다지기', focus: '허벅지, 엉덩이', duration: '50분', status: 'active' },
        { day: '목', title: '휴식 및 스트레칭', focus: '회복', duration: '20분', status: 'pending' },
        { day: '금', title: '등 & 이두 집중', focus: '등, 팔', duration: '55분', status: 'pending' },
        { day: '토', title: '하체 고강도 루틴', focus: '하체 전반', duration: '70분', status: 'pending' },
        { day: '일', title: '가벼운 산책', focus: '유산소', duration: '30분', status: 'pending' },
    ];

    return (
        <div className="main-content fade-in">
            <header className="dashboard-header">
                <h1>주간 운동 계획표</h1>
                <p>나만을 위한 맞춤형 주간 루틴입니다.</p>
            </header>

            <div className="workout-grid" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {isLoading && (
                    <div className="dashboard-card workout-item" style={{ padding: '20px', gridColumn: '1 / -1' }}>
                        불러오는 중입니다...
                    </div>
                )}
                {!!loadError && (
                    <div className="dashboard-card workout-item" style={{ padding: '20px', color: '#ef4444', gridColumn: '1 / -1' }}>
                        {loadError}
                    </div>
                )}

                {planText ? days.map((day, index) => {
                    const isExpanded = expandedDay === day;
                    const dayText = filterExerciseOnly(planByDay?.[day] || '');
                    const summary = getSummary(dayText);
                    return (
                    <div
                        key={day}
                        className={`dashboard-card workout-item ${index === adjustedDay ? 'active' : 'pending'} ${isExpanded ? 'expanded' : ''}`}
                        style={{
                            padding: '20px',
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'stretch',
                            gap: '10px',
                            borderLeft: index === adjustedDay ? '6px solid #4f46e5' : '1px solid rgba(0,0,0,0.05)',
                            background: index === adjustedDay ? '#fdfdfd' : 'white',
                            position: 'relative',
                            transition: 'all 0.3s'
                        }}
                        onClick={() => setExpandedDay(isExpanded ? null : day)}
                    >
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
                            <div className="day-badge" style={{
                                width: '36px',
                                height: '36px',
                                borderRadius: '10px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                background: index === adjustedDay ? '#4f46e5' : '#f1f5f9',
                                color: index === adjustedDay ? 'white' : '#64748b',
                                fontWeight: 700
                            }}>
                                {day}
                            </div>
                            {index === adjustedDay && (
                                <span style={{ fontSize: '0.7rem', padding: '2px 8px', background: '#e0e7ff', color: '#4f46e5', borderRadius: '10px', fontWeight: 700 }}>
                                    TODAY
                                </span>
                            )}
                        </div>

                        <div style={{ fontWeight: 700, fontSize: '0.95rem', color: '#0f172a' }}>
                            {summary}
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: '#94a3b8', fontSize: '0.8rem' }}>
                            <span>{dayText ? '자세히 보기' : '계획 없음'}</span>
                            <ChevronRight size={16} color="#cbd5e1" />
                        </div>

                        {isExpanded && (
                            <div className="markdown-content" style={{ fontSize: '0.9rem', borderTop: '1px dashed #e2e8f0', paddingTop: '10px' }}>
                                {dayText ? (
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                        {dayText}
                                    </ReactMarkdown>
                                ) : (
                                    <span style={{ color: '#94a3b8' }}>이날 계획이 없습니다.</span>
                                )}
                            </div>
                        )}
                    </div>
                )}) : fallbackWorkouts.map((item, index) => (
                    <div
                        key={item.day}
                        className={`dashboard-card workout-item ${item.status}`}
                        style={{
                            padding: '20px',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '16px',
                            borderLeft: index === adjustedDay ? '6px solid #4f46e5' : '1px solid rgba(0,0,0,0.05)',
                            background: index === adjustedDay ? '#fdfdfd' : 'white',
                            opacity: item.status === 'completed' ? 0.7 : 1,
                            position: 'relative',
                            transition: 'all 0.3s'
                        }}
                    >
                        <div className="day-badge" style={{
                            width: '40px',
                            height: '40px',
                            borderRadius: '12px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            background: index === adjustedDay ? '#4f46e5' : '#f1f5f9',
                            color: index === adjustedDay ? 'white' : '#64748b',
                            fontWeight: 700
                        }}>
                            {item.day}
                        </div>

                        <div style={{ flex: 1 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                                <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700 }}>{item.title}</h3>
                                {item.status === 'completed' && <CheckCircle2 size={16} color="#10b981" />}
                                {index === adjustedDay && <span style={{ fontSize: '0.7rem', padding: '2px 8px', background: '#e0e7ff', color: '#4f46e5', borderRadius: '10px', fontWeight: 700 }}>TODAY</span>}
                            </div>
                            <div style={{ display: 'flex', gap: '12px', fontSize: '0.85rem', color: '#94a3b8' }}>
                                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><Dumbbell size={14} /> {item.focus}</span>
                                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><Clock size={14} /> {item.duration}</span>
                            </div>
                        </div>

                        <ChevronRight size={20} color="#cbd5e1" />
                    </div>
                ))}
            </div>

            <div style={{ height: '80px' }}></div>

            <style>{`
                .workout-grid {
                    align-items: stretch;
                }
                .workout-item {
                    cursor: pointer;
                    min-height: 96px;
                }
                .workout-item.expanded {
                    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
                    transform: translateY(-2px);
                }
                .markdown-content p {
                    margin: 0 0 6px 0;
                    color: #475569;
                }
                .markdown-content ul, .markdown-content ol {
                    margin: 0 0 6px 18px;
                    color: #475569;
                }
                .markdown-content li {
                    margin: 2px 0;
                }
                .markdown-content h1, .markdown-content h2, .markdown-content h3 {
                    margin: 6px 0;
                    font-size: 0.95rem;
                }
                @media (max-width: 768px) {
                    .workout-item {
                        padding: 12px !important;
                        gap: 10px !important;
                    }
                    .workout-item h3 {
                        font-size: 1rem !important;
                    }
                    .workout-item .day-badge {
                        width: 36px !important;
                        height: 36px !important;
                        font-size: 0.9rem !important;
                    }
                }
                @media (max-width: 480px) {
                    .workout-item {
                        padding: 10px !important;
                        gap: 8px !important;
                    }
                    .workout-item h3 {
                        font-size: 0.95rem !important;
                    }
                    .workout-item .day-badge {
                        width: 32px !important;
                        height: 32px !important;
                        font-size: 0.85rem !important;
                    }
                    .workout-item > div:last-child {
                        font-size: 0.8rem !important;
                    }
                }
            `}</style>
        </div>
    );
};

export default WorkoutPlan;
