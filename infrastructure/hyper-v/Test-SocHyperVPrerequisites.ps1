<#
.SYNOPSIS
    Prerequisite & Readiness Assessment Script for Phase 32 Hyper-V SOC Lab
.DESCRIPTION
    Performs comprehensive, read-only inspection of Windows host, Hyper-V features,
    administrator privileges, resource capacity (CPU, RAM, Disk), ISO images,
    and network subnet collision before any provisioning actions.
#>

[CmdletBinding()]
param(
    [string]$VmRootPath = "C:\SOC-Lab\vm",
    [string]$IsoRootPath = "C:\SOC-Lab\iso",
    [string]$UbuntuIsoName = "ubuntu-22.04.5-live-server-amd64.iso",
    [string]$KaliIsoName = "kali-linux-2026.2-installer-amd64.iso"
)

$ErrorActionPreference = "Continue"

Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host " 🔍 [SOC LAB] Phase 32: Hyper-V Infrastructure Prerequisites Check" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan

$report = [ordered]@{
    Timestamp          = (Get-Date).ToString("yyyy-MM-ddTHH:mm:sszzz")
    HostName           = $env:COMPUTERNAME
    OSName             = (Get-CimInstance Win32_OperatingSystem).Caption
    OSVersion          = [System.Environment]::OSVersion.VersionString
    IsAdmin            = $false
    HyperVService      = "NotFound"
    HyperVServiceState = "NotFound"
    TotalCores         = 0
    LogicalProcessors  = 0
    TotalRAM_GB        = 0
    FreeRAM_GB         = 0
    TargetDriveFree_GB = 0
    TargetDrivePath    = $VmRootPath
    UbuntuIsoExists    = $false
    KaliIsoExists      = $false
    SubnetConflicts    = @()
    ExistingVMSwitches = @()
    ExistingSOCVMs     = @()
    PassAssessment     = $false
    BlockerReasons     = @()
}

# 1. Administrator Privileges
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
$report.IsAdmin = $isAdmin
if ($isAdmin) {
    Write-Host "[✔] Administrator Privileges: ELEVATED" -ForegroundColor Green
} else {
    Write-Host "[!] Administrator Privileges: NOT ELEVATED (Standard User Mode)" -ForegroundColor Yellow
    $report.BlockerReasons += "Administrator privileges required to create Hyper-V vSwitches and VMs."
}

# 2. OS and Hyper-V Service
$vmms = Get-Service vmms -ErrorAction SilentlyContinue
if ($vmms) {
    $report.HyperVService = "Installed"
    $report.HyperVServiceState = $vmms.Status.ToString()
    $svcColor = if ($vmms.Status -eq "Running") { "Green" } else { "Yellow" }
    Write-Host "[✔] Hyper-V Service (vmms): $($vmms.Status)" -ForegroundColor $svcColor
    if ($vmms.Status -ne "Running") {
        $report.BlockerReasons += "Hyper-V Service (vmms) is not in 'Running' state."
    }
} else {
    Write-Host "[✖] Hyper-V Service (vmms): NOT FOUND" -ForegroundColor Red
    $report.BlockerReasons += "Hyper-V Virtual Machine Management Service is not installed or enabled."
}

# 3. CPU and RAM Capacity
$proc = Get-CimInstance Win32_Processor
$totalCores = ($proc | Measure-Object -Property NumberOfCores -Sum).Sum
$totalLogProc = ($proc | Measure-Object -Property NumberOfLogicalProcessors -Sum).Sum
$report.TotalCores = $totalCores
$report.LogicalProcessors = $totalLogProc

$os = Get-CimInstance Win32_OperatingSystem
$totalRAM = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2)
$freeRAM = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
$report.TotalRAM_GB = $totalRAM
$report.FreeRAM_GB = $freeRAM

Write-Host "[✔] CPU Cores: $totalCores cores ($totalLogProc logical processors)" -ForegroundColor Green
Write-Host "[✔] Memory: Total ${totalRAM} GB | Free ${freeRAM} GB (Required for 4 VMs: 17 GB)" -ForegroundColor Green

if ($totalRAM -lt 16) {
    $report.BlockerReasons += "Total RAM is less than 16GB requirement."
}

