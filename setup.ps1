# Setup script for RAG PDF System
# Run this script to set up the environment and install dependencies

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RAG PDF System - Setup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
Write-Host "Checking Python installation..." -ForegroundColor Yellow
$pythonVersion = py --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python not found. Please install Python 3.10 or higher." -ForegroundColor Red
    exit 1
}
Write-Host "Found: $pythonVersion" -ForegroundColor Green
Write-Host ""

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
    Write-Host "Virtual environment activated!" -ForegroundColor Green
} else {
    Write-Host "ERROR: Virtual environment not found. Creating it now..." -ForegroundColor Yellow
    py -m venv venv
    & "venv\Scripts\Activate.ps1"
    Write-Host "Virtual environment created and activated!" -ForegroundColor Green
}
Write-Host ""

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip
pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "Dependencies installed successfully!" -ForegroundColor Green
} else {
    Write-Host "ERROR: Failed to install dependencies." -ForegroundColor Red
    exit 1
}
Write-Host ""

# Check Ollama
Write-Host "Checking Ollama installation..." -ForegroundColor Yellow
$ollamaCheck = ollama --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Ollama not found or not in PATH." -ForegroundColor Yellow
    Write-Host "Please install Ollama from: https://ollama.ai" -ForegroundColor Yellow
} else {
    Write-Host "Ollama found: $ollamaCheck" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "Checking if mistral:7b model is available..." -ForegroundColor Yellow
    $models = ollama list 2>&1
    if ($models -match "mistral.*7b") {
        Write-Host "Model mistral:7b is already downloaded!" -ForegroundColor Green
    } else {
        Write-Host "Model mistral:7b not found. Download it with:" -ForegroundColor Yellow
        Write-Host "  ollama pull mistral:7b" -ForegroundColor Cyan
    }
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup completed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Make sure Ollama is running:" -ForegroundColor White
Write-Host "   ollama serve" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Start the FastAPI server:" -ForegroundColor White
Write-Host "   uvicorn app.main:app --reload" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Open the API docs:" -ForegroundColor White
Write-Host "   http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
