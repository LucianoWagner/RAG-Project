import { useEffect, useRef } from 'react';
import { Message } from '@/shared/types/models';
import { MessageBubble } from './MessageBubble';
import { SourceList } from './SourceCard';

interface MessageListProps {
    messages: Message[];
    onUploadClick?: () => void;
    onWebSearchClick?: (question: string) => void;
}

export function MessageList({ messages, onUploadClick, onWebSearchClick }: MessageListProps) {
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    if (messages.length === 0) {
        return (
            <div className="flex-1 flex items-center justify-center p-8">
                <div className="text-center space-y-2">
                    <h2 className="text-2xl font-semibold">Welcome to RAG PDF System</h2>
                    <p className="text-muted-foreground">
                        Upload a PDF document and start asking questions
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex-1 overflow-y-auto">
            {messages.map((message) => (
                <div key={message.id}>
                    <MessageBubble
                        message={message}
                        onUploadClick={onUploadClick}
                        onWebSearchClick={onWebSearchClick}
                    />
                    {message.sources && message.sources.length > 0 && (
                        <div className="px-4 pb-3 bg-secondary/30">
                            <SourceList sources={message.sources} />
                        </div>
                    )}
                </div>
            ))}
            <div ref={bottomRef} />
        </div>
    );
}
