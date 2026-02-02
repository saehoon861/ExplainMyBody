import { useState, useEffect } from 'react';
import {
    getDeviceInfo,
    watchDeviceChanges,
    shouldEnableAnimations,
    getDeviceType,
} from '../utils/deviceDetection';

/**
 * 지능적 적응 레이아웃 훅
 *
 * 디바이스 특성에 따라 자동으로 UI를 최적화합니다.
 *
 * @returns {Object} 디바이스 정보 및 적응형 설정
 */
export const useAdaptiveLayout = () => {
    const [deviceInfo, setDeviceInfo] = useState({
        type: 'desktop',
        isTouch: false,
        networkSpeed: 'fast',
        prefersDark: false,
        memory: 4,
        battery: { level: 1.0, charging: true },
        performanceProfile: 'high',
        recommendedImageQuality: 'high',
        shouldEnableAnimations: true,
        lazyLoadingStrategy: 'minimal',
    });

    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        // 초기 디바이스 정보 로드
        const loadDeviceInfo = async () => {
            try {
                const info = await getDeviceInfo();
                setDeviceInfo(info);
                setIsLoading(false);

                // 개발 모드에서 정보 출력
                if (process.env.NODE_ENV === 'development') {
                    console.log('🔍 Device Info (Intelligent Adaptation):', info);
                }
            } catch (error) {
                console.error('Failed to load device info:', error);
                // 오류 발생 시에도 기본값으로 계속 진행
                setIsLoading(false);
            }
        };

        loadDeviceInfo();

        // 변화 감지
        const unsubscribe = watchDeviceChanges(async ({ type }) => {
            const info = await getDeviceInfo();
            setDeviceInfo(info);

            if (process.env.NODE_ENV === 'development') {
                console.log(`🔄 Device Change (${type}):`, info);
            }
        });

        return () => {
            // cleanup은 현재 구현에서 필요 없음
        };
    }, []);

    // 유틸리티 함수들
    const isMobile = deviceInfo.type === 'mobile';
    const isTablet = deviceInfo.type === 'tablet';
    const isDesktop = deviceInfo.type === 'desktop';
    const isSlowNetwork = deviceInfo.networkSpeed === 'slow';
    const isLowPerformance = deviceInfo.performanceProfile === 'low';

    // CSS 클래스 생성
    const getAdaptiveClasses = () => {
        const classes = [];

        classes.push(`device-${deviceInfo.type}`);
        classes.push(`network-${deviceInfo.networkSpeed}`);
        classes.push(`performance-${deviceInfo.performanceProfile}`);

        if (deviceInfo.isTouch) classes.push('touch-device');
        if (!deviceInfo.shouldEnableAnimations) classes.push('reduce-motion');
        if (deviceInfo.prefersDark) classes.push('prefers-dark');

        return classes.join(' ');
    };

    // 이미지 소스 선택 헬퍼
    const getOptimizedImageSrc = (sources) => {
        const quality = deviceInfo.recommendedImageQuality;

        if (quality === 'low' && sources.low) return sources.low;
        if (quality === 'medium' && sources.medium) return sources.medium;
        return sources.high || sources.medium || sources.low;
    };

    return {
        deviceInfo,
        isLoading,
        isMobile,
        isTablet,
        isDesktop,
        isSlowNetwork,
        isLowPerformance,
        getAdaptiveClasses,
        getOptimizedImageSrc,
    };
};

export default useAdaptiveLayout;
