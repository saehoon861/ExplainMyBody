import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Dumbbell, Youtube, ChevronRight, Activity, Zap, Shield } from 'lucide-react';
import '../AppLight.css';

const ExerciseGuide = () => {
    const [activeCategory, setActiveCategory] = useState('상체');
    const location = useLocation();

    const EXERCISE_GUIDES = {
        '상체': [
            { id: 1, name: '팔굽혀펴기 (Push-up)', url: 'https://www.youtube.com/results?search_query=팔굽혀펴기+자세', desc: '가슴, 어깨, 삼두근을 동시에 강화하는 최고의 맨몸 운동입니다.', tag: '기초' },
            { id: 2, name: '턱걸이 (Pull-up)', url: 'https://www.youtube.com/results?search_query=턱걸이+자세', desc: '넓은 등과 강한 팔을 만드는 상체 운동의 꽃입니다.', tag: '상급' },
            { id: 3, name: '드레스 다운 (Lat Pull Down)', url: 'https://www.youtube.com/results?search_query=렛풀다운+자세', desc: '등 근육의 너비를 조절하고 광배근을 발달시킵니다.', tag: '추천' },
            { id: 4, name: '숄더 프레스 (Shoulder Press)', url: 'https://www.youtube.com/results?search_query=숄더프레스+자세', desc: '탄탄하고 넓은 어깨 라인을 만드는 필수 종목입니다.', tag: '필수' }
        ],
        '복근': [
            { id: 5, name: '크런치 (Crunch)', url: 'https://www.youtube.com/results?search_query=크런치+자세', desc: '상복부를 집중적으로 타격하여 복근 라인을 선명하게 만듭니다.', tag: '기초' },
            { id: 6, name: '레그 레이즈 (Leg Raise)', url: 'https://www.youtube.com/results?search_query=레그레이즈+자세', desc: '하복부와 코어 하부 근력을 강화하는 데 효과적입니다.', tag: '추천' },
            { id: 7, name: '플랭크 (Plank)', url: 'https://www.youtube.com/results?search_query=플랭크+자세', desc: '전신 코어의 안정성을 높이고 자세를 교정해줍니다.', tag: '코어' },
            { id: 8, name: '바이시클 크런치', url: 'https://www.youtube.com/results?search_query=바이시클+크런치+자세', desc: '외복사근을 자극하여 슬림한 허리 라인을 만듭니다.', tag: '유산소' }
        ],
        '하체': [
            { id: 9, name: '스쿼트 (Squat)', url: 'https://www.youtube.com/results?search_query=스쿼트+자세', desc: '하체 근력의 기초이자 전신 대사량을 높여주는 최고의 운동.', tag: '필수' },
            { id: 10, name: '런지 (Lunge)', url: 'https://www.youtube.com/results?search_query=런지+자세', desc: '하체의 균형 감각을 높이고 엉덩이 근육을 탄력 있게 만듭니다.', tag: '기초' },
            { id: 11, name: '데드리프트 (Deadlift)', url: 'https://www.youtube.com/results?search_query=데드리프트+자세', desc: '뒷면 사슬 근육 전체를 강화하여 폭발적인 힘을 냅니다.', tag: '고강도' },
            { id: 12, name: '레그 프레스 (Leg Press)', url: 'https://www.youtube.com/results?search_query=레그프레스+자세', desc: '허리에 무리 없이 허벅지 근육을 안전하게 강화합니다.', tag: '안전' }
        ]
    };

    useEffect(() => {
        const params = new URLSearchParams(location.search);
        const cat = params.get('cat');
        if (cat && EXERCISE_GUIDES[cat]) {
            setActiveCategory(cat);
        }
    }, [location]);

    return (
        <div className="main-content fade-in">
            <header className="dashboard-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                    <div className="icon-badge" style={{ background: '#e0e7ff', color: '#4f46e5', padding: '8px', borderRadius: '12px' }}>
                        <Dumbbell size={24} />
                    </div>
                    <h1 style={{ margin: 0 }}>운동법 가이드</h1>
                </div>
                <p>전문가가 추천하는 부위별 정확한 운동법을 확인하세요.</p>
            </header>

            <div className="category-tabs-container">
                <div className="category-tabs">
                    {Object.keys(EXERCISE_GUIDES).map(cat => (
                        <button
                            key={cat}
                            className={`tab-item ${activeCategory === cat ? 'active' : ''}`}
                            onClick={() => setActiveCategory(cat)}
                        >
                            {cat === '상체' && <Zap size={16} />}
                            {cat === '복근' && <Shield size={16} />}
                            {cat === '하체' && <Activity size={16} />}
                            <span>{cat}</span>
                        </button>
                    ))}
                </div>
            </div>

            <div className="exercise-grid">
                {EXERCISE_GUIDES[activeCategory].map((ex, index) => (
                    <a
                        key={ex.id}
                        href={ex.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="guide-card fade-in"
                        style={{ animationDelay: `${index * 0.1}s` }}
                    >
                        <div className="guide-card-header">
                            <span className="tag-badge">{ex.tag}</span>
                            <div className="youtube-badge">
                                <Youtube size={18} />
                                <span>가이드 보기</span>
                            </div>
                        </div>
                        <h3 className="exercise-name">{ex.name}</h3>
                        <p className="exercise-desc">{ex.desc}</p>
                        <div className="guide-card-footer">
                            <span className="learn-more">자세히 알아보기</span>
                            <ChevronRight size={16} />
                        </div>
                    </a>
                ))}
            </div>

            <style>{`
                .category-tabs-container {
                    margin-bottom: 24px;
                    overflow-x: auto;
                    padding-bottom: 8px;
                    -webkit-overflow-scrolling: touch;
                }
                .category-tabs {
                    display: flex;
                    gap: 12px;
                    min-width: max-content;
                }
                .tab-item {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    padding: 12px 24px;
                    background: white;
                    border: 1px solid #e2e8f0;
                    border-radius: 16px;
                    color: #64748b;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                }
                .tab-item.active {
                    background: #4f46e5;
                    color: white;
                    border-color: #4f46e5;
                    box-shadow: 0 8px 16px rgba(79, 70, 229, 0.2);
                    transform: translateY(-2px);
                }
                .exercise-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                    gap: 20px;
                }
                .guide-card {
                    background: white;
                    padding: 24px;
                    border-radius: 24px;
                    border: 1px solid #e2e8f0;
                    text-decoration: none;
                    color: inherit;
                    display: flex;
                    flex-direction: column;
                    transition: all 0.3s ease;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.02);
                }
                .guide-card:hover {
                    transform: translateY(-8px);
                    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.08);
                    border-color: #cbd5e1;
                }
                .guide-card-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 16px;
                }
                .tag-badge {
                    padding: 4px 10px;
                    background: #f1f5f9;
                    color: #475569;
                    border-radius: 10px;
                    font-size: 0.75rem;
                    font-weight: 700;
                }
                .youtube-badge {
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    color: #ef4444;
                    font-size: 0.8rem;
                    font-weight: 600;
                }
                .exercise-name {
                    margin: 0 0 8px 0;
                    font-size: 1.2rem;
                    font-weight: 800;
                    color: #1e293b;
                }
                .exercise-desc {
                    margin: 0;
                    font-size: 0.9rem;
                    color: #64748b;
                    line-height: 1.5;
                    flex: 1;
                    margin-bottom: 20px;
                }
                .guide-card-footer {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding-top: 16px;
                    border-top: 1px solid #f1f5f9;
                    color: #4f46e5;
                    font-weight: 700;
                    font-size: 0.9rem;
                }
                @media (max-width: 768px) {
                    .exercise-grid {
                        grid-template-columns: 1fr;
                    }
                    .tab-item {
                        padding: 10px 18px;
                        font-size: 0.9rem;
                    }
                }
            `}</style>
        </div>
    );
};

export default ExerciseGuide;
