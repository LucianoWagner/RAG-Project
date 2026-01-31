import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, Loader2 } from 'lucide-react';
import { cn } from '@/shared/lib/utils';
import { useDocumentUpload } from '../hooks/useDocuments';

export function UploadZone() {
    const uploadMutation = useDocumentUpload();

    const onDrop = useCallback((acceptedFiles: File[]) => {
        if (acceptedFiles[0]) {
            uploadMutation.mutate(acceptedFiles[0]);
        }
    }, [uploadMutation]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: { 'application/pdf': ['.pdf'] },
        multiple: false,
        disabled: uploadMutation.isPending,
    });

    return (
        <div
            {...getRootProps()}
            className={cn(
                'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
                isDragActive && 'border-foreground bg-secondary/50',
                !isDragActive && 'border-border hover:border-foreground/50 hover:bg-secondary/20',
                uploadMutation.isPending && 'cursor-not-allowed opacity-60'
            )}
        >
            <input {...getInputProps()} />

            {uploadMutation.isPending ? (
                <div className="flex flex-col items-center gap-2">
                    <Loader2 className="h-12 w-12 animate-spin text-foreground" />
                    <p className="text-sm text-muted-foreground">Uploading and processing...</p>
                </div>
            ) : (
                <div className="flex flex-col items-center gap-2">
                    <Upload className="h-12 w-12 text-muted-foreground" />
                    {isDragActive ? (
                        <p className="text-sm font-medium">Drop the PDF here</p>
                    ) : (
                        <>
                            <p className="text-sm font-medium">Drag & drop a PDF here</p>
                            <p className="text-xs text-muted-foreground">or click to select a file</p>
                        </>
                    )}
                </div>
            )}
        </div>
    );
}
