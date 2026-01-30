import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Dumbbell, Youtube, ChevronRight, ArrowUp, Circle, ArrowDown, X, Play } from 'lucide-react';
import '../AppLight.css';

const ExerciseGuide = () => {
    const [activeCategory, setActiveCategory] = useState(null);
    const [selectedVideo, setSelectedVideo] = useState(null);
    const location = useLocation();

    // 조회수가 매우 높고(수백만~수천만) 임베드가 허용된 대한민국 대표 운동 영상들
    const EXERCISE_GUIDES = {
        '상체': [
            { id: 1, name: '팔굽혀펴기 (Push-up)', videoId: 'VoOkoXNEi9c', desc: '피지컬갤러리의 과학적으로 검증된 완벽한 푸쉬업 자세입니다.', tag: '필수' },
            { id: 2, name: '턱걸이 (Pull-up)', videoId: '3U9Yv39ca_A', desc: '초보자도 턱걸이 개수를 늘리는 가장 확실한 방법입니다.', tag: '상급' },
            { id: 3, name: '렛풀다운 (Lat Pull Down)', videoId: 'Y7B2jJ_LdO0', desc: '등 근육의 너비를 조절하고 광배근을 발달시키는 핵심 정격 자세입니다.', tag: '추천' },
            { id: 4, name: '숄더 프레스 (Shoulder Press)', videoId: 'pS-WJny504U', desc: '탄탄하고 넓은 어깨 라인을 만드는 필수 어깨 운동 강의입니다.', tag: '추천' }
        ],
        '복근': [
            { id: 1, name: '크런치 (Crunch)', videoId: '57j88vXyVmc', desc: '상복부를 집중적으로 타격하여 선명한 복근을 만듭니다.', tag: '기초' },
            { id: 2, name: '레그 레이즈 (Leg Raise)', videoId: 'r_L85k_N9A0', desc: '조회수 2천만의 신화! 아랫배 뱃살을 빼는 최강의 하복부 운동입니다.', tag: '필수' },
            { id: 3, name: '플랭크 (Plank)', videoId: 'Zq8nRY9P_No', desc: '심으뜸의 10분 플랭크 챌린지! 전신 코어의 기본이자 완성입니다.', tag: '필수' },
            { id: 4, name: '바이시클 크런치 (Bicycle Crunch)', videoId: '9vS2m9AAnSg', desc: '복부 전체와 옆구리를 동시에 자극하는 고효율 유산소성 복근 운동입니다.', tag: '도전' }
        ],
        '하체': [
            { id: 1, name: '스쿼트 (Squat)', videoId: 'bEv6Tqoz87g', desc: '조회수 1,300만! 하체 운동의 왕, 스쿼트의 정석 자세를 마스터하세요.', tag: '왕강추' },
            { id: 2, name: '런지 (Lunge)', videoId: 'Uv_Mst5nN2M', desc: '엉덩이와 허벅지 라인을 살려주는 최고의 하체 루틴입니다.', tag: '강력추천' },
            { id: 3, name: '데드리프트 (Deadlift)', videoId: 'R9j0D_Lw-vA', desc: '전신 근력 향상의 꽃, 정석 데드리프트 완벽 강의입니다.', tag: '상급' },
            { id: 4, name: '레그 프레스 (Leg Press)', videoId: '9Y4vH1-E-Xg', desc: '안전하게 고중량 하체 훈련을 할 수 있는 레그 프레스 활용법입니다.', tag: '추천' }
        ]
    };

    useEffect(() => {
        const params = new URLSearchParams(location.search);
        const cat = params.get('cat');
        if (cat && EXERCISE_GUIDES[cat]) {
            setActiveCategory(cat);
        } else {
            setActiveCategory(null);
        }
    }, [location]);

    const openVideo = (exercise) => {
        setSelectedVideo(exercise);
        document.body.style.overflow = 'hidden';
    };

    const closeVideo = () => {
        setSelectedVideo(null);
        document.body.style.overflow = 'auto';
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

            {!activeCategory ? (
                <div className="quick-actions-grid fade-in">
                    <div className="action-card" onClick={() => setActiveCategory('상체')}>
                        <div className="icon-box" style={{ background: '#eef2ff', color: '#6366f1' }}>
                            <ArrowUp size={24} />
                        </div>
                        <div className="text-box">
                            <h3>상체 루틴</h3>
                            <p>어깨, 가슴, 등, 팔 운동 가이드</p>
                        </div>
                    </div>
                    <div className="action-card" onClick={() => setActiveCategory('복근')}>
                        <div className="icon-box" style={{ background: '#fff1f2', color: '#f43f5e' }}>
                            <Circle size={24} />
                        </div>
                        <div className="text-box">
                            <h3>복부 & 코어</h3>
                            <p>식스팩과 탄탄한 코어 집중 강화</p>
                        </div>
                    </div>
                    <div className="action-card" onClick={() => setActiveCategory('하체')}>
                        <div className="icon-box" style={{ background: '#f0fdf4', color: '#22c55e' }}>
                            <ArrowDown size={24} />
                        </div>
                        <div className="text-box">
                            <h3>하체 루틴</h3>
                            <p>하체 대근육과 둔근 강화 가이드</p>
                        </div>
                    </div>
                </div>
            ) : (
                <>
                    <div className="category-tabs-container">
                        <div className="category-tabs">
                            <button
                                className="tab-item"
                                onClick={() => setActiveCategory(null)}
                                style={{ background: '#f1f5f9', color: '#64748b' }}
                            >
                                <ChevronRight size={16} style={{ transform: 'rotate(180deg)' }} />
                                <span>전체 메뉴</span>
                            </button>
                            {Object.keys(EXERCISE_GUIDES).map(cat => (
                                <button
                                    key={cat}
                                    className={`tab-item ${activeCategory === cat ? 'active' : ''}`}
                                    onClick={() => setActiveCategory(cat)}
                                >
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
                                    <span className="learn-more">영상으로 배우기</span>
                                    <Play size={16} fill="currentColor" />
                                </div>
                            </div>
                        ))}
                    </div>
                </>
            )}

            {/* Video Modal Popup */}
            {selectedVideo && (
                <div className="video-modal-overlay fade-in" onClick={closeVideo}>
                    <div className="video-modal-card" onClick={e => e.stopPropagation()}>
                        <div className="video-modal-header">
                            <h3>{selectedVideo.name}</h3>
                            <button className="close-btn" onClick={closeVideo}>
                                <X size={24} />
                            </button>
                        </div>
                        <div className="video-container">
                            <iframe
                                width="100%"
                                height="100%"
                                src={`https://www.youtube.com/embed/${selectedVideo.videoId}?autoplay=1&rel=0&modestbranding=1&origin=${window.location.origin}`}
                                title={selectedVideo.name}
                                frameBorder="0"
                                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                                allowFullScreen
                            ></iframe>
                        </div>
                        <div className="video-info">
                            <p>{selectedVideo.desc}</p>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div className="channel-info">
                                    <div className="channel-avatar">EMB</div>
                                    <span>ExplainMyBody 추천 가이드</span>
                                </div>
                                <a
                                    href={`https://youtu.be/${selectedVideo.videoId}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="fallback-link"
                                    style={{
                                        fontSize: '0.85rem',
                                        color: '#ef4444',
                                        fontWeight: 700,
                                        textDecoration: 'none',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '4px',
                                        padding: '8px 16px',
                                        background: '#fff1f2',
                                        borderRadius: '12px'
                                    }}
                                >
                                    <Youtube size={16} />
                                    YouTube에서 직접 보기
                                </a>
                            </div>
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

                .video-modal-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0, 0, 0, 0.85);
                    backdrop-filter: blur(10px);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 9999;
                    padding: 20px;
                }
                .video-modal-card {
                    background: white;
                    border-radius: 32px;
                    width: 100%;
                    max-width: 900px;
                    overflow: hidden;
                    animation: modalSlideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1);
                    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
                }
                .video-modal-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 20px 32px;
                    background: white;
                    border-bottom: 1px solid #f1f5f9;
                }
                .video-modal-header h3 {
                    margin: 0;
                    font-size: 1.25rem;
                    font-weight: 800;
                    color: #1e293b;
                }
                .close-btn {
                    background: none;
                    border: none;
                    color: #64748b;
                    cursor: pointer;
                    padding: 8px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.2s;
                }
                .close-btn:hover {
                    background: #f1f5f9;
                    color: #ef4444;
                    transform: rotate(90deg);
                }
                .video-container {
                    position: relative;
                    padding-bottom: 56.25%; 
                    height: 0;
                    background: black;
                }
                .video-container iframe {
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                }
                .video-info {
                    padding: 24px 32px;
                }
                .video-info p {
                    margin: 0 0 20px 0;
                    color: #475569;
                    font-size: 1rem;
                    line-height: 1.6;
                }
                .channel-info {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }
                .channel-avatar {
                    width: 36px;
                    height: 36px;
                    background: #4f46e5;
                    color: white;
                    border-radius: 12px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: 800;
                    font-size: 0.75rem;
                }
                .channel-info span {
                    font-weight: 700;
                    color: #1e293b;
                    font-size: 0.95rem;
                }

                @keyframes modalSlideUp {
                    from { transform: translateY(40px); opacity: 0; }
                    to { transform: translateY(0); opacity: 1; }
                }

                @media (max-width: 768px) {
                    .exercise-grid {
                        grid-template-columns: 1fr;
                    }
                    .tab-item {
                        padding: 10px 18px;
                        font-size: 0.9rem;
                    }
                    .video-modal-card {
                        border-radius: 20px;
                    }
                    .video-modal-header {
                        padding: 16px 20px;
                    }
                    .video-info {
                        padding: 20px;
                    }
                }
            `}</style>
        </div>
    );
};

export default ExerciseGuide;
