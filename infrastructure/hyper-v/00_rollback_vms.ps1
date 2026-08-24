<#
.SYNOPSIS
    Rollback script for Phase 3 Hyper-V VMs
.DESCRIPTION
    Stops and removes the 4 SOC Lab VMs if needed.
#>

[CmdletBinding()]
param(
    [switch]$RemoveDisks = $false
)

$ErrorActionPreference = "Continue"

Write-Host "============================================================" -ForegroundColor Yellow
Write-Host " [SOC LAB] Rolling Back Hyper-V VMs" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Yellow

$vmNames = @("soc-gateway", "soc-victim", "soc-sensor", "soc-attacker")

foreach ($name in $vmNames) {
    $vm = Get-VM -Name $name -ErrorAction SilentlyContinue
    if ($vm) {
        Write-Host "[-] Stopping and removing VM: $name..." -ForegroundColor Yellow
        if ($vm.State -eq "Running") {
            Stop-VM -Name $name -TurnOff -Force
        }
        Remove-VM -Name $name -Force
        Write-Host "[+] Removed VM: $name" -ForegroundColor Green
    }
}

if ($RemoveDisks -and (Test-Path "C:\SOC-Lab\vm")) {
    Write-Host "[-] Removing VM disk directory C:\SOC-Lab\vm..." -ForegroundColor Yellow
    Remove-Item -Path "C:\SOC-Lab\vm" -Recurse -Force
}
