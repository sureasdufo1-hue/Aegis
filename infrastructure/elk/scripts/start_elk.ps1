# ==============================================================================
# SOC Detection Lab — Phase ELK-2 Elasticsearch Bootstrap & Verification
# ==============================================================================

$ErrorActionPreference = "Continue"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Phase ELK-2: Elasticsearch 8.17.3 Deployment    " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Check Docker Daemon Status
Write-Host "`n[*] Checking Docker Engine availability..." -ForegroundColor Yellow
$dockerPing = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] Docker Desktop engine is not running." -ForegroundColor Red
    Write-Host "    Please ensure Docker Desktop is launched on Windows." -ForegroundColor Yellow
    Write-Host "    Launching Docker Desktop now..." -ForegroundColor Cyan
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe" -ErrorAction SilentlyContinue
    
    Write-Host "[*] Waiting up to 45 seconds for Docker engine to initialize..." -ForegroundColor Yellow
    $retries = 0
    while ($retries -lt 15) {
        Start-Sleep -Seconds 3
        $null = docker info 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[PASS] Docker Engine is now ONLINE!" -ForegroundColor Green
            break
        }
        $retries++
        Write-Host "    Waiting for daemon pipe ($($retries * 3)s)..." -ForegroundColor Gray
    }
} else {
    Write-Host "[PASS] Docker Engine is ONLINE!" -ForegroundColor Green
}

# 2. Validate Compose Syntax
Write-Host "`n[*] Validating docker-compose.elk.yml..." -ForegroundColor Yellow
docker compose -f infrastructure/elk/docker-compose.elk.yml config
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] Docker Compose validation failed!" -ForegroundColor Red
    exit 1
}
Write-Host "[PASS] Compose configuration valid (Exposing 127.0.0.1:9201:9200)" -ForegroundColor Green

# 3. Launch Elasticsearch Container
Write-Host "`n[*] Deploying soc-elasticsearch container..." -ForegroundColor Yellow
docker compose -f infrastructure/elk/docker-compose.elk.yml up -d soc-elasticsearch
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] Failed to launch soc-elasticsearch container." -ForegroundColor Red
    exit 1
}

# 4. Wait for Cluster Ready
Write-Host "`n[*] Waiting for Elasticsearch health check on http://127.0.0.1:9201..." -ForegroundColor Yellow
$pyCheck = python infrastructure/elk/scripts/verify_es_health.py
Write-Host $pyCheck

Write-Host "`n[+] Phase ELK-2 bootstrap execution completed." -ForegroundColor Cyan
