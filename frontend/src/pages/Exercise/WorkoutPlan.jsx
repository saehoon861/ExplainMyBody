import React from 'react';
import { Calendar, ChevronRight, CheckCircle2, Clock, Dumbbell } from 'lucide-react';
import '../../styles/LoginLight.css';

const WorkoutPlan = () => {
    const days = ['월', '화', '수', '목', '금', '토', '일'];
    const currentDay = new Date().getDay(); // 0 is Sunday
    const adjustedDay = currentDay === 0 ? 6 : currentDay - 1;

    const mockWorkouts = [
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

            <div className="workout-grid" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {mockWorkouts.map((item, index) => (
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
                @media (max-width: 768px) {
                    .workout-item {
                        padding: 16px !important;
                        gap: 12px !important;
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
                        padding: 14px !important;
                        gap: 10px !important;
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