# 4. Storage Space on Target Drive
$driveLetter = (Split-Path -Qualifier $VmRootPath).TrimEnd(':')
$drive = Get-PSDrive -Name $driveLetter -PSProvider FileSystem -ErrorAction SilentlyContinue
if ($drive) {
    $freeDriveGB = [math]::Round($drive.Free / 1GB, 2)
    $report.TargetDriveFree_GB = $freeDriveGB
    Write-Host "[✔] Target Storage (${driveLetter}:): Free ${freeDriveGB} GB (Required for VHDX: 166 GB)" -ForegroundColor Green
    if ($freeDriveGB -lt 50) {
        $report.BlockerReasons += "Target drive has less than 50GB free space for full VM provisioning."
    }
} else {
    Write-Host "[!] Target Drive '$driveLetter' not found." -ForegroundColor Yellow
}

# 5. ISO Images Inspection
$ubuntuIsoPath = Join-Path $IsoRootPath $UbuntuIsoName
$kaliIsoPath = Join-Path $IsoRootPath $KaliIsoName

$report.UbuntuIsoExists = (Test-Path $ubuntuIsoPath)
$report.KaliIsoExists = (Test-Path $kaliIsoPath)

if ($report.UbuntuIsoExists) {
    Write-Host "[✔] Ubuntu Server ISO: FOUND ($ubuntuIsoPath)" -ForegroundColor Green
} else {
    Write-Host "[!] Ubuntu Server ISO: NOT FOUND ($ubuntuIsoPath)" -ForegroundColor Yellow
    $report.BlockerReasons += "Ubuntu Server ISO missing at $ubuntuIsoPath"
}

if ($report.KaliIsoExists) {
    Write-Host "[✔] Kali Linux ISO: FOUND ($kaliIsoPath)" -ForegroundColor Green
} else {
    Write-Host "[!] Kali Linux ISO: NOT FOUND ($kaliIsoPath)" -ForegroundColor Yellow
    $report.BlockerReasons += "Kali Linux ISO missing at $kaliIsoPath"
}

# 6. Network Subnet Collision Analysis
Write-Host "`n[*] Inspecting local IP routes and adapters for collisions..." -ForegroundColor Cyan
$targetSubnets = @("10.77.10.", "10.77.20.", "10.77.30.")
$existingRoutes = Get-NetRoute -AddressFamily IPv4 -ErrorAction SilentlyContinue
$collisions = @()
foreach ($sub in $targetSubnets) {
    $match = $existingRoutes | Where-Object { $_.DestinationPrefix -like "$sub*" }
    if ($match) {
        foreach ($m in $match) {
            # Ignore expected vEthernet (soc-vsw-mgmt) route if already deployed
            if ($m.InterfaceAlias -ne "vEthernet (soc-vsw-mgmt)") {
                $collisions += "Subnet $sub conflicts with interface '$($m.InterfaceAlias)' (Route: $($m.DestinationPrefix))"
            }
        }
    }
}
$report.SubnetConflicts = $collisions
if ($collisions.Count -eq 0) {
    Write-Host "[✔] Network Collision Check: NO CONFLICTS (10.77.10/20/30.0/24 are clean)" -ForegroundColor Green
} else {
    foreach ($col in $collisions) {
        Write-Host "[!] Subnet Collision: $col" -ForegroundColor Yellow
        $report.BlockerReasons += $col
    }
}

# 7. Existing Hyper-V Switches and VMs (if accessible)
if ($isAdmin) {
    $switches = Get-VMSwitch -Name "soc-vsw-*" -ErrorAction SilentlyContinue
    if ($switches) {
        $report.ExistingVMSwitches = @($switches | Select-Object -ExpandProperty Name)
        Write-Host "[*] Existing SOC Switches: $($report.ExistingVMSwitches -join ', ')" -ForegroundColor Yellow
    }
    $vms = Get-VM -Name "soc-*" -ErrorAction SilentlyContinue
    if ($vms) {
        $report.ExistingSOCVMs = @($vms | Select-Object -ExpandProperty Name)
        Write-Host "[*] Existing SOC VMs: $($report.ExistingSOCVMs -join ', ')" -ForegroundColor Yellow
    }
}

# Overall Assessment
$report.PassAssessment = ($report.BlockerReasons.Count -eq 0)

Write-Host "`n====================================================================" -ForegroundColor Cyan
Write-Host " 📋 Prerequisites Assessment Summary" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan
if ($report.PassAssessment) {
    Write-Host "Result: PASS (Host is fully ready for Hyper-V provisioning)" -ForegroundColor Green
} else {
    Write-Host "Result: BLOCKED / ATTENTION REQUIRED" -ForegroundColor Yellow
    Write-Host "Blocker / Notice Items:" -ForegroundColor Yellow
    foreach ($b in $report.BlockerReasons) {
        Write-Host "  • $b" -ForegroundColor Yellow
    }
}

# Output JSON report object
return $report
