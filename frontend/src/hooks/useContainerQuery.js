import { useState, useEffect, useRef } from 'react';

/**
 * 컨테이너 크기를 감지하는 Hook
 * ResizeObserver를 사용하여 실시간 크기 추적
 *
 * @param {Object} options - 옵션
 * @param {number} options.debounce - 디바운스 시간 (ms)
 * @returns {Object} 컨테이너 정보
 */
export const useContainerQuery = (options = {}) => {
    const { debounce = 100 } = options;
    const ref = useRef(null);
    const [containerSize, setContainerSize] = useState({
        width: 0,
        height: 0,
    });

    useEffect(() => {
        if (!ref.current) return;

        let timeoutId;
        const resizeObserver = new ResizeObserver((entries) => {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => {
                for (const entry of entries) {
                    const { width, height } = entry.contentRect;
                    setContainerSize({ width, height });
                }
            }, debounce);
        });

        resizeObserver.observe(ref.current);

        // 초기 크기 설정
        if (ref.current) {
            const { width, height } = ref.current.getBoundingClientRect();
            setContainerSize({ width, height });
        }

        return () => {
            clearTimeout(timeoutId);
            resizeObserver.disconnect();
        };
    }, [debounce]);

    // 편의 메서드
    const isSmall = containerSize.width < 500;
    const isMedium = containerSize.width >= 500 && containerSize.width < 900;
    const isLarge = containerSize.width >= 900;

    return {
        ref,
        width: containerSize.width,
        height: containerSize.height,
        isSmall,
        isMedium,
        isLarge,
    };
};

/**
 * 컨테이너 크기에 따라 다른 값을 반환하는 Hook
 *
 * @param {Object} values - 크기별 값
 * @param {any} values.small - 작은 크기일 때 값
 * @param {any} values.medium - 중간 크기일 때 값
 * @param {any} values.large - 큰 크기일 때 값
 * @param {any} values.default - 기본값
 * @returns {any} 현재 크기에 맞는 값
 *
 * @example
 * const columns = useResponsiveValue({ small: 1, medium: 2, large: 3 });
 */
export const useResponsiveValue = (values) => {
    const { isSmall, isMedium, isLarge } = useContainerQuery();

    if (isLarge && values.large !== undefined) return values.large;
    if (isMedium && values.medium !== undefined) return values.medium;
    if (isSmall && values.small !== undefined) return values.small;

    return values.default || values.small;
};

export default useContainerQuery;
