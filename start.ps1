#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Quick start script for RAG PDF System

.DESCRIPTION
    Starts all required services (Docker, FastAPI) and verifies they're running

.EXAMPLE
    .\start.ps1
#>

Write-Host "Starting RAG PDF System..." -ForegroundColor Cyan
Write-Host ""

# 1. Check if in virtual environment
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Virtual environment not activated" -ForegroundColor Yellow
    Write-Host "Activating venv..." -ForegroundColor Yellow
    
    if (Test-Path ".\venv\Scripts\Activate.ps1") {
        & .\venv\Scripts\Activate.ps1
        Write-Host "Virtual environment activated" -ForegroundColor Green
    }
    else {
        Write-Host "Virtual environment not found. Run setup.ps1 first" -ForegroundColor Red
        exit 1
    }
}

# 2. Start Docker services
Write-Host ""
Write-Host "Starting Docker services (Redis + MySQL)..." -ForegroundColor Cyan
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to start Docker services" -ForegroundColor Red
    exit 1
}

Write-Host "Docker services started" -ForegroundColor Green

# 3. Wait for MySQL to be ready
Write-Host ""
Write-Host "Waiting for MySQL to initialize (15 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# 4. Check Ollama
Write-Host ""
Write-Host "Checking Ollama..." -ForegroundColor Cyan

try {
    $ollamaResponse = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 5 -UseBasicParsing
    Write-Host "Ollama is running" -ForegroundColor Green
}
catch {
    Write-Host "Ollama not detected. Make sure to run 'ollama serve' in another terminal" -ForegroundColor Yellow
}

# 5. Verify services
Write-Host ""
Write-Host "Verifying Docker services..." -ForegroundColor Cyan
docker-compose ps

# 6. Show instructions
Write-Host ""
Write-Host "===============================================================" -ForegroundColor Green
Write-Host "All services started!" -ForegroundColor Green
Write-Host "===============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "To start FastAPI:" -ForegroundColor Cyan
Write-Host "  uvicorn app.main:app --reload" -ForegroundColor White
Write-Host ""
Write-Host "To test the system:" -ForegroundColor Cyan
Write-Host "  python test_observability.py" -ForegroundColor White
Write-Host ""
Write-Host "Services running:" -ForegroundColor Cyan
Write-Host "  - Redis:    localhost:6379" -ForegroundColor White
Write-Host "  - MySQL:    localhost:3306" -ForegroundColor White
Write-Host "  - Ollama:   localhost:11434" -ForegroundColor White
Write-Host "  - FastAPI:  localhost:8000 (after running uvicorn)" -ForegroundColor White
Write-Host ""
Write-Host "To stop Docker services:" -ForegroundColor Cyan
Write-Host "  docker-compose down" -ForegroundColor White
Write-Host ""
