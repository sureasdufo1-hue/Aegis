<#
.SYNOPSIS
    Phase 7: Hyper-V Port Mirroring Configuration for SOC Sensor
.DESCRIPTION
    Configures packet mirroring from soc-victim (Source) to soc-sensor nic-monitor (Destination).
    This enables passive network monitoring without touching victim traffic.
#>

[CmdletBinding()]
param()

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " [SOC LAB] Configuring Hyper-V Port Mirroring (Phase 7)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Configure Victim NIC as Mirror Source
Write-Host "[+] Setting 'soc-victim' NIC as PortMirroring Source..." -ForegroundColor Green
Set-VMNetworkAdapter -VMName "soc-victim" -PortMirroring Source -ErrorAction Stop

# 2. Configure Sensor Monitor NIC as Mirror Destination
Write-Host "[+] Setting 'soc-sensor' (nic-monitor) as PortMirroring Destination..." -ForegroundColor Green
Set-VMNetworkAdapter -VMName "soc-sensor" -Name "nic-monitor" -PortMirroring Destination -ErrorAction Stop

Write-Host "`n[+] Verification (GATE-MIRROR-01):" -ForegroundColor Cyan
Get-VMNetworkAdapter -VMName "soc-victim", "soc-sensor" | Select-Object VMName, Name, SwitchName, PortMirroringMode | Format-Table -AutoSize
