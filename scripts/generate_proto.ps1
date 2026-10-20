# Script de génération des stubs Protocol Buffers
$ErrorActionPreference = "Stop"

Write-Host "--- Génération des stubs gRPC Python ---" -ForegroundColor Cyan

$VENV_PYTHON = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
$PROTO_DIR   = Join-Path $PSScriptRoot "..\proto"
$OUT_DIR     = Join-Path $PSScriptRoot "..\grpc_services\generated"

if (-not (Test-Path $OUT_DIR)) {
    New-Item -ItemType Directory -Path $OUT_DIR -Force | Out-Null
}

& $VENV_PYTHON -m grpc_tools.protoc `
    -I $PROTO_DIR `
    --python_out=$OUT_DIR `
    --grpc_python_out=$OUT_DIR `
    (Join-Path $PROTO_DIR "accueil.proto")

# Assurer la présence du fichier __init__.py
$INIT_FILE = Join-Path $OUT_DIR "__init__.py"
if (-not (Test-Path $INIT_FILE)) {
    New-Item -ItemType File -Path $INIT_FILE -Force | Out-Null
}

Write-Host "Succès : Stubs générés dans $OUT_DIR" -ForegroundColor Green
