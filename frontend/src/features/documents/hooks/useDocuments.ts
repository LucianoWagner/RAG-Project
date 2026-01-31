import { useMutation, useQueryClient } from '@tanstack/react-query';
import { documentsApi } from '../api/documentsApi';
import { toast } from 'sonner';
import { UploadResponse } from '@/shared/types/api';

export const useDocumentUpload = () => {
    const queryClient = useQueryClient();

    return useMutation<UploadResponse, Error, File>({
        mutationFn: (file: File) => documentsApi.upload(file),
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ['documents'] });
            toast.success(`Document uploaded: ${data.chunks_processed} chunks processed`);
        },
        onError: (error: any) => {
            if (error.response?.status === 409) {
                const detail = error.response.data.detail;
                if (typeof detail === 'object') {
                    toast.error(`Document already exists: ${detail.original_filename}`);
                } else {
                    toast.error('Document already exists');
                }
            } else {
                toast.error('Upload failed: ' + error.message);
            }
        },
    });
};

export const useDocumentDelete = () => {
    const queryClient = useQueryClient();

    return useMutation<void, Error, string>({
        mutationFn: (filename: string) => documentsApi.delete(filename),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['documents'] });
            toast.success('Document deleted successfully');
        },
        onError: (error) => {
            toast.error('Delete failed: ' + error.message);
        },
    });
};

export const useDeleteAllDocuments = () => {
    const queryClient = useQueryClient();

    return useMutation<void, Error>({
        mutationFn: () => documentsApi.deleteAll(),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['documents'] });
            toast.success('All documents deleted successfully');
        },
        onError: (error) => {
            toast.error('Delete all failed: ' + error.message);
        },
    });
};
