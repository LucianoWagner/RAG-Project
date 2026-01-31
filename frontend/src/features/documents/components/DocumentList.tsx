import { FileUp, Trash2 } from 'lucide-react';
import { Button } from '@/shared/components/ui/Button';
import { UploadZone } from './UploadZone';
import { useDeleteAllDocuments } from '../hooks/useDocuments';

export function DocumentList() {
    const deleteAllMutation = useDeleteAllDocuments();

    const handleDeleteAll = () => {
        if (confirm('Delete ALL documents? This action cannot be undone.')) {
            deleteAllMutation.mutate();
        }
    };

    return (
        <div className="h-full flex flex-col">
            <div className="p-4 border-b border-border">
                <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                        <FileUp className="h-4 w-4" />
                        <h2 className="text-sm font-semibold">Upload Documents</h2>
                    </div>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleDeleteAll}
                        disabled={deleteAllMutation.isPending}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950"
                    >
                        <Trash2 className="h-3 w-3 mr-1" />
                        Clear All
                    </Button>
                </div>
                <UploadZone />
            </div>

            <div className="flex-1 p-4">
                <div className="text-xs text-muted-foreground space-y-1">
                    <p>📄 Upload PDF documents to query them</p>
                    <p>🔍 Use the tool selector below chat to choose search mode</p>
                    <p>🌐 Switch to "Web Search" for Wikipedia queries</p>
                </div>
            </div>
        </div>
    );
}
