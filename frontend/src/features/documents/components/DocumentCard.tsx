import { FileText, Trash2, Clock } from 'lucide-react';
import { Card, CardContent } from '@/shared/components/ui/Card';
import { Button } from '@/shared/components/ui/Button';
import { DocumentMetadata } from '@/shared/types/api';
import { formatBytes, formatDate } from '@/shared/lib/utils';
import { useDocumentDelete } from '../hooks/useDocuments';

interface DocumentCardProps {
    document: DocumentMetadata;
}

export function DocumentCard({ document }: DocumentCardProps) {
    const deleteMutation = useDocumentDelete();

    const handleDelete = () => {
        if (confirm(`Delete ${document.filename}?`)) {
            deleteMutation.mutate(document.filename);
        }
    };

    return (
        <Card className="hover:border-foreground/30 transition-colors">
            <CardContent className="p-4">
                <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3 flex-1 min-w-0">
                        <div className="shrink-0 h-10 w-10 rounded-lg border border-border flex items-center justify-center bg-secondary/50">
                            <FileText className="h-5 w-5 text-foreground" />
                        </div>

                        <div className="flex-1 min-w-0">
                            <h4 className="font-medium text-sm truncate" title={document.filename}>
                                {document.filename}
                            </h4>

                            <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                                <span>{document.chunks_count} chunks</span>
                                <span>•</span>
                                <span>{formatBytes(document.file_size_bytes)}</span>
                                {document.pages_count && (
                                    <>
                                        <span>•</span>
                                        <span>{document.pages_count} pages</span>
                                    </>
                                )}
                            </div>

                            <div className="flex items-center gap-1 mt-2 text-xs text-muted-foreground">
                                <Clock className="h-3 w-3" />
                                <span>{formatDate(new Date(document.upload_timestamp))}</span>
                            </div>
                        </div>
                    </div>

                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={handleDelete}
                        disabled={deleteMutation.isPending}
                        className="shrink-0 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950"
                    >
                        <Trash2 className="h-4 w-4" />
                    </Button>
                </div>
            </CardContent>
        </Card>
    );
}
