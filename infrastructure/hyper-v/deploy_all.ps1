<#
.SYNOPSIS
    Master Hyper-V Deployment & Provisioning Script for SOC Lab
.DESCRIPTION
    Orchestrates the complete Hyper-V infrastructure setup:
    1. Phase 2: Create 3 Virtual Switches (soc-vsw-mgmt, soc-vsw-attack, soc-vsw-victim) & Host IP (10.77.10.10)
    2. Phase 3: Provision 4 Gen-2 VMs (soc-gateway, soc-victim, soc-sensor, soc-attacker)
    3. Phase 7: Configure Hyper-V Port Mirroring (soc-victim -> soc-sensor nic-monitor)
    4. Phase 5: Configure Host static route to Victim Zone (10.77.30.0/24 via 10.77.10.1)
    5. Optionally boot the virtual machines
.EXAMPLE
    powershell.exe -ExecutionPolicy Bypass -File .\infrastructure\hyper-v\deploy_all.ps1
    powershell.exe -ExecutionPolicy Bypass -File .\infrastructure\hyper-v\deploy_all.ps1 -StartVMs
#>

[CmdletBinding()]
param(
    [switch]$StartVMs = $false,
    [switch]$DryRun = $false,
    [string]$VmRootPath = "C:\SOC-Lab\vm",
    [string]$IsoRootPath = "C:\SOC-Lab\iso"
)

$ErrorActionPreference = "Stop"

Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host " 🛡️  SOC Detection & Monitoring Lab — Hyper-V Full Deployment" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan

# Dry Run / WhatIf Preview Mode
if ($DryRun -or $WhatIfPreference) {
    Write-Host "`n[DRY RUN / WHATIF MODE] Provisioning Plan & Resource Matrix:" -ForegroundColor Yellow
    
    $plan = [ordered]@{
        Switches = @(
            [PSCustomObject]@{ Name = "soc-vsw-mgmt";   Type = "Internal"; CIDR = "10.77.10.0/24"; HostIP = "10.77.10.10/24" }
            [PSCustomObject]@{ Name = "soc-vsw-attack"; Type = "Private";  CIDR = "10.77.20.0/24"; HostIP = "None (Isolated)" }
            [PSCustomObject]@{ Name = "soc-vsw-victim"; Type = "Private";  CIDR = "10.77.30.0/24"; HostIP = "None (Isolated)" }
        )
        VirtualMachines = @(
            [PSCustomObject]@{
                VMName = "soc-gateway"; OS = "Ubuntu 22.04 LTS"; Gen = 2; vCPU = 1; RAM_MB = 1024; VHDX_GB = 16
                NICs = "nic-mgmt, nic-attack, nic-victim"
            }
            [PSCustomObject]@{
                VMName = "soc-victim"; OS = "Ubuntu 22.04 + OWASP Shop"; Gen = 2; vCPU = 2; RAM_MB = 4096; VHDX_GB = 30
                NICs = "nic-victim (Mirror: Source)"
            }
            [PSCustomObject]@{
                VMName = "soc-sensor"; OS = "Ubuntu 22.04 + Suricata 8"; Gen = 2; vCPU = 4; RAM_MB = 8192; VHDX_GB = 80
                NICs = "nic-mgmt, nic-monitor (NO IP, Mirror: Destination)"
            }
            [PSCustomObject]@{
                VMName = "soc-attacker"; OS = "Kali Linux 2026.2"; Gen = 2; vCPU = 2; RAM_MB = 4096; VHDX_GB = 40
                NICs = "nic-attack"
            }
        )
        PortMirroring = @{
            Source      = "soc-victim (nic-victim)"
            Destination = "soc-sensor (nic-monitor)"
            Switch      = "soc-vsw-victim"
        }
        HostRoute = @{
            Destination = "10.77.30.0/24"
            NextHop     = "10.77.10.1 (soc-gateway)"
            Interface   = "vEthernet (soc-vsw-mgmt)"
        }
        RollbackTargets = @{
            VMs         = @("soc-gateway", "soc-victim", "soc-sensor", "soc-attacker")
            Switches    = @("soc-vsw-victim", "soc-vsw-attack", "soc-vsw-mgmt")
            Storage     = "$VmRootPath"
        }
    }

    Write-Host "`n1. Target Virtual Switches:" -ForegroundColor Cyan
    $plan.Switches | Format-Table -AutoSize
    
    Write-Host "2. Target Virtual Machines (Gen 2):" -ForegroundColor Cyan
    $plan.VirtualMachines | Select-Object VMName, OS, Gen, vCPU, RAM_MB, VHDX_GB | Format-Table -AutoSize
    
    Write-Host "3. Port Mirroring:" -ForegroundColor Cyan
    Write-Host "   Source:      $($plan.PortMirroring.Source)" -ForegroundColor White
    Write-Host "   Destination: $($plan.PortMirroring.Destination)" -ForegroundColor White
    Write-Host "   Switch:      $($plan.PortMirroring.Switch)" -ForegroundColor White

    Write-Host "`n4. Host Return Route:" -ForegroundColor Cyan
    Write-Host "   Route: $($plan.HostRoute.Destination) via $($plan.HostRoute.NextHop) on '$($plan.HostRoute.Interface)'" -ForegroundColor White

    Write-Host "`n5. Expected Rollback Objects:" -ForegroundColor Cyan
    Write-Host "   VMs:      $($plan.RollbackTargets.VMs -join ', ')" -ForegroundColor White
    Write-Host "   Switches: $($plan.RollbackTargets.Switches -join ', ')" -ForegroundColor White

    Write-Host "`n[DRY RUN COMPLETE] No system state was modified." -ForegroundColor Green
    return $plan
}

