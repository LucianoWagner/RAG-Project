import apiClient from '@/shared/lib/axios';
import { UploadResponse, DocumentMetadata } from '@/shared/types/api';

export const documentsApi = {
    upload: async (file: File): Promise<UploadResponse> => {
        const formData = new FormData();
        formData.append('file', file);

        const response = await apiClient.post('/documents/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    list: async (): Promise<DocumentMetadata[]> => {
        const response = await apiClient.get('/documents');
        return response.data;
    },

    delete: async (filename: string): Promise<void> => {
        await apiClient.delete(`/documents/${filename}`);
    },

    deleteAll: async (): Promise<void> => {
        await apiClient.delete('/documents/all');
    },
};
