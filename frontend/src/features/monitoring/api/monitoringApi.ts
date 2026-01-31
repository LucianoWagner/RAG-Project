import apiClient from '@/shared/lib/axios';
import { HealthResponse, CacheStats } from '@/shared/types/api';

export const monitoringApi = {
    health: async (): Promise<HealthResponse> => {
        const response = await apiClient.get('/health');
        return response.data;
    },

    cacheStats: async (): Promise<CacheStats> => {
        const response = await apiClient.get('/analytics/cache');
        return response.data;
    },

    metrics: async (): Promise<string> => {
        const response = await apiClient.get('/metrics');
        return response.data;
    },
};
