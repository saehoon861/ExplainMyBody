import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, Image as ImageIcon, Check, CheckCircle, ArrowRight, ArrowLeft, AlertCircle, Target, Activity, Loader2, User, Clock, Ruler, Info, Home, RefreshCw, Camera } from 'lucide-react';
import './LoginLight.css';

const InBodyAnalysis = () => {
    const [inbodyImage, setInbodyImage] = useState(null);
    const [inbodyData, setInbodyData] = useState(null);
    const [imagePreview, setImagePreview] = useState(null);
    const [isProcessingOCR, setIsProcessingOCR] = useState(false);
    const [loadingMessage, setLoadingMessage] = useState('인바디 리포트를 읽어오는 중입니다...');
    const [reportSlideIndex, setReportSlideIndex] = useState(0);
    const [errors, setErrors] = useState({});
    const [touchStart, setTouchStart] = useState(null);
    const [touchEnd, setTouchEnd] = useState(null);
    const navigate = useNavigate();

    const minSwipeDistance = 50;

    const onTouchStart = (e) => {
        setTouchEnd(null);
        setTouchStart(e.targetTouches[0].clientX);
    };

    const onTouchMove = (e) => {
        setTouchEnd(e.targetTouches[0].clientX);
    };

    const onTouchEnd = () => {
        if (!touchStart || !touchEnd) return;
        const distance = touchStart - touchEnd;
        const isLeftSwipe = distance > minSwipeDistance;
        const isRightSwipe = distance < -minSwipeDistance;

        if (isLeftSwipe && reportSlideIndex < reportSlides.length - 1) {
            setReportSlideIndex(prev => prev + 1);
        } else if (isRightSwipe && reportSlideIndex > 0) {
            setReportSlideIndex(prev => prev - 1);
        }
    };

    const motivationalQuotes = [
        "오늘의 땀은 내일의 보상입니다. 💪",
        "운동은 몸뿐만 아니라 마음도 치유합니다. ✨",
        "천천히 가더라도 멈추지 마세요. 🏃‍♂️",
        "건강한 몸에 건강한 정신이 깃듭니다. 🧠",
        "나를 위한 투자는 절대 배신하지 않습니다. 🔥",
        "가장 어려운 것은 시작하는 것입니다. 당신은 이미 해냈습니다! 👏",
        "당신의 변화가 누군가에게는 새로운 동기부여가 됩니다. 🌟",
        "몸을 돌보세요. 그곳은 당신이 살아야 할 유일한 장소입니다. 🏠",
        "어제보다 건강한 오늘의 나를 응원합니다! 😊",
        "지방은 타오르고, 자신감은 차오릅니다. 💥"
    ];

    const reportSlides = [
        { title: "체성분 분석", key: "체성분", units: { "체수분": "L", "단백질": "kg", "무기질": "kg", "체지방": "kg" } },
        { title: "골격근·지방분석", key: "체중관리", units: { "체중": "kg", "골격근량": "kg", "체지방량": "kg", "적정체중": "kg", "체중조절": "kg", "지방조절": "kg", "근육조절": "kg" } },
        { title: "비만분석", key: "비만분석", units: { "BMI": "kg/m²", "체지방률": "%", "복부지방률": "%", "내장지방레벨": "lv", "비만도": "%" } },
        { title: "연구항목", key: "연구항목", units: { "제지방량": "kg", "기초대사량": "kcal", "권장섭취열량": "kcal" } },
        { title: "부위별 근육", key: "부위별근육분석" },
        { title: "부위별 체지방", key: "부위별체지방분석" }
    ];

    const [ocrProgress, setOcrProgress] = useState(0);

    React.useEffect(() => {
        let progressInterval;
        if (isProcessingOCR) {
            setOcrProgress(0);
            progressInterval = setInterval(() => {
                setOcrProgress(prev => {
                    if (prev >= 95) return prev;
                    const increment = Math.random() * 15;
                    return Math.min(prev + increment, 95);
                });
            }, 800);
        } else {
            setOcrProgress(0);
        }
        return () => clearInterval(progressInterval);
    }, [isProcessingOCR]);

    React.useEffect(() => {
        let interval;
        if (isProcessingOCR) {
            let index = 0;
            // 초기 메시지 설정 로직은 남겨두되, 100% 시 별도 처리를 위해 render 부분에서 제어
            interval = setInterval(() => {
                index = (index + 1) % motivationalQuotes.length;
                setLoadingMessage(motivationalQuotes[index]);
            }, 2500);
        }
        return () => clearInterval(interval);
    }, [isProcessingOCR]);

    const handleImageUpload = (e) => {
        const file = e.target.files[0];
        if (file) {
            if (!file.type.startsWith('image/')) {
                setErrors({ image: '이미지 파일만 업로드 가능합니다' });
                return;
            }

            setInbodyImage(file);
            setInbodyData(null);
            setErrors({});

            const reader = new FileReader();
            reader.onloadend = () => {
                setImagePreview(reader.result);
            };
            reader.readAsDataURL(file);
        }
    };

    const processOCR = async () => {
        if (!inbodyImage) return;

        setIsProcessingOCR(true);
        setOcrProgress(0);
        setErrors({});

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 180000);

        try {
            const apiFormData = new FormData();
            apiFormData.append('image', inbodyImage);

            const response = await fetch('/api/health-records/ocr/extract', {
                method: 'POST',
                body: apiFormData,
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'OCR 처리 중 오류가 발생했습니다.');
            }

            const result = await response.json();
            if (result.data) {
                setOcrProgress(100);
                setTimeout(() => {
                    setInbodyData(result.data);
                    setIsProcessingOCR(false);
                }, 500);
            } else {
                throw new Error(result.error || '필드 추출에 실패했습니다.');
            }
        } catch (err) {
            clearTimeout(timeoutId);
            console.error('OCR Error:', err);
            if (err.name === 'AbortError') {
                setErrors({ ocr: '요청 시간이 초과되었습니다. 다시 시도해주세요.' });
            } else {
                setErrors({ ocr: err.message || 'OCR 처리 중 오류가 발생했습니다.' });
            }
        } finally {
            if (errors.ocr) setIsProcessingOCR(false);
        }
    };

    const handleInbodyFieldChange = (category, field, value) => {
        setInbodyData(prev => ({
            ...prev,
            [category]: {
                ...prev[category],
                [field]: value
            }
        }));
    };

    const renderInbodyTable = (title, categoryKey, unitMap = {}) => {
        const categoryData = inbodyData?.[categoryKey];
        if (!categoryData) return null;

        return (
            <div className="report-section" key={categoryKey}>
                <div className="section-header">
                    <span className="section-bullet"></span>
                    <h4>{title}</h4>
                </div>
                <div className="report-table">
                    <div className="table-header">
                        <div className="header-cell">항목</div>
                        <div className="header-cell">결과값</div>
                        <div className="header-cell">단위</div>
                    </div>
                    {Object.entries(categoryData).map(([field, value]) => (
                        <div className="table-row" key={field}>
                            <div className="row-label">{field}</div>
                            <div className="row-value">
                                <input
                                    type="text"
                                    value={value || ''}
                                    placeholder="-"
                                    onChange={(e) => handleInbodyFieldChange(categoryKey, field, e.target.value)}
                                />
                            </div>
                            <div className="row-unit">{unitMap[field] || ''}</div>
                        </div>
                    ))}
                </div>
            </div>
        );
    };

    return (
        <div className="login-container">
            <div className="login-card signup-card">
                <div className="login-header" style={{ marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h1>InBody Analysis</h1>
                        <p>AI가 분석하는 나의 건강 리포트</p>
                    </div>
                    <button
                        className="secondary-button compact"
                        onClick={() => navigate('/dashboard')}
                        style={{ width: 'auto', padding: '8px 16px' }}
                    >
                        <Home size={18} />
                        대시보드
                    </button>
                </div>

                <div className="step-content fade-in report-view">
                    <div className="form-group">
                        {!inbodyData && !isProcessingOCR && (
                            <div className={`upload-area ${imagePreview ? 'minimized' : ''}`}>
                                {!imagePreview ? (
                                    <label htmlFor="file-upload" className="upload-label">
                                        <ImageIcon size={48} />
                                        <p>인바디 사진을 업로드하세요</p>
                                        <span className="upload-hint">JPG, PNG 파일 지원</span>
                                        <input
                                            id="file-upload"
                                            type="file"
                                            accept="image/*"
                                            onChange={handleImageUpload}
                                            style={{ display: 'none' }}
                                        />
                                    </label>
                                ) : (
                                    <div className="image-preview simplified">
                                        <div className="upload-status-compact">
                                            <CheckCircle size={20} color="#7dd3fc" />
                                            <span>사진 준비 완료</span>
                                        </div>
                                        <div className="preview-image-container">
                                            <img src={imagePreview} alt="Inbody Preview" />
                                        </div>
                                        <div className="image-actions">
                                            <button
                                                type="button"
                                                className="secondary-button compact"
                                                onClick={() => {
                                                    setImagePreview(null);
                                                    setInbodyImage(null);
                                                    setInbodyData(null);
                                                }}
                                                disabled={isProcessingOCR}
                                            >
                                                재선택
                                            </button>
                                            <button
                                                type="button"
                                                className="primary-button compact"
                                                onClick={processOCR}
                                                style={{ marginTop: 0 }}
                                                disabled={isProcessingOCR}
                                            >
                                                분석 시작
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {inbodyData && (
                            <button
                                type="button"
                                className="ghost-button"
                                style={{ marginBottom: '16px', borderRadius: '12px' }}
                                onClick={() => {
                                    setInbodyData(null);
                                    setImagePreview(null);
                                    setInbodyImage(null);
                                }}
                            >
                                <Camera size={16} />
                                다시 찍기
                            </button>
                        )}
                        {errors.image && <div className="error-message">{errors.image}</div>}
                    </div>

                    {isProcessingOCR && (
                        <div className="ocr-processing-container fade-in">
                            <div className="pushup-loader">
                                <div className="character">
                                    <div className="head"></div>
                                    <div className="body">
                                        <div className="arm arm-l"></div>
                                        <div className="arm arm-r"></div>
                                    </div>
                                    <div className="leg leg-l"></div>
                                    <div className="leg leg-r"></div>
                                </div>
                                <div className="ground"></div>
                            </div>

                            <div className="progress-status-container">
                                <div className={`progress-percentage ${ocrProgress === 100 ? 'complete' : ''}`}>
                                    {ocrProgress === 100 ? '분석 완료!' : `${Math.round(ocrProgress)}%`}
                                </div>
                                <div className="progress-bar-wrapper">
                                    <div
                                        className={`progress-bar-fill ${ocrProgress === 100 ? 'complete' : ''}`}
                                        style={{ width: `${ocrProgress}%` }}
                                    ></div>
                                </div>
                                <p className="loading-quote">
                                    {ocrProgress === 100 ? '당신의 몸을 완벽하게 분석했습니다. ✨' : loadingMessage}
                                </p>
                                <span className="processing-hint">
                                    {ocrProgress === 100 ? '잠시 후 리포트가 공개됩니다!' : '인바디 리포트를 인공지능이 근육을 키워가며(?) 분석 중입니다...'}
                                </span>
                            </div>
                        </div>
                    )}

                    {errors.ocr && <div className="error-message report-error"><AlertCircle size={20} /> {errors.ocr}</div>}

                    {inbodyData && (
                        <div className="inbody-report-container fade-in">
                            <div className="report-header-main">
                                <div className="report-title-row">
                                    <div className="title-group">
                                        <h2>InBody <span>Results</span></h2>
                                        <div className="report-badge">인바디 성적표</div>
                                    </div>
                                </div>
                                <div className="basic-info-grid">
                                    <div className="info-cell">
                                        <User size={14} />
                                        <span className="label">성별</span>
                                        <input
                                            value={inbodyData?.["기본정보"]?.["성별"] || ""}
                                            onChange={(e) => handleInbodyFieldChange("기본정보", "성별", e.target.value)}
                                        />
                                    </div>
                                    <div className="info-cell">
                                        <Ruler size={14} />
                                        <span className="label">신장</span>
                                        <input
                                            value={inbodyData?.["기본정보"]?.["신장"] || ""}
                                            onChange={(e) => handleInbodyFieldChange("기본정보", "신장", e.target.value)}
                                        />
                                        <span className="unit">cm</span>
                                    </div>
                                    <div className="info-cell">
                                        <Clock size={14} />
                                        <span className="label">연령</span>
                                        <input
                                            value={inbodyData?.["기본정보"]?.["연령"] || ""}
                                            onChange={(e) => handleInbodyFieldChange("기본정보", "연령", e.target.value)}
                                        />
                                        <span className="unit">세</span>
                                    </div>
                                </div>
                            </div>

                            <div
                                className="report-carousel-container"
                                onTouchStart={onTouchStart}
                                onTouchMove={onTouchMove}
                                onTouchEnd={onTouchEnd}
                            >
                                <div className="carousel-nav-header">
                                    <button
                                        type="button"
                                        className="slide-nav-btn"
                                        disabled={reportSlideIndex === 0}
                                        onClick={() => setReportSlideIndex(prev => prev - 1)}
                                    >
                                        <ArrowLeft size={18} />
                                    </button>
                                    <div className="slide-dots">
                                        <div
                                            className="active-indicator"
                                            style={{
                                                transform: `translateX(${reportSlideIndex * 21}px)`
                                            }}
                                        ></div>
                                        {reportSlides.map((_, idx) => (
                                            <div
                                                key={idx}
                                                className={`dot ${reportSlideIndex === idx ? 'active' : ''}`}
                                                onClick={() => setReportSlideIndex(idx)}
                                            ></div>
                                        ))}
                                    </div>
                                    <button
                                        type="button"
                                        className="slide-nav-btn"
                                        disabled={reportSlideIndex === reportSlides.length - 1}
                                        onClick={() => setReportSlideIndex(prev => prev + 1)}
                                    >
                                        <ArrowRight size={18} />
                                    </button>
                                </div>

                                <div className="slide-content-wrapper" key={reportSlideIndex}>
                                    {reportSlideIndex >= 4 ? (
                                        <div className="fade-in">
                                            {renderInbodyTable(
                                                reportSlides[reportSlideIndex].title === "부위별 근육" ? "부위별 근육 분석" : "부위별 체지방 분석",
                                                reportSlides[reportSlideIndex].key
                                            )}
                                        </div>
                                    ) : reportSlideIndex === 3 ? (
                                        <div className="report-section fade-in">
                                            <div className="section-header">
                                                <span className="section-bullet"></span>
                                                <h4>{reportSlides[reportSlideIndex].title}</h4>
                                            </div>
                                            <div className="report-table">
                                                <div className="table-header">
                                                    <div className="header-cell">항목</div>
                                                    <div className="header-cell">결과값</div>
                                                    <div className="header-cell">단위</div>
                                                </div>
                                                {inbodyData?.[reportSlides[reportSlideIndex].key] && Object.entries(inbodyData[reportSlides[reportSlideIndex].key])
                                                    .filter(([key]) => key !== "인바디점수")
                                                    .map(([field, value]) => (
                                                        <div className="table-row" key={field}>
                                                            <div className="row-label">{field}</div>
                                                            <div className="row-value">
                                                                <input
                                                                    type="text"
                                                                    value={value || ''}
                                                                    placeholder="-"
                                                                    onChange={(e) => handleInbodyFieldChange(reportSlides[reportSlideIndex].key, field, e.target.value)}
                                                                />
                                                            </div>
                                                            <div className="row-unit">{reportSlides[reportSlideIndex].units[field] || ''}</div>
                                                        </div>
                                                    ))}
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="fade-in">
                                            {renderInbodyTable(
                                                reportSlides[reportSlideIndex].title,
                                                reportSlides[reportSlideIndex].key,
                                                reportSlides[reportSlideIndex].units
                                            )}
                                        </div>
                                    )}
                                </div>
                            </div>

                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default InBodyAnalysis;
