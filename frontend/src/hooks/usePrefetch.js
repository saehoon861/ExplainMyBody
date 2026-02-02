import { useEffect } from 'react';

/**
 * 브라우저가 유휴 상태(Idle)일 때 지정된 라우트(리소스)를 미리 가져옵니다.
 * Edge Native Architecture - Phase 3: Resource Prefetching
 * @param {string[]} routes - 프리페치할 라우트/리소스 URL 배열
 */
export const usePrefetch = (routes) => {
    useEffect(() => {
        // requestIdleCallback 지원 여부 확인
        if ('requestIdleCallback' in window) {
            const handle = requestIdleCallback(() => {
                routes.forEach((route) => {
                    // 이미 존재하는지 확인
                    if (document.querySelector(`link[href="${route}"]`)) return;

                    const link = document.createElement('link');
                    link.rel = 'prefetch';
                    // JS 모듈인 경우 script, 그 외에는 적절히 설정 (여기선 script 가정)
                    link.as = 'script';
                    link.href = route;
                    document.head.appendChild(link);
                });
            });

            return () => cancelIdleCallback(handle);
        } else {
            // Fallback: setTimeout으로 지연 실행
            const timer = setTimeout(() => {
                routes.forEach((route) => {
                    if (document.querySelector(`link[href="${route}"]`)) return;
                    const link = document.createElement('link');
                    link.rel = 'prefetch';
                    link.as = 'script';
                    link.href = route;
                    document.head.appendChild(link);
                });
            }, 3000);
            return () => clearTimeout(timer);
        }
    }, [routes]);
};
