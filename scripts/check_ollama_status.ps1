<#
.SYNOPSIS
    Queries local Ollama endpoint status, loaded models, and resource consumption.
#>

$hostUri = "http://127.0.0.1:11434"

Write-Host "=== Ollama Local Status Check ===" -ForegroundColor Cyan
try {
    $version = Invoke-RestMethod -Uri "$hostUri/api/version" -Method Get -TimeoutSec 3
    Write-Host "Ollama Version: $($version.version)" -ForegroundColor Green

    $tags = Invoke-RestMethod -Uri "$hostUri/api/tags" -Method Get -TimeoutSec 3
    Write-Host "`nInstalled Models ($($tags.models.Count)):" -ForegroundColor Yellow
    foreach ($m in $tags.models) {
        $sizeGb = [math]::Round($m.size / 1GB, 2)
        Write-Host " - $($m.name) (Size: ${sizeGb} GB, Modified: $($m.modified_at), Digest: $($m.digest.Substring(0, 16))...)"
    }

    $ps = Invoke-RestMethod -Uri "$hostUri/api/ps" -Method Get -TimeoutSec 3
    Write-Host "`nCurrently Loaded in Memory ($($ps.models.Count)):" -ForegroundColor Yellow
    foreach ($p in $ps.models) {
        $vramMb = [math]::Round($p.size_vram / 1MB, 2)
        Write-Host " - $($p.name) (VRAM/RAM: ${vramMb} MB, Expires: $($p.expires_at))"
    }
} catch {
    Write-Host "Ollama endpoint $hostUri is offline or unreachable." -ForegroundColor Red
    Write-Host "Details: $_"
}
