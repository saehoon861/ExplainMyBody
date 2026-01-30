import api from '../config/api';

export const weeklyPlanService = {
    // AI 주간 계획서 생성
    async generateWeeklyPlan(userId, requestData) {
        const response = await api.post(
            `/weekly-plans/generate?user_id=${userId}`,
            requestData
        );
        return response.data;
    },

    // 주간 계획에 대한 채팅
    async chatWithPlan(planId, threadId, message) {
        const response = await api.post(
            `/weekly-plans/${planId}/chat`,
            {
                thread_id: threadId,
                message: message
            }
        );
        return response.data;
    },

    // 사용자의 주간 계획 목록 조회
    async getUserPlans(userId, limit = 10) {
        const response = await api.get(`/weekly-plans/user/${userId}?limit=${limit}`);
        return response.data;
    },

    // 특정 주간 계획 조회
    async getPlanById(planId) {
        const response = await api.get(`/weekly-plans/${planId}`);
        return response.data;
    },

    // 주간 계획 수정
    async updatePlan(planId, updateData) {
        const response = await api.patch(`/weekly-plans/${planId}`, updateData);
        return response.data;
    },

    // 주간 계획 삭제
    async deletePlan(planId) {
        const response = await api.delete(`/weekly-plans/${planId}`);
        return response.data;
    }
};
