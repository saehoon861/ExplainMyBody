import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Mail, Lock, Upload, Image as ImageIcon, Check, CheckCircle, ArrowRight, ArrowLeft, AlertCircle, Target, Activity, Loader2, User, Clock, Ruler, Info } from 'lucide-react';
import './Login.css';

const Signup = () => {
    const [step, setStep] = useState(1);
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        confirmPassword: '',
        inbodyImage: null,
        inbodyData: null,
        hasMedicalCondition: false,
        medicalConditions: [],
        medicalConditionsDetail: '',
        gender: 'male',
        age: '31',
        height: '170',
        startWeight: '30',
        targetWeight: '58',
        activityLevel: '보통',
        goal: ''
    });
    const [showProfileModal, setShowProfileModal] = useState(false);
    const [errors, setErrors] = useState({});
    const [passwordStrength, setPasswordStrength] = useState('');
    const [imagePreview, setImagePreview] = useState(null);
    const [isProcessingOCR, setIsProcessingOCR] = useState(false);
    const [loadingMessage, setLoadingMessage] = useState('인바디 리포트를 읽어오는 중입니다...');
    const [reportSlideIndex, setReportSlideIndex] = useState(0);
    const [touchStart, setTouchStart] = useState(null);
    const [touchEnd, setTouchEnd] = useState(null);
    const navigate = useNavigate();

    // 스와이프 감지를 위한 최소 거리 (픽셀)
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
        { title: "부위별 분석", key: ["부위별근육분석", "부위별체지방분석"] }
    ];

    React.useEffect(() => {
        let interval;
        if (isProcessingOCR) {
            let index = 0;
            setLoadingMessage(motivationalQuotes[0]);
            interval = setInterval(() => {
                index = (index + 1) % motivationalQuotes.length;
                setLoadingMessage(motivationalQuotes[index]);
            }, 2500);
        }
        return () => clearInterval(interval);
    }, [isProcessingOCR]);

    const validateEmail = (email) => {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    };

    const calculatePasswordStrength = (password) => {
        if (password.length === 0) return '';
        if (password.length < 6) return 'weak';
        if (password.length < 10) return 'medium';
        if (password.length >= 10 && /[A-Z]/.test(password) && /[0-9]/.test(password)) return 'strong';
        return 'medium';
    };

    const handleInputChange = (field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }));
        setErrors(prev => ({ ...prev, [field]: '' }));

        if (field === 'password') {
            setPasswordStrength(calculatePasswordStrength(value));
        }
    };

    const handleInbodyFieldChange = (category, field, value) => {
        setFormData(prev => ({
            ...prev,
            inbodyData: {
                ...prev.inbodyData,
                [category]: {
                    ...prev.inbodyData[category],
                    [field]: value
                }
            }
        }));
    };

    const handleImageUpload = (e) => {
        const file = e.target.files[0];
        if (file) {
            if (!file.type.startsWith('image/')) {
                setErrors({ image: '이미지 파일만 업로드 가능합니다' });
                return;
            }

            setFormData(prev => ({ ...prev, inbodyImage: file, inbodyData: null }));
            setErrors({});

            const reader = new FileReader();
            reader.onloadend = () => {
                setImagePreview(reader.result);
            };
            reader.readAsDataURL(file);
        }
    };

    const processOCR = async () => {
        if (!formData.inbodyImage) return;

        setIsProcessingOCR(true);
        setErrors({});

        try {
            const apiFormData = new FormData();
            apiFormData.append('image', formData.inbodyImage);

            const response = await fetch('http://localhost:8000/api/health-records/ocr/extract', {
                method: 'POST',
                body: apiFormData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'OCR 처리 중 오류가 발생했습니다.');
            }

            const result = await response.json();
            if (result.success) {
                setFormData(prev => ({
                    ...prev,
                    inbodyData: result.data.structured
                }));
            } else {
                throw new Error(result.error || '필드 추출에 실패했습니다.');
            }
        } catch (err) {
            console.error('OCR Error:', err);
            setErrors({ ocr: err.message });
        } finally {
            setIsProcessingOCR(false);
        }
    };

    const handleMedicalConditionToggle = (condition) => {
        setFormData(prev => {
            const conditions = prev.medicalConditions.includes(condition)
                ? prev.medicalConditions.filter(c => c !== condition)
                : [...prev.medicalConditions, condition];
            return { ...prev, medicalConditions: conditions };
        });
    };

    const validateStep1 = () => {
        const newErrors = {};
        if (!formData.email) {
            newErrors.email = '이메일을 입력해주세요';
        } else if (!validateEmail(formData.email)) {
            newErrors.email = '올바른 이메일 형식이 아닙니다';
        }
        if (!formData.password) {
            newErrors.password = '비밀번호를 입력해주세요';
        } else if (formData.password.length < 6) {
            newErrors.password = '비밀번호는 최소 6자 이상이어야 합니다';
        }
        if (!formData.confirmPassword) {
            newErrors.confirmPassword = '비밀번호 확인을 입력해주세요';
        } else if (formData.password !== formData.confirmPassword) {
            newErrors.confirmPassword = '비밀번호가 일치하지 않습니다';
        }
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const validateStep2 = () => {
        if (!formData.inbodyImage) {
            setErrors({ image: '인바디 사진을 업로드해주세요' });
            return false;
        }
        if (!formData.inbodyData) {
            setErrors({ ocr: '인바디 정보를 분석해주세요' });
            return false;
        }
        return true;
    };

    const validateStep3 = () => {
        const newErrors = {};
        if (!formData.goal.trim()) {
            newErrors.goal = '목표를 입력해주세요';
        }
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleNext = async () => {
        if (step === 1 && validateStep1()) {
            setStep(2);
        } else if (step === 2 && validateStep2()) {
            setStep(3);
        }
    };

    const handlePrevious = () => {
        if (step > 1) {
            setStep(step - 1);
        }
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        if (validateStep3()) {
            console.log('Signup data:', formData);
            navigate('/dashboard');
        }
    };

    const getPasswordStrengthClass = () => {
        if (passwordStrength === 'weak') return 'strength-weak';
        if (passwordStrength === 'medium') return 'strength-medium';
        if (passwordStrength === 'strong') return 'strength-strong';
        return '';
    };

    const getPasswordStrengthText = () => {
        if (passwordStrength === 'weak') return '약함';
        if (passwordStrength === 'medium') return '보통';
        if (passwordStrength === 'strong') return '강함';
        return '';
    };

    const medicalConditionsList = [
        '고혈압', '당뇨', '심장 질환', '호흡기 질환', '관절염', '허리 디스크', '기타 근골격계 질환', '기타', '없음'
    ];

    const renderInbodyTable = (title, categoryKey, unitMap = {}) => {
        const categoryData = formData.inbodyData?.[categoryKey];
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
                <div className="login-header">
                    <h1>ExplainMyBody</h1>
                    <p>새로운 계정 만들기</p>
                </div>

                <div className="progress-indicator">
                    <div className={`progress-step ${step >= 1 ? 'active' : ''} ${step > 1 ? 'completed' : ''}`}>
                        <div className="step-number">{step > 1 ? <Check size={16} /> : '1'}</div>
                        <div className="step-label">계정정보</div>
                    </div>
                    <div className={`progress-line ${step > 1 ? 'active' : ''}`}></div>
                    <div className={`progress-step ${step >= 2 ? 'active' : ''} ${step > 2 ? 'completed' : ''}`}>
                        <div className="step-number">{step > 2 ? <Check size={16} /> : '2'}</div>
                        <div className="step-label">인바디</div>
                    </div>
                    <div className={`progress-line ${step > 2 ? 'active' : ''}`}></div>
                    <div className={`progress-step ${step >= 3 ? 'active' : ''}`}>
                        <div className="step-number">3</div>
                        <div className="step-label">목표설정</div>
                    </div>
                </div>

                <form onSubmit={handleSubmit}>
                    <div className="signup-steps">
                        {step === 1 && (
                            <div className="step-content fade-in" key="step1">
                                <div className="form-group">
                                    <label>이메일</label>
                                    <div className="input-wrapper">
                                        <Mail size={20} />
                                        <input
                                            type="email"
                                            placeholder="example@email.com"
                                            value={formData.email}
                                            onChange={(e) => handleInputChange('email', e.target.value)}
                                            autoFocus
                                        />
                                    </div>
                                    {errors.email && <div className="error-message">{errors.email}</div>}
                                </div>

                                <div className="form-group">
                                    <label>비밀번호</label>
                                    <div className="input-wrapper">
                                        <Lock size={20} />
                                        <input
                                            type="password"
                                            placeholder="최소 6자 이상"
                                            value={formData.password}
                                            onChange={(e) => handleInputChange('password', e.target.value)}
                                        />
                                    </div>
                                    {formData.password && (
                                        <div className={`password-strength ${getPasswordStrengthClass()}`}>
                                            비밀번호 강도: {getPasswordStrengthText()}
                                        </div>
                                    )}
                                    {errors.password && <div className="error-message">{errors.password}</div>}
                                </div>

                                <div className="form-group">
                                    <label>비밀번호 확인</label>
                                    <div className="input-wrapper">
                                        <Lock size={20} />
                                        <input
                                            type="password"
                                            placeholder="비밀번호 재입력"
                                            value={formData.confirmPassword}
                                            onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                                        />
                                    </div>
                                    {formData.confirmPassword && formData.password === formData.confirmPassword && (
                                        <div className="success-message">
                                            <Check size={16} /> 비밀번호가 일치합니다
                                        </div>
                                    )}
                                    {errors.confirmPassword && <div className="error-message">{errors.confirmPassword}</div>}
                                </div>
                            </div>
                        )}

                        {step === 2 && (
                            <div className="step-content fade-in report-view" key="step2">
                                <div className="form-group">
                                    {!formData.inbodyData && !isProcessingOCR && (
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
                                                    <div className="image-actions">
                                                        <button
                                                            type="button"
                                                            className="secondary-button compact"
                                                            onClick={() => {
                                                                setImagePreview(null);
                                                                setFormData(prev => ({ ...prev, inbodyImage: null, inbodyData: null }));
                                                            }}
                                                        >
                                                            재선택
                                                        </button>
                                                        <button
                                                            type="button"
                                                            className="primary-button compact"
                                                            onClick={processOCR}
                                                            style={{ marginTop: 0 }}
                                                        >
                                                            분석 시작
                                                        </button>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    )}

                                    {formData.inbodyData && (
                                        <button
                                            type="button"
                                            className="secondary-button compact"
                                            style={{ marginBottom: '16px', width: 'auto' }}
                                            onClick={() => {
                                                setFormData(prev => ({ ...prev, inbodyData: null }));
                                                setImagePreview(null);
                                            }}
                                        >
                                            사진 다시 업로드하기
                                        </button>
                                    )}
                                    {errors.image && <div className="error-message">{errors.image}</div>}
                                </div>

                                {isProcessingOCR && (
                                    <div className="ocr-processing report-style">
                                        <div className="squat-loader">
                                            <div className="squat-head"></div>
                                            <div className="squat-body">
                                                <div className="squat-arms"></div>
                                            </div>
                                            <div className="squat-legs">
                                                <div className="leg"></div>
                                                <div className="leg"></div>
                                            </div>
                                            <div className="squat-shadow"></div>
                                        </div>
                                        <p className="loading-quote">{loadingMessage}</p>
                                        <span className="processing-hint">인바디 리포트를 근육질 AI가 정밀하게 분석하고 있습니다...</span>
                                    </div>
                                )}

                                {errors.ocr && <div className="error-message report-error"><AlertCircle size={20} /> {errors.ocr}</div>}

                                {formData.inbodyData && (
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
                                                        value={formData.inbodyData?.["기본정보"]?.["성별"] || ""}
                                                        onChange={(e) => handleInbodyFieldChange("기본정보", "성별", e.target.value)}
                                                    />
                                                </div>
                                                <div className="info-cell">
                                                    <Ruler size={14} />
                                                    <span className="label">신장</span>
                                                    <input
                                                        value={formData.inbodyData?.["기본정보"]?.["신장"] || ""}
                                                        onChange={(e) => handleInbodyFieldChange("기본정보", "신장", e.target.value)}
                                                    />
                                                    <span className="unit">cm</span>
                                                </div>
                                                <div className="info-cell">
                                                    <Clock size={14} />
                                                    <span className="label">연령</span>
                                                    <input
                                                        value={formData.inbodyData?.["기본정보"]?.["연령"] || ""}
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
                                                {reportSlideIndex === 4 ? (
                                                    <div className="segmental-sections fade-in">
                                                        {renderInbodyTable("부위별 근육 분석", "부위별근육분석")}
                                                        {renderInbodyTable("부위별 체지방 분석", "부위별체지방분석")}
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
                                                            {formData.inbodyData?.[reportSlides[reportSlideIndex].key] && Object.entries(formData.inbodyData[reportSlides[reportSlideIndex].key])
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

                                        <div className="report-notice">
                                            <Info size={16} />
                                            <p>좌우 화살표를 눌러 다른 항목도 확인해 보세요. 항목을 클릭하여 수정할 수 있습니다.</p>
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {step === 3 && (
                            <div className="step-content fade-in" key="step3">
                                <div className="goal-summary-card" onClick={() => setShowProfileModal(true)}>
                                    <div className="card-header">
                                        <div className="card-title">
                                            <div className="icon-bg">
                                                <Target size={20} />
                                            </div>
                                            <span>나의 목표</span>
                                        </div>
                                        <button type="button" className="edit-btn">수정</button>
                                    </div>
                                    <div className="card-stats">
                                        <div className="stat-item">
                                            <span className="stat-label">식단</span>
                                            <span className="stat-value">운동식단</span>
                                        </div>
                                        <div className="stat-item">
                                            <span className="stat-label">목표</span>
                                            <span className="stat-value highlight">{formData.targetWeight} kg</span>
                                        </div>
                                        <div className="stat-item">
                                            <span className="stat-label">변화</span>
                                            <span className="stat-value">-{Math.max(0, parseInt(formData.startWeight || 0) - parseInt(formData.targetWeight || 0))} kg</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="form-group">
                                    <label>
                                        <Activity size={20} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
                                        운동 시 주의가 필요한 질병이 있으신가요?
                                    </label>
                                    <div className="checkbox-grid">
                                        {medicalConditionsList.map((condition) => (
                                            <div
                                                key={condition}
                                                className={`checkbox-item ${formData.medicalConditions.includes(condition) ? 'active' : ''}`}
                                                onClick={() => handleMedicalConditionToggle(condition)}
                                            >
                                                <span>{condition}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {formData.medicalConditions.includes('기타') && (
                                    <div className="form-group fade-in" style={{ marginTop: '20px' }}>
                                        <label>기타 건강 상태를 적어주세요</label>
                                        <textarea
                                            className="goal-textarea"
                                            placeholder="예: 최근 발목 수술을 하여 조깅이 어렵습니다."
                                            value={formData.medicalConditionsDetail}
                                            onChange={(e) => handleInputChange('medicalConditionsDetail', e.target.value)}
                                            rows={2}
                                            style={{ minHeight: '60px' }}
                                        />
                                    </div>
                                )}

                                <div className="form-group">
                                    <label>
                                        <Target size={20} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
                                        운동 목표를 작성해주세요
                                    </label>
                                    <textarea
                                        className="goal-textarea"
                                        placeholder="예: 3개월 안에 체지방 5% 감량하고 근력 향상시키기"
                                        value={formData.goal}
                                        onChange={(e) => handleInputChange('goal', e.target.value)}
                                        rows={4}
                                        autoFocus
                                    />
                                    {errors.goal && <div className="error-message">{errors.goal}</div>}
                                </div>

                                <div className="info-box">
                                    <AlertCircle size={20} />
                                    <p>입력하신 정보는 맞춤형 운동 코칭을 제공하는 데 사용됩니다.</p>
                                </div>
                            </div>
                        )}
                    </div>

                    <div className="button-group">
                        {step > 1 && (
                            <button type="button" className="secondary-button" onClick={handlePrevious}>
                                <ArrowLeft size={20} />
                                이전
                            </button>
                        )}
                        {step < 3 ? (
                            <button type="button" className="login-button" onClick={handleNext}>
                                {step === 2 && !formData.inbodyData ? '분석을 완료해주세요' : '다음'}
                                <ArrowRight size={20} />
                            </button>
                        ) : (
                            <button type="submit" className="login-button">
                                가입 완료
                                <Check size={20} />
                            </button>
                        )}
                    </div>
                </form>

                <div className="login-footer">
                    이미 계정이 있으신가요? <Link to="/">로그인</Link>
                </div>
            </div>

            {showProfileModal && (
                <div className="modal-overlay" onClick={() => setShowProfileModal(false)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <button className="close-modal-btn" onClick={() => setShowProfileModal(false)}>
                            <ArrowLeft size={24} />
                        </button>
                        <div className="modal-header">
                            <h2>기본 프로필을 먼저 확인해 주세요</h2>
                        </div>

                        <div className="profile-fields-list">
                            <div className="profile-field-row">
                                <span className="field-label">성별</span>
                                <div className="field-value-controls">
                                    <select
                                        value={formData.gender}
                                        onChange={(e) => handleInputChange('gender', e.target.value)}
                                    >
                                        <option value="male">남자</option>
                                        <option value="female">여자</option>
                                    </select>
                                    <ArrowRight size={16} className="chevron-icon" />
                                </div>
                            </div>
                            <div className="profile-field-row">
                                <span className="field-label">나이</span>
                                <div className="field-value-controls">
                                    <input
                                        type="number"
                                        value={formData.age}
                                        onChange={(e) => handleInputChange('age', e.target.value)}
                                    />
                                    <span>세</span>
                                    <ArrowRight size={16} className="chevron-icon" />
                                </div>
                            </div>
                            <div className="profile-field-row">
                                <span className="field-label">키</span>
                                <div className="field-value-controls">
                                    <input
                                        type="number"
                                        value={formData.height}
                                        onChange={(e) => handleInputChange('height', e.target.value)}
                                    />
                                    <span>cm</span>
                                    <ArrowRight size={16} className="chevron-icon" />
                                </div>
                            </div>
                            <div className="profile-field-row">
                                <span className="field-label">평소 활동량</span>
                                <div className="field-value-controls">
                                    <select
                                        value={formData.activityLevel}
                                        onChange={(e) => handleInputChange('activityLevel', e.target.value)}
                                    >
                                        <option value="매우 낮음">매우 낮음</option>
                                        <option value="보통">보통</option>
                                        <option value="매우 높음">매우 높음</option>
                                    </select>
                                    <ArrowRight size={16} className="chevron-icon" />
                                </div>
                            </div>
                            <div className="profile-field-row">
                                <span className="field-label">시작 체중</span>
                                <div className="field-value-controls">
                                    <input
                                        type="number"
                                        value={formData.startWeight}
                                        onChange={(e) => handleInputChange('startWeight', e.target.value)}
                                    />
                                    <span>kg</span>
                                    <ArrowRight size={16} className="chevron-icon" />
                                </div>
                            </div>
                            <div className="profile-field-row">
                                <span className="field-label">목표 체중</span>
                                <div className="field-value-controls">
                                    <input
                                        type="number"
                                        value={formData.targetWeight}
                                        onChange={(e) => handleInputChange('targetWeight', e.target.value)}
                                    />
                                    <span>kg</span>
                                    <ArrowRight size={16} className="chevron-icon" />
                                </div>
                            </div>
                        </div>

                        <button
                            type="button"
                            className="modal-submit-btn"
                            onClick={() => setShowProfileModal(false)}
                        >
                            이 정보로 추천 계획 받기
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Signup;
