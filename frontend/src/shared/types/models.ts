// Domain Models
export interface Message {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: Date;
    sources?: SourceInfo[];
    confidence_score?: number;
    suggested_action?: string | null;
    isLoading?: boolean;
}

export interface SourceInfo {
    text: string;
    score: number;
    source?: string;
    page?: number;
}

export interface User {
    email: string;
    token: string;
}

export interface Document {
    id: number;
    filename: string;
    uploadDate: Date;
    chunks: number;
    size: number;
}
