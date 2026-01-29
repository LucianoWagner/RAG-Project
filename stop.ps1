#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Stop all RAG PDF System services

.DESCRIPTION
    Gracefully stops Docker services (Redis, MySQL)

.EXAMPLE
    .\stop.ps1
#>

Write-Host "🛑 Stopping RAG PDF System..." -ForegroundColor Cyan
Write-Host ""

# Stop Docker services
Write-Host "📦 Stopping Docker services..." -ForegroundColor Yellow
docker-compose down

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ All services stopped" -ForegroundColor Green
}
else {
    Write-Host "⚠️  Some services may still be running" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Note: FastAPI and Ollama must be stopped manually (Ctrl+C)" -ForegroundColor Cyan
