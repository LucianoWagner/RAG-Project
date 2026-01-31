import ReactMarkdown from 'react-markdown';
import { motion } from 'framer-motion';
import { User, Bot, Upload, Globe } from 'lucide-react';
import { Message } from '@/shared/types/models';
import { cn } from '@/shared/lib/utils';
import { LoadingSpinner } from '@/shared/components/LoadingSpinner';
import { Button } from '@/shared/components/ui/Button';

interface MessageBubbleProps {
    message: Message;
    onUploadClick?: () => void;
    onWebSearchClick?: (question: string) => void;
}

export function MessageBubble({ message, onUploadClick, onWebSearchClick }: MessageBubbleProps) {
    const isUser = message.role === 'user';

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
            className={cn('flex gap-3 px-4 py-3', !isUser && 'bg-secondary/30')}
        >
            <div className={cn(
                'shrink-0 h-8 w-8 rounded-full flex items-center justify-center',
                isUser ? 'bg-foreground text-background' : 'bg-background border border-border'
            )}>
                {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
            </div>

            <div className="flex-1 space-y-2 overflow-hidden">
                <div className="flex items-center gap-2">
                    <span className="font-semibold text-sm">
                        {isUser ? 'You' : 'Assistant'}
                    </span>
                    <span className="text-xs text-muted-foreground">
                        {message.timestamp.toLocaleTimeString('es-ES', {
                            hour: '2-digit',
                            minute: '2-digit',
                        })}
                    </span>
                    {message.confidence_score !== undefined && (
                        <span className="text-xs px-2 py-0.5 rounded bg-muted text-muted-foreground">
                            {Math.round(message.confidence_score * 100)}% confident
                        </span>
                    )}
                </div>

                {message.isLoading ? (
                    <div className="flex items-center gap-2">
                        <LoadingSpinner size="sm" />
                        <span className="text-sm text-muted-foreground">Thinking...</span>
                    </div>
                ) : (
                    <>
                        <div className="prose prose-sm max-w-none">
                            <ReactMarkdown>{message.content}</ReactMarkdown>
                        </div>

                        {/* Suggested Action Buttons */}
                        {message.suggested_action === 'upload_or_search' && (
                            <div className="flex gap-2 mt-3">
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={onUploadClick}
                                    className="flex items-center gap-2"
                                >
                                    <Upload className="h-3 w-3" />
                                    Subir PDF
                                </Button>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => onWebSearchClick?.(message.content)}
                                    className="flex items-center gap-2"
                                >
                                    <Globe className="h-3 w-3" />
                                    Buscar en Internet
                                </Button>
                            </div>
                        )}

                        {message.suggested_action === 'web_search' && (
                            <div className="mt-3">
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => onWebSearchClick?.(message.content)}
                                    className="flex items-center gap-2"
                                >
                                    <Globe className="h-3 w-3" />
                                    Buscar en Internet
                                </Button>
                            </div>
                        )}
                    </>
                )}
            </div>
        </motion.div>
    );
}
