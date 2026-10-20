# Script de lancement combiné Service Accueil (gRPC + REST)
$ErrorActionPreference = "Continue"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Démarrage du Service Accueil (Clinique Espoir) " -ForegroundColor Cyan
Write-Host "  Port gRPC : 50051  |  REST Gateway : 8081      " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

$VENV_PYTHON  = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
$VENV_UVICORN = Join-Path $PSScriptRoot "..\.venv\Scripts\uvicorn.exe"

# 1. Démarrer le serveur gRPC dans une nouvelle fenêtre
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\..'; & '$VENV_PYTHON' grpc_services/accueil_server.py"

# 2. Démarrer la Gateway FastAPI
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\..'; & '$VENV_UVICORN' rest_services.gateway:app --port 8081 --reload"

Write-Host "`nLes services ont été lancés dans des fenêtres distinctes." -ForegroundColor Green
Write-Host "Interface Graphique Web : http://localhost:8081" -ForegroundColor Cyan
Write-Host "Documentation Swagger UI: http://localhost:8081/docs" -ForegroundColor Yellow
Write-Host "Serveur gRPC Core       : localhost:50051" -ForegroundColor Yellow
