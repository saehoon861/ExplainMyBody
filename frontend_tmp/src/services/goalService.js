import api from '../config/api';

export const goalService = {
    // 목표 생성
    async createGoal(userId, goalData) {
        const response = await api.post(
            `/goals/?user_id=${userId}`,
            goalData
        );
        return response.data;
    },

    // 목표 조회
    async getGoal(goalId) {
        const response = await api.get(`/goals/${goalId}`);
        return response.data;
    },

    // 사용자의 활성 목표 조회
    async getActiveGoals(userId) {
        const response = await api.get(`/goals/user/${userId}/active`);
        return response.data;
    },

    // 사용자의 모든 목표 조회
    async getAllGoals(userId) {
        const response = await api.get(`/goals/user/${userId}`);
        return response.data;
    },

    // 목표 수정
    async updateGoal(goalId, goalData) {
        const response = await api.patch(`/goals/${goalId}`, goalData);
        return response.data;
    },

    // 목표 삭제
    async deleteGoal(goalId) {
        const response = await api.delete(`/goals/${goalId}`);
        return response.data;
    },

    // 목표 완료
    async completeGoal(goalId) {
        const response = await api.post(`/goals/${goalId}/complete`);
        return response.data;
    },

    // LLM2: 주간 계획서 생성용 input 데이터 준비
    async prepareGoalPlan(userId, requestData) {
        const response = await api.post(
            `/goals/plan/prepare?user_id=${userId}`,
            requestData
        );
        return response.data;
    },
};
