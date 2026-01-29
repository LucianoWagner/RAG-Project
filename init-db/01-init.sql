-- Initialization script for RAG PDF System database
-- Creates database, user, and tables

-- Create database
CREATE DATABASE IF NOT EXISTS rag_metadata CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE rag_metadata;

-- Create tables
CREATE TABLE IF NOT EXISTS document_metadata (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_hash VARCHAR(64) NOT NULL UNIQUE,
    chunks_count INT NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    processing_time_ms INT NOT NULL,
    pages_count INT NULL,
    extracted_text_length INT NULL,
    upload_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_filename (filename),
    INDEX idx_file_hash (file_hash),
    INDEX idx_upload_timestamp (upload_timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Log completion
SELECT 'Database initialization complete' AS status;
