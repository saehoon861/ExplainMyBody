import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Mail, Lock, Upload, Image as ImageIcon, Check, CheckCircle, ArrowRight, ArrowLeft, AlertCircle, Target, Activity, User, Clock, Ruler, Camera } from 'lucide-react';
import '../../styles/LoginLight.css';

const Signup = () => {
    const [step, setStep] = useState(1);

    const preferredExercisesList = [
        '유산소', '무산소', '러닝', '걷기', '고강도운동',
        '웨이트', '요가', '필라테스',
        '맨몸운동', '실내운동', '실외운동', '기타'
    ];

    const [formData, setFormData] = useState({
        email: '',
        password: '',
        confirmPassword: '',
        inbodyImage: null,
        inbodyData: null,
        hasMedicalCondition: false,
        medicalConditions: [],
        medicalConditionsDetail: '',
        preferredExercises: [],
        gender: '남성',
        age: '',
        height: '',
        startWeight: '',
        targetWeight: '',
        goalType: '감량',
        activityLevel: '보통',
        goal: ''
    });

    const [maxStep, setMaxStep] = useState(1);

    const [showProfileModal, setShowProfileModal] = useState(false);
    const [errors, setErrors] = useState({});
    const [passwordStrength, setPasswordStrength] = useState('');
    const [imagePreview, setImagePreview] = useState(null);
    const [isProcessingOCR, setIsProcessingOCR] = useState(false);
    const [loadingMessage, setLoadingMessage] = useState('인바디 리포트를 읽어오는 중입니다...');
    const [reportSlideIndex, setReportSlideIndex] = useState(0);
    const [touchStart, setTouchStart] = useState(null);
    const [touchEnd, setTouchEnd] = useState(null);
    const [emailCheckStatus, setEmailCheckStatus] = useState('idle'); // idle, checking, available, duplicate, error
    const [emailCheckMessage, setEmailCheckMessage] = useState('');
    const navigate = useNavigate();

    const checkEmailDuplicate = async (email) => {
        if (!email || !validateEmail(email)) return;

        setEmailCheckStatus('checking');
        setEmailCheckMessage('');

        try {
            const response = await fetch('/api/auth/check-email', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email }),
            });

            if (response.ok) {
                setEmailCheckStatus('available');
                setEmailCheckMessage('사용 가능한 이메일입니다.');
                setErrors(prev => ({ ...prev, email: '' }));
            } else if (response.status === 409) {
                setEmailCheckStatus('duplicate');
                setEmailCheckMessage('이미 사용 중인 이메일입니다.');
                setErrors(prev => ({ ...prev, email: '이미 사용 중인 이메일입니다.' }));
            } else {
                throw new Error('Server Error');
            }
        } catch (error) {
            console.error('Email check failed:', error);
            setEmailCheckStatus('error');
            // Don't show generic error to user to avoid confusion, validation will catch it later if needed
        }
    };

    // 스와이프 감지를 위한 최소 거리 (픽셀)
    const minSwipeDistance = 50;

    const onTouchStart = (e) => {
        setTouchEnd(null);
        setTouchStart(e.targetTouches[0].clientX);
    };

    const onTouchMove = (e) => {
        setTouchEnd(e.targetTouches[0].clientX);
        // Don't prevent default to allow vertical scrolling
        // Only handle horizontal swipes, allow vertical scrolling
    };

    const onTouchEnd = () => {
        if (!touchStart || !touchEnd) return;

        const distanceX = touchStart - touchEnd;
        const isLeftSwipe = distanceX > minSwipeDistance;
        const isRightSwipe = distanceX < -minSwipeDistance;

        // Only change slides if it's a clear horizontal swipe
        if (isLeftSwipe && reportSlideIndex < reportSlides.length - 1) {
            setReportSlideIndex(prev => prev + 1);
        } else if (isRightSwipe && reportSlideIndex > 0) {
            setReportSlideIndex(prev => prev - 1);
        }

        // Reset touch tracking
        setTouchStart(null);
        setTouchEnd(null);
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
        // Validation for numeric fields
        if (['age', 'height', 'startWeight', 'targetWeight'].includes(field)) {
            // 정규식: 숫자만 혹은 소수점 포함 숫자
            if (!/^\d*\.?\d*$/.test(value)) {
                return; // 숫자 이외의 문자 입력 시 무시
            }
            // 범위 체크
            const numValue = parseFloat(value);
            if (!isNaN(numValue)) {
                if (field === 'age' && numValue > 150) return;
                if (field === 'height' && numValue > 300) return;
                if ((field === 'startWeight' || field === 'targetWeight') && numValue > 500) return;
            }
            if (value.length > 7) return; // 길이 제한
        }

        setFormData(prev => {
            const newState = { ...prev, [field]: value };

            // Sync with inbodyData if it exists
            if (newState.inbodyData) {
                if (field === 'startWeight') {
                    if (!newState.inbodyData['체중관리']) newState.inbodyData['체중관리'] = {};
                    newState.inbodyData['체중관리']['체중'] = value;
                } else if (field === 'height') {
                    if (!newState.inbodyData['기본정보']) newState.inbodyData['기본정보'] = {};
                    newState.inbodyData['기본정보']['신장'] = value;
                } else if (field === 'age') {
                    if (!newState.inbodyData['기본정보']) newState.inbodyData['기본정보'] = {};
                    newState.inbodyData['기본정보']['연령'] = value;
                } else if (field === 'gender') {
                    if (!newState.inbodyData['기본정보']) newState.inbodyData['기본정보'] = {};
                    newState.inbodyData['기본정보']['성별'] = value;
                }
            }
            return newState;
        });
        setErrors(prev => ({ ...prev, [field]: '' }));

        if (field === 'password') {
            setPasswordStrength(calculatePasswordStrength(value));
        }
    };

    // 부위별 분석 카테고리 (드롭다운으로 표시할 카테고리)
    const segmentalCategories = ['부위별근육분석', '부위별체지방분석'];

    const handleInbodyFieldChange = (category, field, value) => {
        // 부위별 분석 카테고리는 드롭다운으로 선택하므로 검증 없이 바로 저장
        if (segmentalCategories.includes(category)) {
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
            return;
        }

        // Validation Logic
        let isValid = true;

        if (field === '성별') {
            // 성별은 텍스트 허용 (최대 10자)
            if (value.length > 10) isValid = false;
        } else {
            // 그 외 수치 데이터는 숫자와 소수점만 허용 (음수 허용)
            // 정규식: 숫자만 혹은 소수점 포함 숫자, 음수 가능
            if (!/^-?\d*\.?\d*$/.test(value)) {
                isValid = false;
            } else {
                // 범위 제한 (터무니 없는 값 방지)
                const numValue = parseFloat(value);
                if (!isNaN(numValue)) {
                    if (field === '신장' && numValue > 300) isValid = false; // 300cm 초과 방지
                    else if (field === '연령' && numValue > 150) isValid = false; // 150세 초과 방지
                    else if ((field.includes('체중') || field.includes('몸무게')) && numValue > 500) isValid = false; // 500kg 초과 방지
                    else if (field.includes('점수') && numValue > 120) isValid = false; // 인바디 점수 120 초과 방지
                    else if (value.length > 7) isValid = false; // 그 외 너무 긴 숫자 방지
                }
            }
        }

        if (isValid) {
            setFormData(prev => {
                const newState = {
                    ...prev,
                    inbodyData: {
                        ...prev.inbodyData,
                        [category]: {
                            ...prev.inbodyData[category],
                            [field]: value
                        }
                    }
                };

                // Sync with root fields if OCR data is updated
                if (category === '체중관리' && field === '체중') newState.startWeight = value;
                if (category === '기본정보' && field === '신장') newState.height = value;
                if (category === '기본정보' && field === '연령') newState.age = value;
                if (category === '기본정보' && field === '성별') newState.gender = value;

                return newState;
            });
        }
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
            apiFormData.append('image', formData.inbodyImage);

            const response = await fetch('/api/health-records/ocr/extract', {
                method: 'POST',
                body: apiFormData,
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'OCR 처리 중 오류가 발생했습니다.');
            }

            const result = await response.json();
            if (result.data) {
                setOcrProgress(100); // 성공 시 100%로 점프
                setTimeout(() => {
                    const extracted = result.data;
                    const basicInfo = extracted?.['기본정보'] || {};
                    // '골격근·지방분석' 섹션의 키가 '체중관리'로 매핑되어 있음 (reportSlides 참조)
                    const weightInfo = extracted?.['체중관리'] || {};

                    const autoFill = {};

                    // 성별 자동 입력
                    if (basicInfo['성별']) {
                        if (basicInfo['성별'].includes('남') || basicInfo['성별'].toLowerCase().includes('m')) {
                            autoFill.gender = '남성';
                            // inbodyData의 성별도 정규화된 값으로 업데이트 (백엔드 일관성 유지)
                            extracted['기본정보']['성별'] = '남성';
                        } else if (basicInfo['성별'].includes('여') || basicInfo['성별'].toLowerCase().includes('f')) {
                            autoFill.gender = '여성';
                            // inbodyData의 성별도 정규화된 값으로 업데이트 (백엔드 일관성 유지)
                            extracted['기본정보']['성별'] = '여성';
                        }
                    }

                    // 나이, 키, 체중 자동 입력 (숫자와 점만 추출)
                    if (basicInfo['연령']) autoFill.age = basicInfo['연령'].replace(/[^0-9]/g, '');
                    if (basicInfo['신장']) autoFill.height = basicInfo['신장'].replace(/[^0-9.]/g, '');
                    if (weightInfo['체중']) autoFill.startWeight = weightInfo['체중'].replace(/[^0-9.]/g, '');

                    setFormData(prev => ({
                        ...prev,
                        inbodyData: extracted,
                        ...autoFill
                    }));
                    setIsProcessingOCR(false); // 로딩 종료 및 결과 화면 전환
                }, 500); // 100%를 잠시 보여준 후 결과 화면으로 전환
            } else {
                throw new Error(result.error || '필드 추출에 실패했습니다.');
            }
        } catch (err) {
            clearTimeout(timeoutId);
            console.error('OCR Error:', err);
            setIsProcessingOCR(false);  // 에러 발생 시 즉시 로딩 종료
            setOcrProgress(0);  // 진행률 초기화

            if (err.name === 'AbortError') {
                setErrors({ ocr: '요청 시간이 초과되었습니다. 다시 시도해주세요.' });
            } else {
                setErrors({ ocr: err.message || 'OCR 처리 중 오류가 발생했습니다.' });
            }
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
        if (!validateEmail(formData.email)) {
            errors.email = '유효한 이메일 주소를 입력해주세요.';
        } else if (emailCheckStatus === 'duplicate') {
            errors.email = '이미 사용 중인 이메일입니다. 다른 이메일을 사용해주세요.';
        } else if (emailCheckStatus === 'checking') {
            // 로딩 중이면 진행 막음
            setErrors(prev => ({ ...prev, email: '이메일 중복 확인 중입니다. 잠시만 기다려주세요.' }));
            return false;
        } else if (emailCheckStatus !== 'available') {
            // 아직 확인 안 된 경우 (e.g. 빠르게 입력 후 바로 버튼 클릭)
            checkEmailDuplicate(formData.email);
            setErrors(prev => ({ ...prev, email: '이메일 중복 확인이 필요합니다.' }));
            return false;
        }

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

        // Final submission only allowed on Step 4 (Medical Condition check)
        if (step !== 4) return;

        if (validateStep4()) {
            try {
                // [프론트엔드 -> 백엔드 데이터 전송 시작]
                // formData 객체에는 회원가입에 필요한 모든 정보(이메일, 비밀번호, 인바디 결과 등)가 담겨 있습니다.
                // fetch API를 사용해 백엔드 API 서버의 '/api/signup' 엔드포인트로 POST 요청을 보냅니다.
                const response = await fetch('/api/auth/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        ...formData,
                        username: formData.email.split('@')[0], // Backend requires username, use email prefix
                        // Convert string numbers to actual numbers or null for backend validation
                        age: formData.age ? parseInt(formData.age) : null,
                        height: formData.height ? parseFloat(formData.height) : null,
                        startWeight: formData.startWeight ? parseFloat(formData.startWeight) : null,
                        targetWeight: formData.targetWeight ? parseFloat(formData.targetWeight) : null
                    }),
                });

                if (!response.ok) {
                    let errorMessage = '회원가입에 실패했습니다.';
                    try {
                        const errorData = await response.json();
                        if (errorData.detail) {
                            if (typeof errorData.detail === 'object') {
                                // Pydantic validation error or complex error object
                                errorMessage = JSON.stringify(errorData.detail, null, 2);
                                if (Array.isArray(errorData.detail)) {
                                    // Try to format Pydantic errors nicely
                                    errorMessage = errorData.detail
                                        .map(err => {
                                            const field = err.loc ? err.loc.join(' -> ') : 'Field';
                                            return `${field}: ${err.msg}`;
                                        })
                                        .join('\n');
                                }
                            } else {
                                errorMessage = errorData.detail;
                            }
                        }
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

                // 성공 시 대시보드에 사용자 정보 전달 및 로컬 스토리지 저장
                localStorage.setItem('user', JSON.stringify(result));

                // 운동 설정 정보를 별도 저장 (운동 플래너에서 사용)
                localStorage.setItem('exerciseSettings', JSON.stringify({
                    goal: formData.goalType || '',
                    preferences: formData.preferredExercises || [],
                    diseases: [
                        ...(formData.medicalConditions || []),
                        formData.medicalConditionsDetail || ''
                    ].filter(Boolean).join(', ')
                }));

                // alert('회원가입이 완료되었습니다!');
                navigate('/signup-success');
            } catch (err) {
                console.error('Signup Error:', err);
                setErrors({ submit: err.message });
                alert(`오류: ${err.message}`);
            }
        }
    };

    const medicalConditionsList = [
        '고혈압', '당뇨', '심장 질환', '호흡기 질환', '관절염', '허리 디스크', '근골격계 질환', '기타'
    ];

    const segmentalOptions = ['표준', '표준이상', '표준이하'];

    const renderInbodyTable = (title, categoryKey, unitMap = {}) => {
        const categoryData = formData.inbodyData?.[categoryKey];
        if (!categoryData) return null;
        const isSegmental = segmentalCategories.includes(categoryKey);

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
                        <div className="header-cell">{isSegmental ? '평가' : '단위'}</div>
                    </div>
                    {Object.entries(categoryData).map(([field, value]) => (
                        <div className="table-row" key={field}>
                            <div className="row-label">{field}</div>
                            <div className="row-value">
                                {isSegmental ? (
                                    <select
                                        value={value || ''}
                                        onChange={(e) => handleInbodyFieldChange(categoryKey, field, e.target.value)}
                                        className="segmental-select"
                                    >
                                        <option value="">선택</option>
                                        {segmentalOptions.map(option => (
                                            <option key={option} value={option}>{option}</option>
                                        ))}
                                    </select>
                                ) : (
                                    <input
                                        type="text"
                                        value={value || ''}
                                        placeholder="-"
                                        onChange={(e) => handleInbodyFieldChange(categoryKey, field, e.target.value)}
                                    />
                                )}
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

                <form onSubmit={handleSubmit} onKeyDown={(e) => {
                    // 엔터키로 인한 자동 제출 방지 (textarea 제외)
                    if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA') {
                        e.preventDefault();
                    }
                }}>
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
                                            onChange={(e) => {
                                                handleInputChange('email', e.target.value);
                                                // Reset check status on change
                                                setEmailCheckStatus('idle');
                                                setEmailCheckMessage('');
                                            }}
                                            onBlur={() => checkEmailDuplicate(formData.email)}
                                            autoFocus
                                        />
                                        {/* Status Text inside input */}
                                        <div style={{ position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)', fontSize: '11px', fontWeight: 'bold' }}>
                                            {emailCheckStatus === 'checking' && <span style={{ color: '#94a3b8' }}>확인중...</span>}
                                            {emailCheckStatus === 'available' && <span style={{ color: '#10b981' }}>사용가능</span>}
                                            {emailCheckStatus === 'duplicate' && <span style={{ color: '#ef4444' }}>중복</span>}
                                        </div>
                                    </div>

                                    {/* Helper Message Area */}
                                    <div style={{ minHeight: '20px', marginTop: '4px' }}>
                                        {emailCheckStatus === 'available' && (
                                            <div className="success-message fade-in" style={{ fontSize: '0.85rem', color: '#10b981', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                                {emailCheckMessage}
                                            </div>
                                        )}
                                        {emailCheckStatus === 'duplicate' && (
                                            <div className="error-message fade-in" style={{ fontSize: '0.85rem', color: '#ef4444', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                                {emailCheckMessage}
                                            </div>
                                        )}
                                        {errors.email && emailCheckStatus !== 'duplicate' && (
                                            <div className="error-message">{errors.email}</div>
                                        )}
                                    </div>
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
                                            style={{ position: 'relative', display: 'flex', alignItems: 'center', gap: '10px', touchAction: 'pan-y', overflow: 'visible' }}
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
                                            <span className="stat-value highlight">{formData.goalType}{formData.goalType === '재활' && formData.goal ? ` (${formData.goal})` : ''}</span>
                                        </div>
                                        <div className="stat-item">
                                            <span className="stat-label">목표체중</span>
                                            <span className="stat-value">{formData.targetWeight || '-'} kg</span>
                                        </div>
                                        <div className="stat-item">
                                            <span className="stat-label">변화</span>
                                            <span className="stat-value">
                                                {(() => {
                                                    const start = parseFloat(formData.startWeight);
                                                    const target = parseFloat(formData.targetWeight);
                                                    if (isNaN(start) || isNaN(target)) return '-';
                                                    const diff = (target - start).toFixed(1);
                                                    const sign = diff > 0 ? '+' : '';
                                                    return `${sign}${diff}`;
                                                })()} kg
                                            </span>
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
                            <button
                                type="button" // submit 타입을 button으로 변경하여 자동 제출 방지
                                className="login-button"
                                onClick={(e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    handleSubmit(e);
                                }}
                            >
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
                            <h2>목표를 설정해 주세요</h2>
                        </div>

                        <div className="profile-fields-list">
                            <div className="profile-field-row" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: '12px' }}>
                                <span className="field-label">목표 (다중 선택 가능)</span>
                                <div className="checkbox-grid" style={{ width: '100%', display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px' }}>
                                    {['감량', '유지', '증량', '재활'].map(type => {
                                        const selectedGoals = formData.goalType ? formData.goalType.split(',').map(g => g.trim()).filter(g => g !== '') : [];
                                        const isSelected = selectedGoals.includes(type);
                                        const exclusiveGoals = ['감량', '유지', '증량'];
                                        return (
                                            <div
                                                key={type}
                                                className={`checkbox-item ${isSelected ? 'active' : ''}`}
                                                onClick={() => {
                                                    let newGoals;
                                                    if (isSelected) {
                                                        // 선택 해제
                                                        newGoals = selectedGoals.filter(g => g !== type);
                                                    } else {
                                                        // 새로 선택
                                                        if (exclusiveGoals.includes(type)) {
                                                            // 감량/유지/증량 중 하나 선택 시: 기존 감량/유지/증량 제거, 재활은 유지
                                                            newGoals = selectedGoals.filter(g => !exclusiveGoals.includes(g));
                                                            newGoals.push(type);
                                                        } else {
                                                            // 재활 선택 시: 기존 선택에 추가
                                                            newGoals = [...selectedGoals, type];
                                                        }
                                                        const order = ['감량', '유지', '증량', '재활'];
                                                        newGoals.sort((a, b) => order.indexOf(a) - order.indexOf(b));
                                                    }
                                                    handleInputChange('goalType', newGoals.join(', '));
                                                    if (!newGoals.includes('재활')) {
                                                        handleInputChange('goal', '');
                                                    }
                                                }}
                                                style={{ padding: '12px', textAlign: 'center', backgroundColor: 'white' }}
                                            >
                                                <span>{type}</span>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>

                            {formData.goalType && formData.goalType.includes('재활') && (
                                <div style={{ marginBottom: '20px', padding: '16px', backgroundColor: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0' }} className="fade-in">
                                    <span style={{ display: 'block', marginBottom: '12px', fontSize: '0.85rem', color: '#64748b', fontWeight: '600' }}>재활 부위 선택 (다중 선택 가능)</span>
                                    <div className="checkbox-grid" style={{ marginBottom: '12px', display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px' }}>
                                        {['허리 재활', '어깨 재활', '무릎 재활', '목 재활', '발목 재활'].map(part => {
                                            const selectedParts = (formData.goal || '').split(',').map(p => p.trim()).filter(p => p !== '');
                                            const isSelected = selectedParts.includes(part);
                                            return (
                                                <div
                                                    key={part}
                                                    className={`checkbox-item ${isSelected ? 'active' : ''}`}
                                                    onClick={() => {
                                                        let newParts;
                                                        if (isSelected) {
                                                            newParts = selectedParts.filter(p => p !== part);
                                                        } else {
                                                            newParts = [...selectedParts, part];
                                                        }
                                                        handleInputChange('goal', newParts.join(', '));
                                                    }}
                                                    style={{ fontSize: '0.8rem', padding: '8px', textAlign: 'center', backgroundColor: 'white' }}
                                                >
                                                    <span>{part}</span>
                                                </div>
                                            );
                                        })}
                                        <div
                                            className={`checkbox-item ${(() => {
                                                const standardParts = ['허리 재활', '어깨 재활', '무릎 재활', '목 재활', '발목 재활'];
                                                const parts = (formData.goal || '').split(',').map(p => p.trim()).filter(p => p !== '');
                                                return parts.some(p => !standardParts.includes(p)) || (formData.goal && formData.goal.endsWith(' '));
                                            })() ? 'active' : ''}`}
                                            onClick={() => {
                                                const standardParts = ['허리 재활', '어깨 재활', '무릎 재활', '목 재활', '발목 재활'];
                                                const parts = (formData.goal || '').split(',').map(p => p.trim()).filter(p => p !== '');
                                                const hasOther = parts.some(p => !standardParts.includes(p));

                                                if (hasOther || (formData.goal && formData.goal.endsWith(' '))) {
                                                    const newParts = parts.filter(p => standardParts.includes(p));
                                                    handleInputChange('goal', newParts.join(', '));
                                                } else {
                                                    const prefix = formData.goal ? (formData.goal.endsWith(', ') ? formData.goal : formData.goal + ', ') : '';
                                                    handleInputChange('goal', prefix + ' ');
                                                }
                                            }}
                                            style={{ fontSize: '0.8rem', padding: '8px', textAlign: 'center', backgroundColor: 'white' }}
                                        >
                                            <span>기타</span>
                                        </div>
                                    </div>
                                    {(() => {
                                        const standardParts = ['허리 재활', '어깨 재활', '무릎 재활', '목 재활', '발목 재활'];
                                        const fullDesc = formData.goal || '';
                                        const parts = fullDesc.split(',').map(p => p.trim()).filter(p => p !== '');
                                        const otherValue = parts.find(p => !standardParts.includes(p)) || (fullDesc.endsWith(' ') ? '' : null);

                                        if (otherValue !== null) {
                                            return (
                                                <div style={{ position: 'relative', marginTop: '8px' }}>
                                                    <input
                                                        type="text"
                                                        placeholder="예: 손목, 팔꿈치 등"
                                                        style={{
                                                            width: '100%',
                                                            padding: '14px 16px',
                                                            fontSize: '0.95rem',
                                                            border: '2px solid #e2e8f0',
                                                            borderRadius: '12px',
                                                            backgroundColor: '#ffffff',
                                                            outline: 'none',
                                                            transition: 'all 0.2s ease',
                                                            boxShadow: '0 2px 4px rgba(0,0,0,0.02)'
                                                        }}
                                                        onFocus={(e) => {
                                                            e.target.style.borderColor = '#6366f1';
                                                            e.target.style.boxShadow = '0 0 0 3px rgba(99, 102, 241, 0.1)';
                                                        }}
                                                        onBlur={(e) => {
                                                            e.target.style.borderColor = '#e2e8f0';
                                                            e.target.style.boxShadow = '0 2px 4px rgba(0,0,0,0.02)';
                                                        }}
                                                        value={otherValue}
                                                        onChange={(e) => {
                                                            const val = e.target.value;
                                                            const baseParts = parts.filter(p => standardParts.includes(p));
                                                            if (val) {
                                                                handleInputChange('goal', [...baseParts, val].join(', '));
                                                            } else {
                                                                handleInputChange('goal', baseParts.join(', ') + (baseParts.length > 0 ? ', ' : '') + ' ');
                                                            }
                                                        }}
                                                    />
                                                </div>
                                            );
                                        }
                                        return null;
                                    })()}
                                </div>
                            )}
                            {/* Gender, Age, Height fields removed as per request */}
                            <div className="profile-field-row">
                                <span className="field-label">평소 활동량</span>
                                <div className="field-value-controls">
                                    <select
                                        value={formData.activityLevel}
                                        onChange={(e) => handleInputChange('activityLevel', e.target.value)}
                                        style={{ padding: '10px 12px', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '0.95rem' }}
                                    >
                                        <option value="매우 낮음">매우 낮음</option>
                                        <option value="보통">보통</option>
                                        <option value="매우 높음">매우 높음</option>
                                    </select>
                                </div>
                            </div>
                            <div className="profile-field-row">
                                <span className="field-label">시작 체중 <span style={{ fontSize: '0.7rem', color: '#94a3b8', fontWeight: '400' }}>(인바디 기준)</span></span>
                                <div className="field-value-controls" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <input
                                        type="text"
                                        value={formData.startWeight}
                                        onChange={(e) => handleInputChange('startWeight', e.target.value)}
                                        disabled={!!formData.inbodyData?.["체중관리"]?.["체중"]}
                                        style={{
                                            width: '80px',
                                            padding: '10px 12px',
                                            borderRadius: '8px',
                                            border: '1px solid #e2e8f0',
                                            fontSize: '1rem',
                                            textAlign: 'center',
                                            backgroundColor: !!formData.inbodyData?.["체중관리"]?.["체중"] ? '#f1f5f9' : 'white',
                                            color: !!formData.inbodyData?.["체중관리"]?.["체중"] ? '#64748b' : 'inherit',
                                            cursor: !!formData.inbodyData?.["체중관리"]?.["체중"] ? 'not-allowed' : 'text'
                                        }}
                                    />
                                    <span style={{ color: '#64748b', fontWeight: '500' }}>kg</span>
                                </div>
                            </div>
                            <div className="profile-field-row">
                                <span className="field-label">목표 체중</span>
                                <div className="field-value-controls" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <input
                                        type="text"
                                        value={formData.targetWeight}
                                        onChange={(e) => handleInputChange('targetWeight', e.target.value)}
                                        style={{ width: '80px', padding: '10px 12px', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '1rem', textAlign: 'center' }}
                                    />
                                    <span style={{ color: '#64748b', fontWeight: '500' }}>kg</span>
                                </div>
                            </div>
                        </div>

                        <button
                            type="button"
                            className="modal-submit-btn"
                            onClick={() => setShowProfileModal(false)}
                        >
                            운동목표설정 완료
                        </button>
                    </div>
                </div>
            )
            }
        </div >
    );
};

export default Signup;
