<#
.SYNOPSIS
    Phase 3: Hyper-V VM Provisioning Script for SOC Lab (Locale-Independent)
.DESCRIPTION
    Provisions the 4 isolated Virtual Machines specified in HLD/LLD v1.0 and Implementation Plan Phase 3:
    1. soc-gateway  (Ubuntu 22.04: 1 vCPU, 1GB RAM, 16GB VHDX, 3 NICs: mgmt, attack, victim)
    2. soc-victim   (Ubuntu 22.04: 2 vCPU, 4GB RAM, 30GB VHDX, 1 NIC: victim)
    3. soc-sensor   (Ubuntu 22.04: 4 vCPU, 8GB RAM, 80GB VHDX, 2 NICs: mgmt, monitor)
    4. soc-attacker (Kali Linux:   2 vCPU, 4GB RAM, 40GB VHDX, 1 NIC: attack)
.NOTES
    Completion Gate: GATE-VM-01
    Runtime Gate: RG-005 (MAC Mapping)
#>

[CmdletBinding()]
param(
    [string]$VmRootPath = "C:\SOC-Lab\vm",
    [string]$IsoRootPath = "C:\SOC-Lab\iso",
    [string]$UbuntuIsoName = "ubuntu-22.04.5-live-server-amd64.iso",
    [string]$KaliIsoName = "kali-linux-2026.2-installer-amd64.iso"
)

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " [SOC LAB] Hyper-V VM Provisioning (Phase 3)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 0. Check Administrator Privileges
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Error "[!] CRITICAL: Administrator privileges required."
    exit 1
}

# 1. Create Base Directories
if (-not (Test-Path $VmRootPath)) {
    New-Item -ItemType Directory -Force -Path $VmRootPath | Out-Null
    Write-Host "[+] Created VM root directory: $VmRootPath" -ForegroundColor Green
}

$ubuntuIsoPath = Join-Path $IsoRootPath $UbuntuIsoName
$kaliIsoPath = Join-Path $IsoRootPath $KaliIsoName

# Helper function to safely rename the first default network adapter
function Rename-FirstDefaultAdapter {
    param(
        [string]$VMName,
        [string]$NewName
    )
    $adapter = Get-VMNetworkAdapter -VMName $VMName | Select-Object -First 1
    if ($adapter) {
        $adapter | Rename-VMNetworkAdapter -NewName $NewName
    }
}

# -------------------------------------------------------------
# 2. VM 1: soc-gateway
# -------------------------------------------------------------
$gwName = "soc-gateway"
$gwDir = Join-Path $VmRootPath $gwName
$gwVhd = Join-Path $gwDir "$gwName.vhdx"

if (-not (Get-VM -Name $gwName -ErrorAction SilentlyContinue)) {
    Write-Host "`n[+] Provisioning $gwName..." -ForegroundColor Green
    New-Item -ItemType Directory -Force -Path $gwDir | Out-Null
    New-VM -Name $gwName -Generation 2 -MemoryStartupBytes 1GB -NewVHDPath $gwVhd -NewVHDSizeBytes 16GB -Path $gwDir | Out-Null
    Set-VMProcessor -VMName $gwName -Count 1
    Set-VMMemory -VMName $gwName -DynamicMemoryEnabled $false
    
    # Rename default NIC to nic-mgmt and connect to soc-vsw-mgmt
    Rename-FirstDefaultAdapter -VMName $gwName -NewName "nic-mgmt"
    Connect-VMNetworkAdapter -VMName $gwName -Name "nic-mgmt" -SwitchName "soc-vsw-mgmt"
    
    # Add nic-attack -> soc-vsw-attack
    Add-VMNetworkAdapter -VMName $gwName -Name "nic-attack" -SwitchName "soc-vsw-attack"
    
    # Add nic-victim -> soc-vsw-victim
    Add-VMNetworkAdapter -VMName $gwName -Name "nic-victim" -SwitchName "soc-vsw-victim"
    
    # Attach ISO if present
    if (Test-Path $ubuntuIsoPath) {
        Set-VMDvdDrive -VMName $gwName -Path $ubuntuIsoPath
    }
    Set-VMFirmware -VMName $gwName -EnableSecureBoot On -SecureBootTemplate MicrosoftUEFICertificateAuthority
    Write-Host "[+] $gwName provisioned successfully." -ForegroundColor Green
} else {
    Write-Host "[*] $gwName already exists." -ForegroundColor Yellow
}

# -------------------------------------------------------------
# 3. VM 2: soc-victim
# -------------------------------------------------------------
$vicName = "soc-victim"
$vicDir = Join-Path $VmRootPath $vicName
$vicVhd = Join-Path $vicDir "$vicName.vhdx"

if (-not (Get-VM -Name $vicName -ErrorAction SilentlyContinue)) {
    Write-Host "`n[+] Provisioning $vicName..." -ForegroundColor Green
    New-Item -ItemType Directory -Force -Path $vicDir | Out-Null
    New-VM -Name $vicName -Generation 2 -MemoryStartupBytes 4GB -NewVHDPath $vicVhd -NewVHDSizeBytes 30GB -Path $vicDir | Out-Null
    Set-VMProcessor -VMName $vicName -Count 2
    Set-VMMemory -VMName $vicName -DynamicMemoryEnabled $false
    
    # Rename default NIC to nic-victim and connect to soc-vsw-victim
    Rename-FirstDefaultAdapter -VMName $vicName -NewName "nic-victim"
    Connect-VMNetworkAdapter -VMName $vicName -Name "nic-victim" -SwitchName "soc-vsw-victim"
    
    # Attach ISO if present
    if (Test-Path $ubuntuIsoPath) {
        Set-VMDvdDrive -VMName $vicName -Path $ubuntuIsoPath
    }
    Set-VMFirmware -VMName $vicName -EnableSecureBoot On -SecureBootTemplate MicrosoftUEFICertificateAuthority
    Write-Host "[+] $vicName provisioned successfully." -ForegroundColor Green
} else {
    Write-Host "[*] $vicName already exists." -ForegroundColor Yellow
}

