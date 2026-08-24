<#
.SYNOPSIS
    Rollback script for Phase 2: Hyper-V Virtual Switches
.DESCRIPTION
    Safely tears down the 3 SOC lab virtual switches if a reset or reconfiguration is needed.
.NOTES
    [DESTRUCTIVE]
#>

[CmdletBinding()]
param()

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Error "[!] Administrator privileges required."
    exit 1
}

Write-Host "[*] Rolling back SOC Lab Hyper-V Virtual Switches..." -ForegroundColor Yellow

$switches = @("soc-vsw-victim", "soc-vsw-attack", "soc-vsw-mgmt")
foreach ($sw in $switches) {
    if (Get-VMSwitch -Name $sw -ErrorAction SilentlyContinue) {
        Write-Host "[-] Removing vSwitch: $sw..." -ForegroundColor Red
        Remove-VMSwitch -Name $sw -Force
    }
}

Write-Host "[+] Rollback complete." -ForegroundColor Green
