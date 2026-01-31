import apiClient from '@/shared/lib/axios';

interface LoginRequest {
    email: string;
    password: string;
}

interface LoginResponse {
    access_token: string;
    token_type: string;
}

export const authApi = {
    login: async (credentials: LoginRequest): Promise<LoginResponse> => {
        const response = await apiClient.post('/auth/login', credentials);
        return response.data;
    },

    logout: async (): Promise<void> => {
        await apiClient.post('/auth/logout');
    },
};