# 0. Check Administrator Privileges
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "`n[!] CRITICAL: Administrator privileges are required to manage Hyper-V." -ForegroundColor Red
    Write-Host "[!] Please re-run this script in an elevated PowerShell session (Run as Administrator)." -ForegroundColor Yellow
    Write-Host "    Example: Start-Process powershell -Verb RunAs -ArgumentList '-ExecutionPolicy Bypass -File .\infrastructure\hyper-v\deploy_all.ps1'" -ForegroundColor Gray
    exit 1
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# ------------------------------------------------------------------
# Step 1: Create Virtual Switches & Host Management IP
# ------------------------------------------------------------------
Write-Host "`n[Step 1/5] Executing 01_create_vswitches.ps1..." -ForegroundColor Green
$vswitchScript = Join-Path $scriptDir "01_create_vswitches.ps1"
if (Test-Path $vswitchScript) {
    & $vswitchScript
} else {
    Write-Error "Script not found: $vswitchScript"
}

# ------------------------------------------------------------------
# Step 2: Provision Virtual Machines (Gen 2)
# ------------------------------------------------------------------
Write-Host "`n[Step 2/5] Executing 03_provision_vms.ps1..." -ForegroundColor Green
$vmScript = Join-Path $scriptDir "03_provision_vms.ps1"
if (Test-Path $vmScript) {
    & $vmScript -VmRootPath $VmRootPath -IsoRootPath $IsoRootPath
} else {
    Write-Error "Script not found: $vmScript"
}

# ------------------------------------------------------------------
# Step 3: Configure Port Mirroring
# ------------------------------------------------------------------
Write-Host "`n[Step 3/5] Executing 02_configure_port_mirroring.ps1..." -ForegroundColor Green
$mirrorScript = Join-Path $scriptDir "02_configure_port_mirroring.ps1"
if (Test-Path $mirrorScript) {
    & $mirrorScript
} else {
    Write-Error "Script not found: $mirrorScript"
}

# ------------------------------------------------------------------
# Step 4: Configure Host Route to Victim Subnet
# ------------------------------------------------------------------
Write-Host "`n[Step 4/5] Executing 04_configure_host_route.ps1..." -ForegroundColor Green
$routeScript = Join-Path $scriptDir "04_configure_host_route.ps1"
if (Test-Path $routeScript) {
    & $routeScript
} else {
    Write-Error "Script not found: $routeScript"
}

# ------------------------------------------------------------------
# Step 5: Start Virtual Machines (Optional or Requested)
# ------------------------------------------------------------------
if ($StartVMs) {
    Write-Host "`n[Step 5/5] Starting Virtual Machines..." -ForegroundColor Green
    $bootOrder = @("soc-gateway", "soc-sensor", "soc-victim", "soc-attacker")
    foreach ($vmName in $bootOrder) {
        $vm = Get-VM -Name $vmName -ErrorAction SilentlyContinue
        if ($vm -and $vm.State -ne "Running") {
            Write-Host "  [+] Starting VM: $vmName..." -ForegroundColor Cyan
            Start-VM -Name $vmName
        } else {
            Write-Host "  [*] $vmName is already running or not found." -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "`n[Step 5/5] Skipping VM boot. (Use -StartVMs parameter to start them automatically)" -ForegroundColor Yellow
}

# ------------------------------------------------------------------
# Final Verification Summary
# ------------------------------------------------------------------
Write-Host "`n====================================================================" -ForegroundColor Cyan
Write-Host " 📋 Deployment Verification & Status Summary" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan

Write-Host "`n[1] Virtual Switches:" -ForegroundColor Green
Get-VMSwitch -Name "soc-vsw-*" | Select-Object Name, SwitchType | Format-Table -AutoSize

Write-Host "[2] Virtual Machines:" -ForegroundColor Green
Get-VM -Name "soc-*" | Select-Object Name, State, Generation, @{N='MemoryAssignedMB';E={$_.MemoryAssigned/1MB}}, Uptime | Format-Table -AutoSize

Write-Host "[3] Network Adapters & Port Mirroring:" -ForegroundColor Green
Get-VMNetworkAdapter -VMName "soc-gateway", "soc-victim", "soc-sensor", "soc-attacker" -ErrorAction SilentlyContinue |
    Select-Object VMName, Name, SwitchName, MacAddress, PortMirroringMode | Format-Table -AutoSize

Write-Host "[4] Host Static Route to Victim Zone:" -ForegroundColor Green
Get-NetRoute -DestinationPrefix "10.77.30.0/24" -InterfaceAlias "vEthernet (soc-vsw-mgmt)" -ErrorAction SilentlyContinue |
    Select-Object DestinationPrefix, NextHop, RouteMetric, InterfaceAlias | Format-Table -AutoSize

Write-Host "`n🎉 [COMPLETED] Hyper-V Virtual Infrastructure Deployment Succeeded!" -ForegroundColor Green
