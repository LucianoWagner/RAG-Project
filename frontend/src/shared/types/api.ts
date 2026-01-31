// API Response Types
export interface QueryResponse {
    answer: string;
    sources: SourceChunk[];
    has_context: boolean;
    intent: 'GREETING' | 'DOCUMENT_QUERY' | 'WEB_SEARCH';
    confidence_score?: number;
    suggested_action?: string | null;
}

export interface SourceChunk {
    text: string;
    score: number;
    metadata?: {
        source?: string;
        page?: number;
    };
}

export interface UploadResponse {
    filename: string;
    chunks_processed: number;
    message: string;
}

export interface DocumentMetadata {
    id: number;
    filename: string;
    file_hash: string;
    chunks_count: number;
    file_size_bytes: number;
    processing_time_ms: number;
    pages_count?: number;
    extracted_text_length?: number;
    upload_timestamp: string;
}

export interface HealthResponse {
    status: string;
    services: {
        ollama: {
            available: boolean;
            circuit_breaker: string;
        };
        redis: {
            available: boolean;
            circuit_breaker: string;
        };
        mysql: {
            available: boolean;
        };
        embedding_model: {
            loaded: boolean;
        };
        vector_store: {
            initialized: boolean;
            documents: number;
        };
    };
    timestamp: string;
}

export interface ServiceHealth {
    status: string;
    message?: string;
}

export interface VectorStoreHealth {
    status: string;
    documents_count: number;
    chunks_count: number;
}

export interface CacheStats {
    embeddings: CacheTypeStats;
    wikipedia: CacheTypeStats;
}

export interface CacheTypeStats {
    hits: number;
    misses: number;
    hit_ratio: number;
}

// Error Response
export interface ErrorResponse {
    detail: string | {
        message: string;
        original_filename?: string;
        upload_date?: string;
        chunks_count?: number;
    };
}
