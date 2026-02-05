/**
 * 인바디 OCR 관련 API 서비스
 *
 * 📍 사용 위치: pages/InBody/InBodyAnalysis.jsx
 *
 * 백엔드 API 엔드포인트:
 * - POST /api/health-records/ocr/extract - OCR 데이터 추출
 * - POST /api/health-records/ocr/validate - OCR 데이터 저장
 * - GET /api/health-records/user/{user_id} - 사용자 건강 기록 조회
 */

import { apiRequest, apiFormDataRequest } from './api';

/**
 * 인바디 이미지 OCR 처리
 *
 * 📍 사용 위치: pages/InBody/InBodyAnalysis.jsx (이미지 업로드 후 분석 시작)
 *
 * 기능:
 * - 사용자가 업로드한 인바디 결과지 이미지를 서버로 전송
 * - AI OCR이 이미지에서 텍스트 추출 (체중, 골격근량, BMI 등)
 * - 추출된 데이터를 구조화된 JSON으로 반환
 * - 프론트에서 사용자가 수정 가능한 폼으로 표시
 *
 * @param {File} imageFile - 인바디 이미지 파일 (JPG, PNG)
 *
 * @returns {Promise<Object>} OCR 추출 데이터
 * @returns {Object} return.data - 추출된 인바디 데이터
 * @returns {Object} return.data.기본정보 - 기본 정보 (성별, 신장, 연령)
 * @returns {Object} return.data.체성분 - 체성분 (체수분, 단백질, 무기질, 체지방)
 * @returns {Object} return.data.체중관리 - 체중 관리 (체중, 골격근량, 체지방량 등)
 * @returns {Object} return.data.비만분석 - 비만 분석 (BMI, 체지방률, 내장지방 등)
 * @returns {Object} return.data.연구항목 - 연구 항목 (제지방량, 기초대사량 등)
 * @returns {Object} return.data.부위별근육분석 - 부위별 근육 상태
 * @returns {Object} return.data.부위별체지방분석 - 부위별 체지방 상태
 *
 * @throws {Error} OCR 처리 실패 또는 이미지 인식 불가
 *
 * @example
 * // 사용자가 이미지 업로드 후
 * const imageFile = event.target.files[0];
 * try {
 *   const result = await extractInbodyData(imageFile);
 *   console.log(result.data.체중관리.체중); // "77.7"
 *   console.log(result.data.체중관리.골격근량); // "35.2"
 *   // 이 데이터를 폼에 표시하여 사용자가 수정 가능
 * } catch (error) {
 *   alert("이미지를 인식할 수 없습니다. 다시 촬영해주세요.");
 * }
 */
export const extractInbodyData = async (imageFile) => {
    const formData = new FormData();
    formData.append('image', imageFile);

    return await apiFormDataRequest('/health-records/ocr/extract', formData);
};

/**
 * 인바디 데이터 저장
 *
 * 📍 사용 위치: pages/InBody/InBodyAnalysis.jsx (저장 버튼 클릭 시)
 *
 * 기능:
 * - OCR로 추출하고 사용자가 수정한 인바디 데이터를 DB에 저장
 * - 건강 기록으로 저장되어 나중에 조회 가능
 * - 대시보드 그래프에 반영됨
 *
 * @param {number} userId - 사용자 ID (localStorage에서 가져옴)
 * @param {Object} inbodyData - 인바디 데이터 (OCR 추출 + 사용자 수정)
 * @param {Object} inbodyData.기본정보 - 기본 정보
 * @param {Object} inbodyData.체성분 - 체성분
 * @param {Object} inbodyData.체중관리 - 체중 관리
 * @param {Object} inbodyData.비만분석 - 비만 분석
 * @param {Object} inbodyData.연구항목 - 연구 항목
 * @param {Object} inbodyData.부위별근육분석 - 부위별 근육
 * @param {Object} inbodyData.부위별체지방분석 - 부위별 체지방
 *
 * @returns {Promise<Object>} 저장된 건강 기록
 * @returns {number} return.id - 건강 기록 ID
 * @returns {number} return.user_id - 사용자 ID
 * @returns {Object} return.measurements - 저장된 측정값
 * @returns {string} return.created_at - 생성 일시
 *
 * @throws {Error} 저장 실패 또는 유효하지 않은 데이터
 *
 * @example
 * // 사용자가 데이터 확인 후 저장 버튼 클릭
 * const userData = JSON.parse(localStorage.getItem('user'));
 * const inbodyData = {
 *   기본정보: { 성별: "남", 신장: 175, 연령: 30 },
 *   체중관리: { 체중: 77.7, 골격근량: 35.2, ... },
 *   // ... 나머지 데이터
 * };
 * const savedRecord = await saveInbodyData(userData.id, inbodyData);
 * alert("저장되었습니다!");
 */
export const saveInbodyData = async (userId, inbodyData) => {
    return await apiRequest(`/health-records/ocr/validate?user_id=${userId}`, {
        method: 'POST',
        body: JSON.stringify(inbodyData),
    });
};

/**
 * 사용자 건강 기록 조회
 *
 * 📍 사용 위치: pages/InBody/InBodyAnalysis.jsx (이전 기록 탭)
 *
 * 기능:
 * - 사용자가 이전에 저장한 인바디 기록 목록 조회
 * - 날짜 역순으로 정렬되어 반환 (최신 순)
 * - 기록 클릭 시 상세 데이터 확인 가능
 *
 * @param {number} userId - 사용자 ID
 * @param {number} [limit=20] - 조회할 기록 개수 (기본 20개)
 *
 * @returns {Promise<Array>} 건강 기록 목록
 * @returns {number} return[].id - 기록 ID
 * @returns {number} return[].user_id - 사용자 ID
 * @returns {Object} return[].measurements - 측정값 (체중, 골격근량 등)
 * @returns {string} return[].body_type1 - 체형 타입 (예: "표준", "비만")
 * @returns {string} return[].created_at - 기록 생성 일시
 *
 * @example
 * // 이전 기록 탭 클릭 시
 * const userData = JSON.parse(localStorage.getItem('user'));
 * const records = await getUserHealthRecords(userData.id, 10);
 * records.forEach(record => {
 *   console.log(`${record.created_at}: 체중 ${record.measurements.체중관리.체중}kg`);
 * });
 * // "2025-01-30: 체중 77.7kg"
 * // "2025-01-15: 체중 78.5kg"
 */
export const getUserHealthRecords = async (userId, limit = 20) => {
    return await apiRequest(`/health-records/user/${userId}?limit=${limit}`);
};

/**
 * 인바디 이미지 업로드 및 저장 (원스텝)
 *
 * 📍 사용 위치: pages/Chatbot/ChatbotSelector.jsx (스캔 팝업에서 업로드 시)
 *
 * 기능:
 * - 인바디 검사지 이미지를 업로드하고 OCR 추출 후 바로 저장
 * - extractInbodyData + saveInbodyData를 한 번에 처리
 * - 챗봇 선택 화면에서 빠른 업로드용
 *
 * @param {number} userId - 사용자 ID
 * @param {File} imageFile - 인바디 이미지 파일 (JPG, PNG)
 *
 * @returns {Promise<Object>} 저장된 건강 기록
 *
 * @throws {Error} OCR 처리 또는 저장 실패
 */
export const uploadInbodyImage = async (userId, imageFile) => {
    // 1. OCR로 이미지에서 데이터 추출
    const extractResult = await extractInbodyData(imageFile);

    // 2. 추출된 데이터를 바로 저장
    const savedRecord = await saveInbodyData(userId, extractResult.data || extractResult);

    return savedRecord;
};
