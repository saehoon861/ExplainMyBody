import api from '../config/api';

export const authService = {
    async register(userData) {
        const response = await api.post('/auth/register', userData);
        return response.data;
    },

    async login(credentials) {
        const response = await api.post('/auth/login', credentials);
        return response.data;
    },

    async getCurrentUser(userId) {
        const response = await api.get(`/auth/me?user_id=${userId}`);
        return response.data;
    },
};
