<#
.SYNOPSIS
    Phase 5: Configure Windows Host Route to Victim Subnet
.DESCRIPTION
    Adds the route to 10.77.30.0/24 via Gateway MGMT IP 10.77.10.1 on vEthernet (soc-vsw-mgmt).
    Note: Attack network (10.77.20.0/24) route is intentionally NOT added to Host as per AGENTS.md contract.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$mgmtAlias = "vEthernet (soc-vsw-mgmt)"
$destPrefix = "10.77.30.0/24"
$nextHop = "10.77.10.1"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " [SOC LAB] Configuring Host Return Route to Victim Zone" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$existingRoute = Get-NetRoute -DestinationPrefix $destPrefix -InterfaceAlias $mgmtAlias -ErrorAction SilentlyContinue
if (-not $existingRoute) {
    New-NetRoute -DestinationPrefix $destPrefix -InterfaceAlias $mgmtAlias -NextHop $nextHop -RouteMetric 50 | Out-Null
    Write-Host "[+] Added route: $destPrefix via $nextHop on $mgmtAlias" -ForegroundColor Green
} else {
    Write-Host "[*] Route for $destPrefix via $nextHop already exists." -ForegroundColor Yellow
}

# Verification
Get-NetRoute -DestinationPrefix $destPrefix | Format-Table -AutoSize
