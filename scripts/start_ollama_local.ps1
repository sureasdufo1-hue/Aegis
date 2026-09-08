<#
.SYNOPSIS
    Starts Ollama in strict local-only mode with approved SOC constraints.
.DESCRIPTION
    Phase LLM-3: Local AI Platform Foundation
    Enforces OLLAMA_HOST=127.0.0.1:11434, OLLAMA_NUM_PARALLEL=1, OLLAMA_NO_CLOUD=1
#>

[CmdletBinding()]
param()

$env:OLLAMA_HOST = "127.0.0.1:11434"
$env:OLLAMA_NO_CLOUD = "1"
$env:OLLAMA_NUM_PARALLEL = "1"
$env:OLLAMA_MAX_LOADED_MODELS = "1"
$env:OLLAMA_KEEP_ALIVE = "10m"
$env:OLLAMA_ORIGINS = ""

Write-Host "[SOC-AI] Initializing Ollama in strict local-only mode..." -ForegroundColor Cyan
Write-Host "  OLLAMA_HOST: $env:OLLAMA_HOST"
Write-Host "  OLLAMA_NO_CLOUD: $env:OLLAMA_NO_CLOUD"
Write-Host "  OLLAMA_NUM_PARALLEL: $env:OLLAMA_NUM_PARALLEL"
Write-Host "  OLLAMA_MAX_LOADED_MODELS: $env:OLLAMA_MAX_LOADED_MODELS"

$ollamaCmd = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollamaCmd) {
    # Check default install path
    $defaultPath = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
    if (Test-Path $defaultPath) {
        $ollamaCmd = $defaultPath
    } else {
        Write-Error "Ollama executable not found. Please complete Phase LLM-4 installation first."
        exit 1
    }
}

Write-Host "[SOC-AI] Starting Ollama server process..." -ForegroundColor Green
& $ollamaCmd serve
