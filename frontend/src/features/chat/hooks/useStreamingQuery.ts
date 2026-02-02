import { useState, useCallback, useRef } from 'react';
import { SourceChunk } from '@/shared/types/api';

interface StatusMessage {
    message: string;
    step: string;
}

interface StreamingState {
    isStreaming: boolean;
    streamedContent: string;
    sources: SourceChunk[];
    statusMessage: string | null;
    error: string | null;
    suggestedAction: string | null;
}

interface StreamError {
    message: string;
    suggested_action?: string;
    intent?: string;
}

export function useStreamingQuery() {
    const [state, setState] = useState<StreamingState>({
        isStreaming: false,
        streamedContent: '',
        sources: [],
        statusMessage: null,
        error: null,
        suggestedAction: null,
    });

    const abortControllerRef = useRef<AbortController | null>(null);

    const startStream = useCallback(async (
        question: string,
        mode: 'pdf' | 'web'
    ) => {
        // Reset state
        setState({
            isStreaming: true,
            streamedContent: '',
            sources: [],
            statusMessage: null,
            error: null,
            suggestedAction: null,
        });

        const token = localStorage.getItem('token');
        const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

        // Choose endpoint based on mode
        const endpoint = mode === 'pdf' ? '/query/stream' : '/query/web-search/stream';
        const url = new URL(endpoint, baseUrl);
        url.searchParams.set('question', question);

        // Abort controller for cancellation
        abortControllerRef.current = new AbortController();

        try {
            const response = await fetch(url.toString(), {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Accept': 'text/event-stream',
                },
                signal: abortControllerRef.current.signal,
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            if (!response.body) {
                throw new Error('No response body');
            }

            // Read SSE stream
            const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();

            let buffer = '';
            let currentEventType = 'token'; // Track event type across lines

            while (true) {
                const { done, value } = await reader.read();

                if (done) break;

                buffer += value;
                const lines = buffer.split('\n');

                // Keep last incomplete line in buffer
                buffer = lines.pop() || '';

                for (const line of lines) {
                    // Empty lines separate events
                    if (line.trim() === '') {
                        continue;
                    }

                    if (line.startsWith('event: ')) {
                        // Update current event type
                        currentEventType = line.slice(7).trim();
                        continue;
                    }

                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);

                        try {
                            switch (currentEventType) {
                                case 'status': {
                                    const statusData: StatusMessage = JSON.parse(data);
                                    setState(prev => ({
                                        ...prev,
                                        statusMessage: statusData.message,
                                    }));
                                    break;
                                }

                                case 'sources': {
                                    const sourcesData: SourceChunk[] = JSON.parse(data);
                                    setState(prev => ({
                                        ...prev,
                                        sources: sourcesData,
                                        statusMessage: null, // Clear status when sources arrive
                                    }));
                                    break;
                                }

                                case 'token': {
                                    setState(prev => ({
                                        ...prev,
                                        streamedContent: prev.streamedContent + data,
                                        statusMessage: null, // Clear status when tokens start
                                    }));
                                    break;
                                }

                                case 'done': {
                                    setState(prev => ({
                                        ...prev,
                                        isStreaming: false,
                                        statusMessage: null,
                                    }));
                                    return;
                                }

                                case 'error': {
                                    const errorData: StreamError = JSON.parse(data);
                                    setState(prev => ({
                                        ...prev,
                                        isStreaming: false,
                                        error: errorData.message,
                                        suggestedAction: errorData.suggested_action || null,
                                        statusMessage: null,
                                    }));
                                    return;
                                }
                            }
                        } catch (parseError) {
                            console.warn('Failed to parse SSE data:', data, parseError);
                        }
                    }
                }
            }

        } catch (error: any) {
            if (error.name === 'AbortError') {
                // User cancelled
                setState(prev => ({
                    ...prev,
                    isStreaming: false,
                    statusMessage: null,
                }));
            } else {
                console.error('Stream error:', error);
                setState(prev => ({
                    ...prev,
                    isStreaming: false,
                    error: error.message || 'Error al conectar con el servidor',
                    statusMessage: null,
                }));
            }
        }
    }, []);

    const stopStream = useCallback(() => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
            abortControllerRef.current = null;
        }
        setState(prev => ({
            ...prev,
            isStreaming: false,
            statusMessage: null,
        }));
    }, []);

    return {
        ...state,
        startStream,
        stopStream,
    };
}
