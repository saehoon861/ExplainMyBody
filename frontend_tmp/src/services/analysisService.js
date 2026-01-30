import api from '../config/api';

export const analysisService = {
    // 기존 분석 API (레거시 - 추후 제거 예정)
    async analyzeHealthRecord(userId, recordId) {
        const response = await api.post(
            `/analysis/${recordId}?user_id=${userId}`
        );
        return response.data;
    },

    async getAnalysisReport(reportId) {
        const response = await api.get(`/analysis/${reportId}`);
        return response.data;
    },

    async getAnalysisByRecord(recordId) {
        const response = await api.get(`/analysis/record/${recordId}`);
        return response.data;
    },

    async getUserAnalysisReports(userId, limit = 10) {
        const response = await api.get(`/analysis/user/${userId}?limit=${limit}`);
        return response.data;
    },

    // LLM1: 건강 상태 분석용 input 데이터 준비
    async prepareStatusAnalysis(userId, recordId) {
        const response = await api.get(
            `/health-records/${recordId}/analysis/prepare?user_id=${userId}`
        );
        return response.data;
    },

    // LLM 분석 실행 (실제 AI 분석 호출)
    async analyzeWithLLM(userId, recordId) {
        const response = await api.post(
            `/analysis/${recordId}?user_id=${userId}`
        );
        return response.data;
    },

    // AI와 채팅 (분석 결과에 대한 질문)
    async chatWithAnalysis(reportId, message, threadId) {
        const response = await api.post(
            `/analysis/${reportId}/chat`,
            {
                message: message,
                thread_id: threadId
            }
        );
        return response.data;
    },
};
