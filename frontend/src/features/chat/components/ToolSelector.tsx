import { FileText, Globe } from 'lucide-react';
import { cn } from '@/shared/lib/utils';

export type SearchTool = 'pdf' | 'web';

interface ToolSelectorProps {
    selected: SearchTool;
    onChange: (tool: SearchTool) => void;
    disabled?: boolean;
}

export function ToolSelector({ selected, onChange, disabled }: ToolSelectorProps) {
    return (
        <div className="flex items-center gap-2 px-4 py-2 border-t border-border bg-secondary/20">
            <span className="text-xs font-medium text-muted-foreground">Search Mode:</span>
            <div className="flex gap-1 border border-border rounded-md p-1">
                <button
                    type="button"
                    onClick={() => onChange('pdf')}
                    disabled={disabled}
                    className={cn(
                        'flex items-center gap-1.5 px-3 py-1 rounded text-xs font-medium transition-colors',
                        selected === 'pdf'
                            ? 'bg-foreground text-background'
                            : 'text-muted-foreground hover:text-foreground hover:bg-secondary',
                        disabled && 'opacity-50 cursor-not-allowed'
                    )}
                >
                    <FileText className="h-3 w-3" />
                    PDF Documents
                </button>
                <button
                    type="button"
                    onClick={() => onChange('web')}
                    disabled={disabled}
                    className={cn(
                        'flex items-center gap-1.5 px-3 py-1 rounded text-xs font-medium transition-colors',
                        selected === 'web'
                            ? 'bg-foreground text-background'
                            : 'text-muted-foreground hover:text-foreground hover:bg-secondary',
                        disabled && 'opacity-50 cursor-not-allowed'
                    )}
                >
                    <Globe className="h-3 w-3" />
                    Web Search
                </button>
            </div>
        </div>
    );
}
