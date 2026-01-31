import { useQuery } from '@tanstack/react-query';
import { monitoringApi } from '../api/monitoringApi';
import { HealthResponse } from '@/shared/types/api';

export const useHealth = () => {
    return useQuery<HealthResponse, Error>({
        queryKey: ['health'],
        queryFn: monitoringApi.health,
        refetchInterval: 30000, // Refetch every 30 seconds
    });
};
