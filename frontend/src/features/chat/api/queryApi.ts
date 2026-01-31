import apiClient from '@/shared/lib/axios';
import { QueryResponse } from '@/shared/types/api';

export const queryApi = {
    query: async (question: string): Promise<QueryResponse> => {
        const response = await apiClient.post('/query', { question });
        return response.data;
    },

    webSearch: async (question: string): Promise<QueryResponse> => {
        const response = await apiClient.post('/query/web-search', { question });
        return response.data;
    },
};
