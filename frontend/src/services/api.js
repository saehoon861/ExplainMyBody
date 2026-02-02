/**
 * API 기본 설정
 * 백엔드 개발자를 위한 참고사항:
 * - 모든 API 호출의 기본 설정
 * - 백엔드 URL: /api (프록시 설정됨)
 */

const API_BASE_URL = '/api';

/**
 * API 요청 헬퍼 함수
 */
export const apiRequest = async (endpoint, options = {}) => {
    const url = `${API_BASE_URL}${endpoint}`;
    const config = {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers,
        },
        ...options,
    };

    try {
        const response = await fetch(url, config);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error(`API Error (${endpoint}):`, error);
        throw error;
    }
};

/**
 * FormData 요청 헬퍼 함수 (파일 업로드용)
 */
export const apiFormDataRequest = async (endpoint, formData, options = {}) => {
    const url = `${API_BASE_URL}${endpoint}`;
    const config = {
        method: 'POST',
        body: formData,
        ...options,
        // Content-Type은 자동 설정됨 (multipart/form-data)
    };

    try {
        const response = await fetch(url, config);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error(`API Error (${endpoint}):`, error);
        throw error;
    }
};