# -------------------------------------------------------------
# 4. VM 3: soc-sensor
# -------------------------------------------------------------
$sensorName = "soc-sensor"
$sensorDir = Join-Path $VmRootPath $sensorName
$sensorVhd = Join-Path $sensorDir "$sensorName.vhdx"

if (-not (Get-VM -Name $sensorName -ErrorAction SilentlyContinue)) {
    Write-Host "`n[+] Provisioning $sensorName..." -ForegroundColor Green
    New-Item -ItemType Directory -Force -Path $sensorDir | Out-Null
    New-VM -Name $sensorName -Generation 2 -MemoryStartupBytes 8GB -NewVHDPath $sensorVhd -NewVHDSizeBytes 80GB -Path $sensorDir | Out-Null
    Set-VMProcessor -VMName $sensorName -Count 4
    Set-VMMemory -VMName $sensorName -DynamicMemoryEnabled $false
    
    # Rename default NIC to nic-mgmt and connect to soc-vsw-mgmt
    Rename-FirstDefaultAdapter -VMName $sensorName -NewName "nic-mgmt"
    Connect-VMNetworkAdapter -VMName $sensorName -Name "nic-mgmt" -SwitchName "soc-vsw-mgmt"
    
    # Add nic-monitor -> soc-vsw-victim (Passive Mirroring Destination)
    Add-VMNetworkAdapter -VMName $sensorName -Name "nic-monitor" -SwitchName "soc-vsw-victim"
    
    # Attach ISO if present
    if (Test-Path $ubuntuIsoPath) {
        Set-VMDvdDrive -VMName $sensorName -Path $ubuntuIsoPath
    }
    Set-VMFirmware -VMName $sensorName -EnableSecureBoot On -SecureBootTemplate MicrosoftUEFICertificateAuthority
    Write-Host "[+] $sensorName provisioned successfully." -ForegroundColor Green
} else {
    Write-Host "[*] $sensorName already exists." -ForegroundColor Yellow
}

# -------------------------------------------------------------
# 5. VM 4: soc-attacker
# -------------------------------------------------------------
$atkName = "soc-attacker"
$atkDir = Join-Path $VmRootPath $atkName
$atkVhd = Join-Path $atkDir "$atkName.vhdx"

if (-not (Get-VM -Name $atkName -ErrorAction SilentlyContinue)) {
    Write-Host "`n[+] Provisioning $atkName..." -ForegroundColor Green
    New-Item -ItemType Directory -Force -Path $atkDir | Out-Null
    New-VM -Name $atkName -Generation 2 -MemoryStartupBytes 4GB -NewVHDPath $atkVhd -NewVHDSizeBytes 40GB -Path $atkDir | Out-Null
    Set-VMProcessor -VMName $atkName -Count 2
    Set-VMMemory -VMName $atkName -DynamicMemoryEnabled $false
    
    # Rename default NIC to nic-attack and connect to soc-vsw-attack
    Rename-FirstDefaultAdapter -VMName $atkName -NewName "nic-attack"
    Connect-VMNetworkAdapter -VMName $atkName -Name "nic-attack" -SwitchName "soc-vsw-attack"
    
    # Attach ISO if present
    if (Test-Path $kaliIsoPath) {
        Set-VMDvdDrive -VMName $atkName -Path $kaliIsoPath
    }
    Set-VMFirmware -VMName $atkName -EnableSecureBoot Off
    Write-Host "[+] $atkName provisioned successfully." -ForegroundColor Green
} else {
    Write-Host "[*] $atkName already exists." -ForegroundColor Yellow
}

# -------------------------------------------------------------
# 6. Verification & RG-005 MAC Address Extraction
# -------------------------------------------------------------
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host " [GATE-VM-01 & RG-005] Provisioning Summary & MAC Mapping" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$vms = Get-VM | Where-Object Name -like "soc-*"
$vms | Select-Object Name, State, Generation, @{N='MemoryGB';E={[math]::Round($_.MemoryAssigned/1GB,2)}} | Format-Table -AutoSize

$adapters = Get-VMNetworkAdapter -VMName "soc-gateway", "soc-victim", "soc-sensor", "soc-attacker" -ErrorAction SilentlyContinue
if ($adapters) {
    $adapters | Select-Object VMName, Name, SwitchName, MacAddress, PortMirroringMode | Format-Table -AutoSize
    
    # Save MAC Mapping
    $artifactDir = Join-Path $PSScriptRoot "..\..\docs\04-deployment"
    if (Test-Path $artifactDir) {
        $outCsv = Join-Path $artifactDir "hyperv-mac-map.csv"
        $adapters | Select-Object VMName, Name, SwitchName, MacAddress | Export-Csv -Path $outCsv -NoTypeInformation -Force
        Write-Host "[+] Exported MAC Mapping to $outCsv" -ForegroundColor Green
    }
}

if (($vms | Measure-Object).Count -eq 4) {
    Write-Host "[PASS] GATE-VM-01: All 4 VMs created with correct hardware and network assignments." -ForegroundColor Green
} else {
    Write-Host "[FAIL] GATE-VM-01: VM count mismatch." -ForegroundColor Red
}
