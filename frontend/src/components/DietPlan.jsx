import React, { useState, useEffect } from 'react';
import { UtensilsCrossed, Apple, Salad, Coffee, ChefHat, Info, ChevronRight, Activity, Flame, ShieldAlert } from 'lucide-react';
import '../AppLight.css';

const DietPlan = () => {
    const [userData, setUserData] = useState(null);
    const [activeMeal, setActiveMeal] = useState('아침');

    useEffect(() => {
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
            setUserData(JSON.parse(storedUser));
        }
    }, []);

    const MEAL_PLANS = {
        '아침': [
            { id: 1, name: '오트밀 볼', calories: 350, protein: 12, carbs: 45, fat: 10, items: ['압착 오트밀 50g', '저지방 우유 150ml', '블루베리 한 줌', '아몬드 5알'], icon: Coffee, color: '#6366f1' },
            { id: 2, name: '통밀 토스트와 계란', calories: 280, protein: 18, carbs: 32, fat: 8, items: ['통밀빵 2쪽', '스크램블 에그 2개', '아보카도 1/4개'], icon: UtensilsCrossed, color: '#f59e0b' }
        ],
        '점심': [
            { id: 1, name: '닭가슴살 샐러드', calories: 420, protein: 35, carbs: 20, fat: 15, items: ['닭가슴살 150g', '믹스 야채 100g', '오리엔탈 드레싱', '고구마 100g'], icon: Salad, color: '#10b981' },
            { id: 2, name: '소고기 야채 볶음', calories: 450, protein: 32, carbs: 25, fat: 18, items: ['우둔살 150g', '브로콜리', '파프리카', '현미밥 130g'], icon: UtensilsCrossed, color: '#ef4444' }
        ],
        '저녁': [
            { id: 1, name: '연어 스테이크', calories: 380, protein: 30, carbs: 10, fat: 22, items: ['연어 필렛 150g', '아스파라거스', '레몬 드레싱', '구운 토마토'], icon: ChefHat, color: '#818cf8' },
            { id: 2, name: '두부 스테이크', calories: 320, protein: 22, carbs: 15, fat: 12, items: ['단단한 두부 200g', '표고버섯', '간장 소스', '어린잎 채소'], icon: Salad, color: '#4ade80' }
        ]
    };

    const getRecommendedCalories = () => {
        if (!userData) return 2000;
        // Simple BMR calculation (approximate)
        const bmr = userData.gender === 'male' ?
            (10 * userData.start_weight + 6.25 * userData.height - 5 * userData.age + 5) :
            (10 * userData.start_weight + 6.25 * userData.height - 5 * userData.age - 161);

        let multiplier = 1.2; // Sedentary
        if (userData.activity_level === 'active') multiplier = 1.55;

        const goal = userData.goal_type || '유지';
        if (goal.includes('감량')) return Math.round(bmr * multiplier - 500);
        if (goal.includes('증량')) return Math.round(bmr * multiplier + 500);
        return Math.round(bmr * multiplier);
    };

    const recommendedCals = getRecommendedCalories();

    return (
        <div className="main-content fade-in">
            <header className="dashboard-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                    <div className="icon-badge" style={{ background: '#fef3c7', color: '#d97706', padding: '8px', borderRadius: '12px' }}>
                        <Apple size={24} />
                    </div>
                    <h1 style={{ margin: 0 }}>오늘의 식단</h1>
                </div>
                <p>나의 인바디 데이터와 목표에 맞춘 맞춤형 식단 가이드입니다.</p>
            </header>

            <div className="dashboard-card" style={{
                background: 'linear-gradient(135deg, #059669, #10b981)',
                color: 'white',
                marginBottom: '32px',
                padding: '24px'
            }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                    <span style={{ fontWeight: 600, opacity: 0.9 }}>권장 데일리 영양 가이드</span>
                    <Info size={18} opacity={0.7} />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                    <div className="daily-stat">
                        <span style={{ fontSize: '0.85rem', opacity: 0.8 }}>목표 칼로리</span>
                        <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
                            <span style={{ fontSize: '1.8rem', fontWeight: 800 }}>{recommendedCals}</span>
                            <span style={{ fontSize: '0.9rem' }}>kcal</span>
                        </div>
                    </div>
                    {userData && (
                        <div className="daily-stat">
                            <span style={{ fontSize: '0.85rem', opacity: 0.8 }}>현재 상태</span>
                            <div style={{ fontSize: '1.1rem', fontWeight: 700, padding: '4px 0' }}>
                                {userData.goal_type || '목표 유지'}
                            </div>
                        </div>
                    )}
                </div>
                <div style={{ marginTop: '20px', background: 'rgba(255,255,255,0.15)', borderRadius: '12px', padding: '12px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '8px' }}>
                        <span>탄수화물 50%</span>
                        <span>단백질 30%</span>
                        <span>지방 20%</span>
                    </div>
                    <div style={{ height: '6px', background: 'rgba(255,255,255,0.2)', borderRadius: '3px', display: 'flex', overflow: 'hidden' }}>
                        <div style={{ width: '50%', background: 'white' }}></div>
                        <div style={{ width: '30%', background: '#fbbf24' }}></div>
                        <div style={{ width: '20%', background: '#6ee7b7' }}></div>
                    </div>
                </div>
            </div>

            <div className="category-tabs-container">
                <div className="category-tabs">
                    {['아침', '점심', '저녁'].map(meal => (
                        <button
                            key={meal}
                            className={`tab-item ${activeMeal === meal ? 'active' : ''}`}
                            onClick={() => setActiveMeal(meal)}
                            style={activeMeal === meal ? { background: '#10b981', borderColor: '#10b981' } : {}}
                        >
                            <span>{meal} 가이드</span>
                        </button>
                    ))}
                </div>
            </div>

            <div className="diet-grid" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {MEAL_PLANS[activeMeal].map((plan, index) => (
                    <div key={plan.id} className="action-card fade-in" style={{
                        animationDelay: `${index * 0.1}s`,
                        flexDirection: 'row',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '24px'
                    }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                            <div className="icon-box" style={{ background: `${plan.color}15`, color: plan.color }}>
                                <plan.icon size={24} />
                            </div>
                            <div>
                                <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 800 }}>{plan.name}</h3>
                                <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                                    {plan.items.slice(0, 2).map((item, i) => (
                                        <span key={i} style={{ fontSize: '0.8rem', color: '#94a3b8' }}>#{item.split(' ')[0]}</span>
                                    ))}
                                </div>
                            </div>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                            <div style={{ color: '#10b981', fontWeight: 800, fontSize: '1.1rem' }}>{plan.calories} kcal</div>
                            <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '2px' }}>P {plan.protein}g | C {plan.carbs}g</div>
                        </div>
                    </div>
                ))}
            </div>

            <div className="dashboard-card" style={{ marginTop: '32px', background: '#f8fafc', border: '1px dashed #e2e8f0' }}>
                <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                    <ShieldAlert size={20} color="#f59e0b" style={{ marginTop: '2px' }} />
                    <div>
                        <h4 style={{ margin: '0 0 4px 0', fontSize: '0.95rem' }}>영양 팁</h4>
                        <p style={{ margin: 0, fontSize: '0.85rem', color: '#64748b', lineHeight: 1.5 }}>
                            식사 30분 전 물 한 잔을 마시면 신진대사가 활발해지고 과식을 예방하는 데 도움이 됩니다.
                            {activeMeal === '저녁' ? ' 저녁 식사는 취침 3시간 전까지 마치는 것이 좋습니다.' : ''}
                        </p>
                    </div>
                </div>
            </div>

            <div style={{ height: '40px' }}></div>
        </div>
    );
};

export default DietPlan;
