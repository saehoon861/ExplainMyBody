import api from '../config/api';

export const healthService = {
    async extractInbodyFromImage(imageFile) {
        const formData = new FormData();
        formData.append('image', imageFile);

        const response = await api.post('/health-records/ocr/extract', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    async validateAndSaveInbody(userId, inbodyData) {
        const response = await api.post(
            `/health-records/ocr/validate?user_id=${userId}`,
            inbodyData
        );
        return response.data;
    },

    async createHealthRecord(userId, recordData) {
        const response = await api.post(
            `/health-records/?user_id=${userId}`,
            recordData
        );
        return response.data;
    },

    async getHealthRecord(recordId) {
        const response = await api.get(`/health-records/${recordId}`);
        return response.data;
    },

    async getUserHealthRecords(userId, limit = 10) {
        const response = await api.get(`/health-records/user/${userId}?limit=${limit}`);
        return response.data;
    },

    async getLatestHealthRecord(userId) {
        const response = await api.get(`/health-records/user/${userId}/latest`);
        return response.data;
    },

    // LLM1: 건강 기록 분석용 input 데이터 준비
    async prepareStatusAnalysis(userId, recordId) {
        const response = await api.get(
            `/health-records/${recordId}/analysis/prepare?user_id=${userId}`
        );
        return response.data;
    },
};
