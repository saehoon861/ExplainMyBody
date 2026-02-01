import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Dumbbell, Youtube, ChevronRight, Activity, Zap, Shield, X } from 'lucide-react';
import '../../styles/AppLight.css';

const ExerciseGuide = () => {
    const [activeCategory, setActiveCategory] = useState('상체');
    const [activeVideo, setActiveVideo] = useState(null);
    const location = useLocation();

    // 각 운동별 유튜브 영상 ID 매핑 (실제 운동 가이드 영상)
    const EXERCISE_GUIDES = {
        '상체': [
            { id: 1, name: '팔굽혀펴기 (Push-up)', videoId: 'IODxDxX7oi4', desc: '가슴, 어깨, 삼두근을 동시에 강화하는 최고의 맨몸 운동입니다.', tag: '기초' },
            { id: 2, name: '턱걸이 (Pull-up)', videoId: 'eGo4IYlbE5g', desc: '넓은 등과 강한 팔을 만드는 상체 운동의 꽃입니다.', tag: '상급' },
            { id: 3, name: '랫 풀다운 (Lat Pull Down)', videoId: 'CAwf7n6Luuc', desc: '등 근육의 너비를 조절하고 광배근을 발달시킵니다.', tag: '추천' },
            { id: 4, name: '숄더 프레스 (Shoulder Press)', videoId: 'qEwKCR5JCog', desc: '탄탄하고 넓은 어깨 라인을 만드는 필수 종목입니다.', tag: '필수' }
        ],
        '복근': [
            { id: 5, name: '크런치 (Crunch)', videoId: 'Xyd_fa5zoEU', desc: '상복부를 집중적으로 타격하여 복근 라인을 선명하게 만듭니다.', tag: '기초' },
            { id: 6, name: '레그 레이즈 (Leg Raise)', videoId: 'JB2oyawG9KI', desc: '하복부와 코어 하부 근력을 강화하는 데 효과적입니다.', tag: '추천' },
            { id: 7, name: '플랭크 (Plank)', videoId: 'ASdvN_XEl_c', desc: '전신 코어의 안정성을 높이고 자세를 교정해줍니다.', tag: '코어' },
            { id: 8, name: '바이시클 크런치', videoId: 'Iwyvozckjak', desc: '외복사근을 자극하여 슬림한 허리 라인을 만듭니다.', tag: '유산소' }
        ],
        '하체': [
            { id: 9, name: '스쿼트 (Squat)', videoId: 'aclHkVaku9U', desc: '하체 근력의 기초이자 전신 대사량을 높여주는 최고의 운동.', tag: '필수' },
            { id: 10, name: '런지 (Lunge)', videoId: 'QOVaHwm-Q6U', desc: '하체의 균형 감각을 높이고 엉덩이 근육을 탄력 있게 만듭니다.', tag: '기초' },
            { id: 11, name: '데드리프트 (Deadlift)', videoId: 'op9kVnSso6Q', desc: '뒷면 사슬 근육 전체를 강화하여 폭발적인 힘을 냅니다.', tag: '고강도' },
            { id: 12, name: '레그 프레스 (Leg Press)', videoId: 'IZxyjW7MPJQ', desc: '허리에 무리 없이 허벅지 근육을 안전하게 강화합니다.', tag: '안전' }
        ]
    };

    useEffect(() => {
        const params = new URLSearchParams(location.search);
        const cat = params.get('cat');
        if (cat && EXERCISE_GUIDES[cat]) {
            setActiveCategory(cat);
        }
    }, [location]);

    const openVideo = (exercise) => {
        setActiveVideo({
            id: exercise.videoId,
            title: exercise.name
        });
    };

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
                    <div
                        key={ex.id}
                        className="guide-card fade-in"
                        style={{ animationDelay: `${index * 0.1}s`, cursor: 'pointer' }}
                        onClick={() => openVideo(ex)}
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
                    </div>
                ))}
            </div>

            {/* 비디오 팝업 모달 */}
            {activeVideo && (
                <div className="video-modal-overlay fade-in" onClick={() => setActiveVideo(null)}>
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

                /* Video Modal Styles */
                .video-modal-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0, 0, 0, 0.7);
                    backdrop-filter: blur(8px);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 99999;
                    padding: 20px;
                }
                .video-modal-card {
                    background: #111;
                    border-radius: 20px;
                    width: 100%;
                    max-width: 800px;
                    overflow: hidden;
                    box-shadow: 0 25px 50px rgba(0,0,0,0.5);
                    animation: zoomIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
                }
                .video-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 16px 24px;
                    background: #1a1a1a;
                    border-bottom: 1px solid #333;
                }
                .video-header h3 {
                    margin: 0;
                    color: white;
                    font-size: 1.1rem;
                    font-weight: 600;
                }
                .close-button {
                    background: rgba(255,255,255,0.1);
                    border: none;
                    color: #aaa;
                    cursor: pointer;
                    padding: 8px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.2s;
                }
                .close-button:hover {
                    background: rgba(255,255,255,0.2);
                    color: white;
                    transform: rotate(90deg);
                }
                .video-container {
                    aspect-ratio: 16 / 9;
                    width: 100%;
                    overflow: hidden;
                    background: black;
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
                @keyframes zoomIn {
                    from { transform: scale(0.9); opacity: 0; }
                    to { transform: scale(1); opacity: 1; }
                }

                @media (max-width: 768px) {
                    .exercise-grid {
                        grid-template-columns: 1fr;
                    }
                    .tab-item {
                        padding: 12px 20px;
                        font-size: 0.95rem;
                    }
                    .guide-card {
                        padding: 20px;
                    }
                    .exercise-name {
                        font-size: 1.15rem;
                    }
                    .exercise-desc {
                        font-size: 0.95rem;
                    }
                    .video-modal-card {
                        max-width: 95%;
                    }
                }
                @media (max-width: 480px) {
                    .tab-item {
                        padding: 10px 16px;
                        font-size: 0.9rem;
                    }
                    .guide-card {
                        padding: 18px;
                    }
                    .exercise-name {
                        font-size: 1.1rem;
                    }
                    .youtube-badge {
                        font-size: 0.75rem;
                    }
                }
            `}</style>
        </div>
    );
};

export default ExerciseGuide;
