/**
 * 인증 관련 API 서비스
 *
 * 📍 사용 위치: pages/Auth/ (Login.jsx, Signup.jsx)
 *
 * 백엔드 API 엔드포인트:
 * - POST /api/auth/register - 회원가입
 * - POST /api/auth/login - 로그인
 * - PUT /api/users/{user_id}/goal - 사용자 목표 업데이트
 */

import { apiRequest } from './api';

/**
 * 회원가입
 *
 * 📍 사용 위치: pages/Auth/Signup.jsx
 *
 * 기능:
 * - 새로운 사용자 계정 생성
 * - 이메일, 비밀번호, 기본 정보(신장, 체중 등) 저장
 * - 회원가입 성공 시 사용자 정보 반환
 *
 * @param {Object} userData - 회원가입 정보
 * @param {string} userData.email - 이메일 (필수)
 * @param {string} userData.password - 비밀번호 (필수)
 * @param {string} userData.gender - 성별 ("male" | "female")
 * @param {number} userData.height - 신장 (cm)
 * @param {number} userData.age - 나이
 * @param {number} userData.start_weight - 시작 체중 (kg)
 * @param {number} userData.target_weight - 목표 체중 (kg)
 * @param {string} userData.goal_type - 목표 타입 ("감량" | "유지" | "증량" | "재활")
 * @param {string} userData.goal_description - 목표 상세 설명 (선택)
 *
 * @returns {Promise<Object>} 생성된 사용자 정보
 * @returns {number} return.id - 사용자 ID
 * @returns {string} return.email - 이메일
 * @returns {string} return.gender - 성별
 * @returns {number} return.height - 신장
 *
 * @example
 * const userData = {
 *   email: "test@example.com",
 *   password: "password123",
 *   gender: "male",
 *   height: 175,
 *   age: 30,
 *   start_weight: 80,
 *   target_weight: 75,
 *   goal_type: "감량"
 * };
 * const user = await register(userData);
 * console.log(user.id); // 1
 */
export const register = async (userData) => {
    return await apiRequest('/auth/register', {
        method: 'POST',
        body: JSON.stringify(userData),
    });
};

/**
 * 로그인
 *
 * 📍 사용 위치: pages/Auth/Login.jsx
 *
 * 기능:
 * - 이메일과 비밀번호로 로그인
 * - 로그인 성공 시 사용자 전체 정보 반환
 * - 반환된 정보는 localStorage에 저장됨
 *
 * @param {string} email - 이메일 주소
 * @param {string} password - 비밀번호
 *
 * @returns {Promise<Object>} 사용자 정보
 * @returns {number} return.id - 사용자 ID
 * @returns {string} return.email - 이메일
 * @returns {string} return.gender - 성별
 * @returns {number} return.height - 신장
 * @returns {number} return.age - 나이
 * @returns {number} return.start_weight - 시작 체중
 * @returns {number} return.target_weight - 목표 체중
 * @returns {string} return.goal_type - 목표 타입
 * @returns {Object} return.inbody_data - 최근 인바디 데이터 (있는 경우)
 *
 * @throws {Error} 이메일 또는 비밀번호 불일치
 *
 * @example
 * try {
 *   const user = await login("test@example.com", "password123");
 *   localStorage.setItem('user', JSON.stringify(user));
 *   // 대시보드로 이동
 * } catch (error) {
 *   alert("로그인 실패: " + error.message);
 * }
 */
export const login = async (email, password) => {
    return await apiRequest('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
    });
};

/**
 * 사용자 목표 업데이트
 *
 * 📍 사용 위치: pages/Dashboard/Dashboard.jsx (목표 수정 모달)
 *
 * 기능:
 * - 사용자의 운동 목표 정보 수정
 * - 시작 체중, 목표 체중, 목표 타입 변경 가능
 * - 업데이트 후 최신 사용자 정보 반환
 *
 * @param {number} userId - 사용자 ID
 * @param {Object} goalData - 목표 데이터
 * @param {number} goalData.start_weight - 시작 체중 (kg)
 * @param {number} goalData.target_weight - 목표 체중 (kg)
 * @param {string} goalData.goal_type - 목표 타입 ("감량, 유지, 증량, 재활" 등)
 * @param {string} goalData.goal_description - 목표 상세 (예: "허리 재활, 어깨 재활")
 *
 * @returns {Promise<Object>} 업데이트된 사용자 정보
 *
 * @throws {Error} 사용자를 찾을 수 없거나 업데이트 실패
 *
 * @example
 * // 대시보드에서 목표 수정
 * const goalData = {
 *   start_weight: 80,
 *   target_weight: 75,
 *   goal_type: "감량, 재활",
 *   goal_description: "허리 재활, 무릎 재활"
 * };
 * const updatedUser = await updateUserGoal(userId, goalData);
 * localStorage.setItem('user', JSON.stringify(updatedUser));
 */
export const updateUserGoal = async (userId, goalData) => {
    return await apiRequest(`/users/${userId}/goal`, {
        method: 'PUT',
        body: JSON.stringify(goalData),
    });
};
