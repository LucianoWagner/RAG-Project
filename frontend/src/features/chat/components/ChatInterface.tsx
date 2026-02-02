import { useState, useRef, ChangeEvent, useEffect } from 'react';
import { Message } from '@/shared/types/models';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { useStreamingQuery } from '../hooks/useStreamingQuery';
import { useDocumentUpload } from '@/features/documents/hooks/useDocuments';
import { generateId } from '@/shared/lib/utils';
import { SearchTool } from './ToolSelector';
import { toast } from 'sonner';

export function ChatInterface() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [currentQuestion, setCurrentQuestion] = useState('');
    const fileInputRef = useRef<HTMLInputElement>(null);
    const streamingMessageIdRef = useRef<string | null>(null);

    const streaming = useStreamingQuery();
    const uploadMutation = useDocumentUpload();

    const handleSendMessage = async (content: string, searchTool: SearchTool) => {
        setCurrentQuestion(content);

        // Add user message
        const userMessage: Message = {
            id: generateId(),
            role: 'user',
            content,
            timestamp: new Date(),
        };
        setMessages((prev) => [...prev, userMessage]);

        // Add streaming placeholder message
        const streamingMessageId = generateId();
        streamingMessageIdRef.current = streamingMessageId;

        const placeholderMessage: Message = {
            id: streamingMessageId,
            role: 'assistant',
            content: '',
            timestamp: new Date(),
            isStreaming: true,
            statusMessage: '🔍 Analizando...',
        };
        setMessages((prev) => [...prev, placeholderMessage]);

        // Start streaming
        const mode = searchTool === 'web' ? 'web' : 'pdf';
        await streaming.startStream(content, mode);
    };

    // Update streaming message as tokens arrive
    useEffect(() => {
        if (!streamingMessageIdRef.current) return;

        setMessages((prev) =>
            prev.map((msg) =>
                msg.id === streamingMessageIdRef.current
                    ? {
                        ...msg,
                        content: streaming.error || streaming.streamedContent,
                        sources: streaming.sources,
                        statusMessage: streaming.statusMessage || undefined,
                        isStreaming: streaming.isStreaming,
                        suggested_action: streaming.suggestedAction || undefined,
                    }
                    : msg
            )
        );

        // Clear streaming message ID when done or error
        if (!streaming.isStreaming && streamingMessageIdRef.current) {
            setTimeout(() => {
                streamingMessageIdRef.current = null;
            }, 100);
        }
    }, [
        streaming.streamedContent,
        streaming.sources,
        streaming.statusMessage,
        streaming.isStreaming,
        streaming.error,
        streaming.suggestedAction,
    ]);

    const handleUploadClick = () => {
        fileInputRef.current?.click();
    };

    const handleFileSelect = async (e: ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        try {
            await uploadMutation.mutateAsync(file);
            toast.success('PDF uploaded successfully! You can now ask questions about it.');
        } catch (error) {
            // Error handling already done in mutation
        }

        // Reset file input
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    const handleWebSearchClick = async (question: string) => {
        // Trigger web search streaming
        const userMessage: Message = {
            id: generateId(),
            role: 'user',
            content: `🌐 ${question}`,
            timestamp: new Date(),
        };
        setMessages((prev) => [...prev, userMessage]);

        const streamingMessageId = generateId();
        streamingMessageIdRef.current = streamingMessageId;

        const placeholderMessage: Message = {
            id: streamingMessageId,
            role: 'assistant',
            content: '',
            timestamp: new Date(),
            isStreaming: true,
            statusMessage: '🌐 Buscando en Wikipedia...',
        };
        setMessages((prev) => [...prev, placeholderMessage]);

        // Start web search stream
        await streaming.startStream(currentQuestion || question, 'web');
    };

    const handleStopGeneration = () => {
        streaming.stopStream();
    };

    return (
        <div className="h-full flex flex-col">
            {/* Hidden file input for programmatic upload */}
            <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                onChange={handleFileSelect}
                className="hidden"
            />

            <MessageList
                messages={messages}
                onUploadClick={handleUploadClick}
                onWebSearchClick={handleWebSearchClick}
            />
            <ChatInput
                onSend={handleSendMessage}
                isLoading={streaming.isStreaming}
                onStop={streaming.isStreaming ? handleStopGeneration : undefined}
            />
        </div>
    );
}
