<#
.SYNOPSIS
    Phase 2: Hyper-V Virtual Switch & Management IP Creation Script
.DESCRIPTION
    Creates the 3 isolated virtual switches and configures the Host Management IP
    as defined in the SOC Architecture Baseline (HLD/LLD v1.0 & Implementation Plan Phase 2):
    1. soc-vsw-mgmt   (Internal: Host <-> Gateway <-> Sensor)
    2. soc-vsw-attack (Private:  Attacker <-> Gateway)
    3. soc-vsw-victim (Private:  Gateway <-> Victim)
    4. Host Adapter: vEthernet (soc-vsw-mgmt) -> 10.77.10.10/24
.NOTES
    Completion Gate: GATE-NET-INFRA-01
    Evidence ID: EV-NET-INFRA-001
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " [SOC LAB] Hyper-V Virtual Network Provisioning (Phase 2)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 0. Check Administrator Privileges
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Error "[!] CRITICAL: Administrator privileges required. Please execute this script in an elevated PowerShell session."
    exit 1
}

# 1. Management vSwitch (Internal for Host <-> Lab communication)
if (-not (Get-VMSwitch -Name "soc-vsw-mgmt" -ErrorAction SilentlyContinue)) {
    Write-Host "[+] Creating Internal Switch: soc-vsw-mgmt..." -ForegroundColor Green
    New-VMSwitch -Name "soc-vsw-mgmt" -SwitchType Internal -Notes "SOC Lab Management Network (10.77.10.0/24)" | Out-Null
} else {
    Write-Host "[*] soc-vsw-mgmt already exists." -ForegroundColor Yellow
}

# 2. Attack Zone vSwitch (Private - completely isolated from host)
if (-not (Get-VMSwitch -Name "soc-vsw-attack" -ErrorAction SilentlyContinue)) {
    Write-Host "[+] Creating Private Switch: soc-vsw-attack..." -ForegroundColor Green
    New-VMSwitch -Name "soc-vsw-attack" -SwitchType Private -Notes "SOC Lab Attack Zone Network (10.77.20.0/24)" | Out-Null
} else {
    Write-Host "[*] soc-vsw-attack already exists." -ForegroundColor Yellow
}

# 3. Victim Zone vSwitch (Private - completely isolated from host)
if (-not (Get-VMSwitch -Name "soc-vsw-victim" -ErrorAction SilentlyContinue)) {
    Write-Host "[+] Creating Private Switch: soc-vsw-victim..." -ForegroundColor Green
    New-VMSwitch -Name "soc-vsw-victim" -SwitchType Private -Notes "SOC Lab Victim Zone Network (10.77.30.0/24)" | Out-Null
} else {
    Write-Host "[*] soc-vsw-victim already exists." -ForegroundColor Yellow
}

# 4. Configure Windows Host Management IP (10.77.10.10/24)
$mgmtAlias = "vEthernet (soc-vsw-mgmt)"
Write-Host "`n[+] Configuring Host Adapter '$mgmtAlias' with 10.77.10.10/24..." -ForegroundColor Green

# Ensure interface exists
$adapter = Get-NetAdapter -Name $mgmtAlias -ErrorAction SilentlyContinue
if (-not $adapter) {
    Write-Error "[!] Adapter '$mgmtAlias' not found. Ensure soc-vsw-mgmt was created successfully."
    exit 1
}

# Disable DHCP
Set-NetIPInterface -InterfaceAlias $mgmtAlias -Dhcp Disabled -ErrorAction SilentlyContinue

# Assign IP if not already assigned
$existingIP = Get-NetIPAddress -InterfaceAlias $mgmtAlias -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object IPAddress -eq "10.77.10.10"
if (-not $existingIP) {
    # Remove any existing IPv4 on this interface first to prevent duplicates
    Get-NetIPAddress -InterfaceAlias $mgmtAlias -AddressFamily IPv4 -ErrorAction SilentlyContinue | Remove-NetIPAddress -Confirm:$false -ErrorAction SilentlyContinue
    New-NetIPAddress -InterfaceAlias $mgmtAlias -IPAddress 10.77.10.10 -PrefixLength 24 | Out-Null
    Write-Host "[+] Assigned IP 10.77.10.10/24 to '$mgmtAlias'." -ForegroundColor Green
} else {
    Write-Host "[*] IP 10.77.10.10/24 is already configured on '$mgmtAlias'." -ForegroundColor Yellow
}

# 5. Verification & Gate Check
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host " [GATE-NET-INFRA-01] Verification Summary" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$switches = Get-VMSwitch -Name "soc-vsw-*" | Select-Object Name, SwitchType
$switches | Format-Table -AutoSize

$ipCheck = Get-NetIPAddress -InterfaceAlias $mgmtAlias -AddressFamily IPv4 | Select-Object InterfaceAlias, IPAddress, PrefixLength
$ipCheck | Format-Table -AutoSize

$mgmtSw = $switches | Where-Object { $_.Name -eq "soc-vsw-mgmt" -and $_.SwitchType -eq "Internal" }
$attSw  = $switches | Where-Object { $_.Name -eq "soc-vsw-attack" -and $_.SwitchType -eq "Private" }
$vicSw  = $switches | Where-Object { $_.Name -eq "soc-vsw-victim" -and $_.SwitchType -eq "Private" }
$hostIP = $ipCheck | Where-Object { $_.IPAddress -eq "10.77.10.10" -and $_.PrefixLength -eq 24 }

if ($mgmtSw -and $attSw -and $vicSw -and $hostIP) {
    Write-Host "[PASS] GATE-NET-INFRA-01: Virtual network infrastructure successfully created and verified." -ForegroundColor Green
} else {
    Write-Host "[FAIL] GATE-NET-INFRA-01: One or more network baseline components missing." -ForegroundColor Red
}
