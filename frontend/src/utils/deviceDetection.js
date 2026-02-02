/**
 * 지능적 적응(Intelligent Adaptation) 유틸리티
 *
 * 디바이스 특성, 네트워크 상태, 사용자 선호도를 감지하여
 * 최적화된 사용자 경험을 제공합니다.
 */

/**
 * 디바이스 타입 감지
 */
export const getDeviceType = () => {
    const width = window.innerWidth;
    if (width <= 480) return 'mobile';
    if (width <= 768) return 'tablet';
    return 'desktop';
};

/**
 * 터치 디바이스 감지
 */
export const isTouchDevice = () => {
    return (
        'ontouchstart' in window ||
        navigator.maxTouchPoints > 0 ||
        navigator.msMaxTouchPoints > 0
    );
};

/**
 * 네트워크 속도 감지
 * @returns {'slow' | 'medium' | 'fast'}
 */
export const getNetworkSpeed = () => {
    // Network Information API 지원 확인
    if ('connection' in navigator) {
        const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;

        if (connection) {
            const effectiveType = connection.effectiveType;

            // slow-2g, 2g -> slow
            if (effectiveType === 'slow-2g' || effectiveType === '2g') {
                return 'slow';
            }
            // 3g -> medium
            if (effectiveType === '3g') {
                return 'medium';
            }
            // 4g, 5g -> fast
            return 'fast';
        }
    }

    // 기본값: fast
    return 'fast';
};

/**
 * 사용자 다크 모드 선호도 감지
 */
export const prefersDarkMode = () => {
    if (window.matchMedia) {
        return window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    return false;
};

/**
 * 디바이스 메모리 감지 (GB)
 */
export const getDeviceMemory = () => {
    if ('deviceMemory' in navigator) {
        return navigator.deviceMemory; // GB 단위
    }
    return 4; // 기본값 4GB
};

/**
 * 배터리 상태 감지
 */
export const getBatteryInfo = async () => {
    if ('getBattery' in navigator) {
        try {
            const battery = await navigator.getBattery();
            return {
                level: battery.level, // 0.0 ~ 1.0
                charging: battery.charging,
            };
        } catch (error) {
            return { level: 1.0, charging: true };
        }
    }
    return { level: 1.0, charging: true };
};

/**
 * 성능 프로파일 생성
 * 디바이스의 전체적인 성능 등급을 판단
 */
export const getPerformanceProfile = () => {
    const deviceType = getDeviceType();
    const memory = getDeviceMemory();
    const networkSpeed = getNetworkSpeed();

    // 성능 점수 계산
    let score = 0;

    // 디바이스 타입
    if (deviceType === 'desktop') score += 3;
    else if (deviceType === 'tablet') score += 2;
    else score += 1;

    // 메모리
    if (memory >= 8) score += 3;
    else if (memory >= 4) score += 2;
    else score += 1;

    // 네트워크
    if (networkSpeed === 'fast') score += 3;
    else if (networkSpeed === 'medium') score += 2;
    else score += 1;

    // 성능 등급 판정
    if (score >= 8) return 'high';
    if (score >= 5) return 'medium';
    return 'low';
};

/**
 * 이미지 품질 추천
 */
export const getRecommendedImageQuality = () => {
    const networkSpeed = getNetworkSpeed();
    const performanceProfile = getPerformanceProfile();

    if (networkSpeed === 'slow' || performanceProfile === 'low') {
        return 'low'; // 저화질
    }
    if (networkSpeed === 'medium' && performanceProfile === 'medium') {
        return 'medium'; // 중화질
    }
    return 'high'; // 고화질
};

/**
 * 애니메이션 활성화 여부 판단
 */
export const shouldEnableAnimations = () => {
    const performanceProfile = getPerformanceProfile();

    // 사용자가 모션 감소를 선호하는지 확인
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        return false;
    }

    // 저사양 기기에서는 애니메이션 비활성화
    return performanceProfile !== 'low';
};

/**
 * 컴포넌트 lazy loading 전략
 */
export const getLazyLoadingStrategy = () => {
    const networkSpeed = getNetworkSpeed();
    const performanceProfile = getPerformanceProfile();

    if (networkSpeed === 'slow' || performanceProfile === 'low') {
        return 'aggressive'; // 적극적 lazy loading
    }
    if (networkSpeed === 'medium' || performanceProfile === 'medium') {
        return 'moderate'; // 보통 lazy loading
    }
    return 'minimal'; // 최소 lazy loading
};

/**
 * 디바이스 정보 객체 반환
 */
export const getDeviceInfo = async () => {
    const battery = await getBatteryInfo();

    return {
        type: getDeviceType(),
        isTouch: isTouchDevice(),
        networkSpeed: getNetworkSpeed(),
        prefersDark: prefersDarkMode(),
        memory: getDeviceMemory(),
        battery,
        performanceProfile: getPerformanceProfile(),
        recommendedImageQuality: getRecommendedImageQuality(),
        shouldEnableAnimations: shouldEnableAnimations(),
        lazyLoadingStrategy: getLazyLoadingStrategy(),
    };
};

/**
 * 변화 감지 리스너 등록
 */
export const watchDeviceChanges = (callback) => {
    // 네트워크 변화 감지
    if ('connection' in navigator) {
        const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
        if (connection) {
            connection.addEventListener('change', () => {
                callback({ type: 'network', info: getDeviceInfo() });
            });
        }
    }

    // 다크 모드 변화 감지
    if (window.matchMedia) {
        const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
        darkModeQuery.addEventListener('change', () => {
            callback({ type: 'theme', info: getDeviceInfo() });
        });
    }

    // 화면 크기 변화 감지
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            callback({ type: 'resize', info: getDeviceInfo() });
        }, 250);
    });
};

export default {
    getDeviceType,
    isTouchDevice,
    getNetworkSpeed,
    prefersDarkMode,
    getDeviceMemory,
    getBatteryInfo,
    getPerformanceProfile,
    getRecommendedImageQuality,
    shouldEnableAnimations,
    getLazyLoadingStrategy,
    getDeviceInfo,
    watchDeviceChanges,
};
