import { useMutation } from '@tanstack/react-query';
import { queryApi } from '../api/queryApi';
import { toast } from 'sonner';
import { QueryResponse } from '@/shared/types/api';

export const useQuery = () => {
    return useMutation<QueryResponse, Error, string>({
        mutationFn: (question: string) => queryApi.query(question),
        onError: (error) => {
            toast.error('Failed to process query: ' + error.message);
        },
    });
};

export const useWebSearch = () => {
    return useMutation<QueryResponse, Error, string>({
        mutationFn: (question: string) => queryApi.webSearch(question),
        onError: (error) => {
            toast.error('Web search failed: ' + error.message);
        },
    });
};
