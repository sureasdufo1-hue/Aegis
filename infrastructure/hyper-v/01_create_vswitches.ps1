<#
.SYNOPSIS
    Phase 2: Hyper-V Virtual Switch Creation Script for SOC Lab
.DESCRIPTION
    Creates the 3 isolated virtual switches required by the SOC Architecture Baseline:
    1. soc-vsw-mgmt   (Internal: Host <-> Gateway <-> Sensor)
    2. soc-vsw-attack (Private:  Attacker <-> Gateway)
    3. soc-vsw-victim (Private:  Gateway <-> Victim)
#>

[CmdletBinding()]
param()

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " [SOC LAB] Creating Hyper-V Virtual Switches (Phase 2)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Management vSwitch (Internal for Host-VM communication)
if (-not (Get-VMSwitch -Name "soc-vsw-mgmt" -ErrorAction SilentlyContinue)) {
    Write-Host "[+] Creating Internal Switch: soc-vsw-mgmt..." -ForegroundColor Green
    New-VMSwitch -Name "soc-vsw-mgmt" -SwitchType Internal -Notes "SOC Lab Management Network (10.77.10.0/24)"
} else {
    Write-Host "[*] soc-vsw-mgmt already exists." -ForegroundColor Yellow
}

# 2. Attack Zone vSwitch (Private - completely isolated from host)
if (-not (Get-VMSwitch -Name "soc-vsw-attack" -ErrorAction SilentlyContinue)) {
    Write-Host "[+] Creating Private Switch: soc-vsw-attack..." -ForegroundColor Green
    New-VMSwitch -Name "soc-vsw-attack" -SwitchType Private -Notes "SOC Lab Attack Zone Network (10.77.20.0/24)"
} else {
    Write-Host "[*] soc-vsw-attack already exists." -ForegroundColor Yellow
}

# 3. Victim Zone vSwitch (Private - completely isolated from host)
if (-not (Get-VMSwitch -Name "soc-vsw-victim" -ErrorAction SilentlyContinue)) {
    Write-Host "[+] Creating Private Switch: soc-vsw-victim..." -ForegroundColor Green
    New-VMSwitch -Name "soc-vsw-victim" -SwitchType Private -Notes "SOC Lab Victim Zone Network (10.77.30.0/24)"
} else {
    Write-Host "[*] soc-vsw-victim already exists." -ForegroundColor Yellow
}

Write-Host "`n[+] Verification:" -ForegroundColor Cyan
Get-VMSwitch -Name "soc-vsw-*" | Select-Object Name, SwitchType, Notes | Format-Table -AutoSize
