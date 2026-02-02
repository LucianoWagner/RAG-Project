import { useState, useRef, useEffect } from 'react';
import { Send, Square } from 'lucide-react';
import { Button } from '@/shared/components/ui/Button';
import { Textarea } from '@/shared/components/ui/Textarea';
import { ToolSelector, SearchTool } from './ToolSelector';
import { cn } from '@/shared/lib/utils';

interface ChatInputProps {
    onSend: (message: string, searchTool: SearchTool) => void;
    isLoading?: boolean;
    onStop?: () => void;
}

export function ChatInput({ onSend, isLoading, onStop }: ChatInputProps) {
    const [input, setInput] = useState('');
    const [selectedTool, setSelectedTool] = useState<SearchTool>('pdf');
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (input.trim() && !isLoading) {
            onSend(input.trim(), selectedTool);
            setInput('');
            if (textareaRef.current) {
                textareaRef.current.style.height = 'auto';
            }
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    };

    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
        }
    }, [input]);

    return (
        <div className="border-t border-border bg-background">
            <form onSubmit={handleSubmit} className="p-4">
                <div className="flex gap-2">
                    <Textarea
                        ref={textareaRef}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Type your question here..."
                        className="min-h-[44px] max-h-[200px] resize-none"
                        disabled={isLoading}
                    />
                    {isLoading && onStop ? (
                        <Button
                            type="button"
                            size="icon"
                            variant="destructive"
                            onClick={onStop}
                            className="shrink-0"
                        >
                            <Square className="h-4 w-4" />
                        </Button>
                    ) : (
                        <Button
                            type="submit"
                            size="icon"
                            disabled={!input.trim() || isLoading}
                            className={cn('shrink-0', !input.trim() && 'opacity-50')}
                        >
                            <Send className="h-4 w-4" />
                        </Button>
                    )}
                </div>
                <p className="text-xs text-muted-foreground mt-2">
                    Press <kbd className="px-1 py-0.5 rounded bg-secondary text-foreground">Enter</kbd> to send, <kbd className="px-1 py-0.5 rounded bg-secondary text-foreground">Shift + Enter</kbd> for new line
                </p>
            </form>
            <ToolSelector
                selected={selectedTool}
                onChange={setSelectedTool}
                disabled={isLoading}
            />
        </div>
    );
}
