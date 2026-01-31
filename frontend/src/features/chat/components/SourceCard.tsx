import { FileText } from 'lucide-react';
import { Card } from '@/shared/components/ui/Card';
import { SourceInfo } from '@/shared/types/models';

interface SourceCardProps {
    source: SourceInfo;
    index: number;
}

export function SourceCard({ source, index }: SourceCardProps) {
    return (
        <Card className="p-3 hover:border-foreground/30 transition-colors">
            <div className="flex items-start gap-2">
                <FileText className="h-4 w-4 mt-0.5 shrink-0 text-muted-foreground" />
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-medium">Source {index + 1}</span>
                        {source.source && (
                            <span className="text-xs text-muted-foreground truncate">
                                {source.source}
                                {source.page && ` (p.${source.page})`}
                            </span>
                        )}
                        <span className="text-xs px-1.5 py-0.5 rounded bg-secondary text-foreground ml-auto shrink-0">
                            {Math.round(source.score * 100)}%
                        </span>
                    </div>
                    <p className="text-xs text-muted-foreground line-clamp-2">
                        {source.text}
                    </p>
                </div>
            </div>
        </Card>
    );
}

interface SourceListProps {
    sources: SourceInfo[];
}

export function SourceList({ sources }: SourceListProps) {
    if (!sources || sources.length === 0) return null;

    return (
        <div className="mt-3 space-y-2">
            <p className="text-xs font-semibold text-muted-foreground">Sources:</p>
            <div className="grid gap-2">
                {sources.map((source, index) => (
                    <SourceCard key={index} source={source} index={index} />
                ))}
            </div>
        </div>
    );
}
