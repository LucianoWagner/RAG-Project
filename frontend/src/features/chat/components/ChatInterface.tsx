import { useState, useRef, ChangeEvent } from 'react';
import { Message } from '@/shared/types/models';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { useQuery as useQueryMutation, useWebSearch } from '../hooks/useQuery';
import { useDocumentUpload } from '@/features/documents/hooks/useDocuments';
import { generateId } from '@/shared/lib/utils';
import { SearchTool } from './ToolSelector';
import { toast } from 'sonner';

export function ChatInterface() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [currentQuestion, setCurrentQuestion] = useState('');
    const fileInputRef = useRef<HTMLInputElement>(null);

    const queryMutation = useQueryMutation();
    const webSearchMutation = useWebSearch();
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

        // Add loading message
        const loadingMessage: Message = {
            id: generateId(),
            role: 'assistant',
            content: '',
            timestamp: new Date(),
            isLoading: true,
        };
        setMessages((prev) => [...prev, loadingMessage]);

        try {
            let response;

            // Route to correct endpoint based on tool selection
            if (searchTool === 'web') {
                response = await webSearchMutation.mutateAsync(content);
            } else {
                response = await queryMutation.mutateAsync(content);
            }

            // Remove loading message and add response
            setMessages((prev) => {
                const withoutLoading = prev.filter((m) => m.id !== loadingMessage.id);
                return [
                    ...withoutLoading,
                    {
                        id: generateId(),
                        role: 'assistant',
                        content: response.answer,
                        timestamp: new Date(),
                        sources: response.sources,
                        confidence_score: response.confidence_score,
                        suggested_action: response.suggested_action,
                    },
                ];
            });
        } catch (error) {
            // Remove loading message and show error
            setMessages((prev) => {
                const withoutLoading = prev.filter((m) => m.id !== loadingMessage.id);
                return [
                    ...withoutLoading,
                    {
                        id: generateId(),
                        role: 'assistant',
                        content: 'Sorry, I encountered an error processing your request.',
                        timestamp: new Date(),
                    },
                ];
            });
        }
    };

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
        // Reuse the current question for web search
        const userMessage: Message = {
            id: generateId(),
            role: 'user',
            content: `🌐 Web search: ${question}`,
            timestamp: new Date(),
        };
        setMessages((prev) => [...prev, userMessage]);

        const loadingMessage: Message = {
            id: generateId(),
            role: 'assistant',
            content: '',
            timestamp: new Date(),
            isLoading: true,
        };
        setMessages((prev) => [...prev, loadingMessage]);

        try {
            const response = await webSearchMutation.mutateAsync(currentQuestion || question);

            setMessages((prev) => {
                const withoutLoading = prev.filter((m) => m.id !== loadingMessage.id);
                return [
                    ...withoutLoading,
                    {
                        id: generateId(),
                        role: 'assistant',
                        content: response.answer,
                        timestamp: new Date(),
                        sources: response.sources,
                    },
                ];
            });
        } catch (error) {
            setMessages((prev) => {
                const withoutLoading = prev.filter((m) => m.id !== loadingMessage.id);
                return [
                    ...withoutLoading,
                    {
                        id: generateId(),
                        role: 'assistant',
                        content: 'Sorry, web search failed.',
                        timestamp: new Date(),
                    },
                ];
            });
        }
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
                isLoading={queryMutation.isPending || webSearchMutation.isPending}
            />
        </div>
    );
}
