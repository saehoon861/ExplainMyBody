import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Mail, Lock, Upload, Image as ImageIcon, Check, CheckCircle, ArrowRight, ArrowLeft, AlertCircle, Target, Activity, Loader2, User, Clock, Ruler, Info, ChevronLeft, ChevronRight, Camera } from 'lucide-react';
import './LoginLight.css';

const Signup = () => {
    const [step, setStep] = useState(() => {
        const saved = localStorage.getItem('signup_persist');
        return saved ? JSON.parse(saved).step || 1 : 1;
    });

    const preferredExercisesList = [
        '유산소', '무산소', '러닝', '걷기', '고강도운동',
        '에이트', '요가', '필라테스',
        '맨몸운동', '실내운동', '실외운동', '기타'
    ];

    const [formData, setFormData] = useState(() => {
        const saved = localStorage.getItem('signup_persist');
        if (saved) {
            const parsed = JSON.parse(saved);
            return { ...parsed.formData, password: '', confirmPassword: '' }; // Don't restore passwords
        }
        return {
            email: '',
            password: '',
            confirmPassword: '',
            inbodyImage: null,
            inbodyData: null,
            hasMedicalCondition: false,
            medicalConditions: [],
            medicalConditionsDetail: '',
            preferredExercises: [],
            gender: 'male',
            age: '31',
            height: '170',
            startWeight: '30',
            targetWeight: '58',
            goalType: '감량',
            activityLevel: '보통',
            goal: ''
        };
    });

    const [maxStep, setMaxStep] = useState(() => {
        const saved = localStorage.getItem('signup_persist');
        return saved ? JSON.parse(saved).maxStep || 1 : 1;
    });

    // Save to localStorage effects
    React.useEffect(() => {
        const dataToSave = {
            formData: { ...formData, password: '', confirmPassword: '', inbodyImage: null }, // Exclude sensitive/complex data
            step,
            maxStep
        };
        localStorage.setItem('signup_persist', JSON.stringify(dataToSave));
    }, [formData, step, maxStep]);
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
        { title: "부위별 근육", key: "부위별근육분석" },
        { title: "부위별 체지방", key: "부위별체지방분석" }
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

    const [ocrProgress, setOcrProgress] = useState(0);

    React.useEffect(() => {
        let progressInterval;
        if (isProcessingOCR) {
            setOcrProgress(0);
            progressInterval = setInterval(() => {
                setOcrProgress(prev => {
                    if (prev >= 95) return prev; // 실제 결과가 올 때까지 95%에서 대기
                    const increment = Math.random() * 15; // 랜덤한 증가량으로 실제 분석 느낌 연출
                    return Math.min(prev + increment, 95);
                });
            }, 800);
        } else {
            setOcrProgress(0);
        }
        return () => clearInterval(progressInterval);
    }, [isProcessingOCR]);

    const processOCR = async () => {
        if (!formData.inbodyImage) return;

        setIsProcessingOCR(true);
        setOcrProgress(0);
        setErrors({});

        // 180초 타임아웃 설정 (OCR 처리 시간 고려)
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 180000);

        try {
            const apiFormData = new FormData();
            apiFormData.append('file', formData.inbodyImage);

            const response = await fetch('/api/process', {
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
            if (result.success) {
                setOcrProgress(100); // 성공 시 100%로 점프
                setTimeout(() => {
                    setFormData(prev => ({
                        ...prev,
                        inbodyData: result.data.structured
                    }));
                }, 500); // 100%를 잠시 보여준 후 결과 화면으로 전환
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
            // setIsProcessingOCR(false)는 결과 데이터를 보여줄 때 지연 호출됨
            if (errors.ocr) setIsProcessingOCR(false);
        }
    };

    const handlePreferredExerciseToggle = (exercise) => {
        setFormData(prev => {
            const exercises = prev.preferredExercises.includes(exercise)
                ? prev.preferredExercises.filter(e => e !== exercise)
                : [...prev.preferredExercises, exercise];
            return { ...prev, preferredExercises: exercises };
        });
    };

    const handleMedicalConditionToggle = (condition) => {
        setFormData(prev => {
            const conditions = prev.medicalConditions.includes(condition)
                ? prev.medicalConditions.filter(c => c !== condition)
                : [...prev.medicalConditions, condition];
            return { ...prev, medicalConditions: conditions };
        });
    };

    const handleStepChange = (newStep) => {
        if (newStep < step || newStep <= maxStep) {
            setStep(newStep);
        }
    };

    const navigateNext = (nextStep) => {
        setStep(nextStep);
        setMaxStep(Math.max(maxStep, nextStep));
        window.scrollTo(0, 0);
    };

    const updateMaxStep = () => {
        // Just a helper if needed, but navigateNext handles it
    };

    const handlePrevious = () => {
        if (step > 1) {
            setStep(step - 1);
        }
    };

    const getPasswordStrengthClass = () => {
        return passwordStrength;
    };

    const getPasswordStrengthText = () => {
        switch (passwordStrength) {
            case 'weak': return '약함';
            case 'medium': return '보통';
            case 'strong': return '강함';
            default: return '';
        }
    };

    const validateStep1 = () => {
        const errors = {};
        if (!validateEmail(formData.email)) errors.email = '유효한 이메일 주소를 입력해주세요.';
        if (formData.password.length < 6) errors.password = '비밀번호는 6자 이상이어야 합니다.';
        if (formData.password !== formData.confirmPassword) errors.confirmPassword = '비밀번호가 일치하지 않습니다.';

        setErrors(errors);
        return Object.keys(errors).length === 0;
    };

    const validateStep4 = () => {
        return true;
    };

    const handleNext = () => {
        if (step === 1 && !validateStep1()) return;

        if (step < 4) {
            setStep(prev => prev + 1);
            setMaxStep(prev => Math.max(prev, step + 1));
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (validateStep4()) {
            try {
                // [프론트엔드 -> 백엔드 데이터 전송 시작]
                // formData 객체에는 회원가입에 필요한 모든 정보(이메일, 비밀번호, 인바디 결과 등)가 담겨 있습니다.
                // fetch API를 사용해 백엔드 API 서버의 '/api/signup' 엔드포인트로 POST 요청을 보냅니다.
                const response = await fetch('/api/signup', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData), // 데이터를 JSON 문자열로 변환하여 전송
                });

                if (!response.ok) {
                    let errorMessage = '회원가입에 실패했습니다.';
                    try {
                        const errorData = await response.json();
                        errorMessage = errorData.detail || errorMessage;
                    } catch (e) {
                        // If response is not JSON (e.g., HTML 500 error)
                        console.error('Non-JSON error response:', e);
                        errorMessage = `서버 오류가 발생했습니다. (${response.status})`;
                    }
                    throw new Error(errorMessage);
                }

                let result;
                try {
                    result = await response.json();
                } catch (e) {
                    throw new Error('서버로부터 올바른 응답을 받지 못했습니다. (JSON Parsing Error)');
                }
                console.log('Signup success:', result);

                // 성공 시 대시보드로 이동
                alert('회원가입이 완료되었습니다!');
                localStorage.removeItem('signup_persist'); // Clear saved data
                navigate('/dashboard');
            } catch (err) {
                console.error('Signup Error:', err);
                setErrors({ submit: err.message });
                alert(`오류: ${err.message}`);
            }
        }
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
                    {[1, 2, 3, 4].map((s) => (
                        <React.Fragment key={s}>
                            <div
                                className={`progress-step ${step === s ? 'active' : ''} ${maxStep > s ? 'completed' : ''}`}
                                onClick={() => handleStepChange(s)}
                                style={{ cursor: s <= maxStep ? 'pointer' : 'default' }}
                            >
                                <div className="step-number">{maxStep > s ? <Check size={16} /> : s}</div>
                                <div className="step-label">
                                    {s === 1 && '계정정보'}
                                    {s === 2 && '인바디'}
                                    {s === 3 && '목표설정'}
                                    {s === 4 && '건강체크'}
                                </div>
                            </div>
                            {s < 4 && <div className={`progress-line ${maxStep > s ? 'active' : ''}`}></div>}
                        </React.Fragment>
                    ))}
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
                                    {!formData.inbodyData && (
                                        <div className={`upload-area ${imagePreview ? 'minimized' : ''} ${isProcessingOCR ? 'exit' : ''}`}>
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
                                                                setFormData(prev => ({ ...prev, inbodyImage: null, inbodyData: null }));
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

                                {formData.inbodyData && (
                                    <div className="inbody-report-container fade-in">
                                        <div className="report-header-main">
                                            <div className="report-title-row" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                                                <div className="title-group">
                                                    <h2 style={{ fontSize: '1.5rem', margin: 0 }}>InBody <span>Results</span></h2>
                                                    <div className="report-badge">인바디 성적표</div>
                                                </div>
                                                <button
                                                    type="button"
                                                    className="ghost-button"
                                                    style={{ borderRadius: '10px' }}
                                                    onClick={() => {
                                                        setFormData(prev => ({ ...prev, inbodyData: null }));
                                                        setImagePreview(null);
                                                    }}
                                                >
                                                    <Camera size={14} />
                                                    <span>다시 찍기</span>
                                                </button>
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
                                            style={{ position: 'relative', display: 'flex', alignItems: 'center', gap: '10px', touchAction: 'pan-y' }}
                                        >
                                            <button
                                                type="button"
                                                className="slide-nav-btn"
                                                disabled={reportSlideIndex === 0}
                                                onClick={() => setReportSlideIndex(prev => prev - 1)}
                                                style={{ zIndex: 10, fontSize: '0.8rem' }}
                                            >
                                                ◀
                                            </button>

                                            <div className="slide-content-wrapper" key={reportSlideIndex} style={{ flex: 1 }}>
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
                                            <button
                                                type="button"
                                                className="slide-nav-btn"
                                                disabled={reportSlideIndex === reportSlides.length - 1}
                                                onClick={() => setReportSlideIndex(prev => prev + 1)}
                                                style={{ zIndex: 10, fontSize: '0.8rem' }}
                                            >
                                                ▶
                                            </button>
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
                                            <span className="stat-label">목표</span>
                                            <span className="stat-value highlight">{formData.goalType}</span>
                                        </div>
                                        <div className="stat-item">
                                            <span className="stat-label">목표체중</span>
                                            <span className="stat-value">{formData.targetWeight} kg</span>
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
                                        선호하는 운동을 선택해주세요 (다중 선택 가능)
                                    </label>
                                    <div className="checkbox-grid">
                                        {preferredExercisesList.map((exercise) => (
                                            <div
                                                key={exercise}
                                                className={`checkbox-item ${formData.preferredExercises.includes(exercise) ? 'active' : ''}`}
                                                onClick={() => handlePreferredExerciseToggle(exercise)}
                                            >
                                                <span>{exercise}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>


                            </div>
                        )}

                        {step === 4 && (
                            <div className="step-content fade-in" key="step4">
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

                                <div className="info-box">
                                    <AlertCircle size={20} />
                                    <p>입력하신 정보는 맞춤형 운동 코칭을 제공하는 데 사용됩니다.</p>
                                </div>
                            </div>
                        )}
                    </div>

                    <div className="button-group">
                        {step > 1 && (
                            <button type="button" className="secondary-button" onClick={handlePrevious} style={{ minWidth: '80px', whiteSpace: 'nowrap' }}>
                                <ArrowLeft size={20} />
                                이전
                            </button>
                        )}
                        {step < 4 ? (
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
                                <span className="field-label">목표</span>
                                <div className="field-value-controls">
                                    <select
                                        value={formData.goalType}
                                        onChange={(e) => handleInputChange('goalType', e.target.value)}
                                    >
                                        <option value="감량">감량</option>
                                        <option value="증량">증량</option>
                                        <option value="유지">유지</option>
                                        <option value="재활">재활</option>
                                    </select>
                                    <ArrowRight size={16} className="chevron-icon" />
                                </div>
                            </div>
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
