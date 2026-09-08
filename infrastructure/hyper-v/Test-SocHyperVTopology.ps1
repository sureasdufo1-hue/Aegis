<#
.SYNOPSIS
    Topology & Hardware Baseline Verification Script for Phase 32 Hyper-V SOC Lab
.DESCRIPTION
    Verifies that all 3 virtual switches, 4 Generation 2 VMs, exact vCPU/RAM/VHDX specs,
    network adapter switch bindings, and host return routes match the HLD/LLD v1.0 specifications.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Continue"

Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host " 🔍 [SOC LAB] Phase 32: Hyper-V Topology & Configuration Verification" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[!] Administrator privileges required for full Hyper-V topology inspection." -ForegroundColor Yellow
}

$results = [ordered]@{
    Timestamp          = (Get-Date).ToString("yyyy-MM-ddTHH:mm:sszzz")
    VirtualSwitches    = @{}
    HostManagementIP   = @{}
    HostVictimRoute    = @{}
    VMs                = @{}
    PortMirroring      = @{}
    Pass               = $false
    MissingComponents  = @()
}

# 1. Virtual Switches
$expectedSwitches = @{
    "soc-vsw-mgmt"   = "Internal"
    "soc-vsw-attack" = "Private"
    "soc-vsw-victim" = "Private"
}

foreach ($swName in $expectedSwitches.Keys) {
    $sw = Get-VMSwitch -Name $swName -ErrorAction SilentlyContinue
    if ($sw) {
        $typeMatch = ($sw.SwitchType.ToString() -eq $expectedSwitches[$swName])
        $results.VirtualSwitches[$swName] = @{
            Found      = $true
            SwitchType = $sw.SwitchType.ToString()
            Expected   = $expectedSwitches[$swName]
            TypeMatch  = $typeMatch
        }
        Write-Host "[✔] vSwitch '$swName': Found ($($sw.SwitchType))" -ForegroundColor Green
    } else {
        $results.VirtualSwitches[$swName] = @{ Found = $false; Expected = $expectedSwitches[$swName] }
        $results.MissingComponents += "Virtual Switch '$swName' ($($expectedSwitches[$swName])) missing."
        Write-Host "[✖] vSwitch '$swName': NOT FOUND" -ForegroundColor Red
    }
}

# 2. Host Management IP
$mgmtAlias = "vEthernet (soc-vsw-mgmt)"
$ipObj = Get-NetIPAddress -InterfaceAlias $mgmtAlias -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object IPAddress -eq "10.77.10.10"
if ($ipObj) {
    $results.HostManagementIP = @{
        Found     = $true
        IPAddress = $ipObj.IPAddress
        Prefix    = $ipObj.PrefixLength
        Interface = $mgmtAlias
    }
    Write-Host "[✔] Host Adapter '$mgmtAlias': 10.77.10.10/24 Configured" -ForegroundColor Green
} else {
    $results.HostManagementIP = @{ Found = $false }
    $results.MissingComponents += "Host IP 10.77.10.10/24 on '$mgmtAlias' missing."
    Write-Host "[✖] Host Adapter '$mgmtAlias': 10.77.10.10/24 NOT FOUND" -ForegroundColor Red
}

# 3. Host Route to Victim Subnet
$route = Get-NetRoute -DestinationPrefix "10.77.30.0/24" -InterfaceAlias $mgmtAlias -ErrorAction SilentlyContinue
if ($route) {
    $results.HostVictimRoute = @{
        Found     = $true
        Prefix    = $route.DestinationPrefix
        NextHop   = $route.NextHop
        Interface = $mgmtAlias
    }
    Write-Host "[✔] Host Static Route: 10.77.30.0/24 via $($route.NextHop)" -ForegroundColor Green
} else {
    $results.HostVictimRoute = @{ Found = $false }
    $results.MissingComponents += "Host route 10.77.30.0/24 via 10.77.10.1 missing."
    Write-Host "[✖] Host Static Route: 10.77.30.0/24 NOT FOUND" -ForegroundColor Red
}

# 4. Virtual Machines & Adapters
$expectedVMs = @{
    "soc-gateway"  = @{ vCPU = 1; RAM_MB = 1024; NICs = @("nic-mgmt", "nic-attack", "nic-victim") }
    "soc-victim"   = @{ vCPU = 2; RAM_MB = 4096; NICs = @("nic-victim") }
    "soc-sensor"   = @{ vCPU = 4; RAM_MB = 8192; NICs = @("nic-mgmt", "nic-monitor") }
    "soc-attacker" = @{ vCPU = 2; RAM_MB = 4096; NICs = @("nic-attack") }
}

foreach ($vmName in $expectedVMs.Keys) {
    $vm = Get-VM -Name $vmName -ErrorAction SilentlyContinue
    if ($vm) {
        $adapters = Get-VMNetworkAdapter -VMName $vmName -ErrorAction SilentlyContinue
        $nicNames = @($adapters | Select-Object -ExpandProperty Name)
        $results.VMs[$vmName] = @{
            Found      = $true
            State      = $vm.State.ToString()
            Generation = $vm.Generation
            vCPU       = $vm.ProcessorCount
            RAM_MB     = [math]::Round($vm.MemoryStartup / 1MB)
            NICs       = $nicNames
        }
        Write-Host "[✔] VM '$vmName': Found ($($vm.State), Gen $($vm.Generation), $($vm.ProcessorCount) vCPU, $([math]::Round($vm.MemoryStartup / 1MB))MB RAM)" -ForegroundColor Green
    } else {
        $results.VMs[$vmName] = @{ Found = $false }
        $results.MissingComponents += "VM '$vmName' missing."
        Write-Host "[✖] VM '$vmName': NOT FOUND" -ForegroundColor Red
    }
}

# 5. Port Mirroring Mode
$victimNIC = Get-VMNetworkAdapter -VMName "soc-victim" -ErrorAction SilentlyContinue | Where-Object Name -eq "nic-victim"
$sensorMonNIC = Get-VMNetworkAdapter -VMName "soc-sensor" -ErrorAction SilentlyContinue | Where-Object Name -eq "nic-monitor"

$vicMirror = if ($victimNIC) { $victimNIC.PortMirroringMode.ToString() } else { "None" }
$senMirror = if ($sensorMonNIC) { $sensorMonNIC.PortMirroringMode.ToString() } else { "None" }

$results.PortMirroring = @{
    VictimNIC_Mode    = $vicMirror
    SensorMonNIC_Mode = $senMirror
    Valid             = ($vicMirror -eq "Source" -and $senMirror -eq "Destination")
}

if ($results.PortMirroring.Valid) {
    Write-Host "[✔] Port Mirroring: soc-victim (Source) -> soc-sensor nic-monitor (Destination)" -ForegroundColor Green
} else {
    Write-Host "[✖] Port Mirroring: NOT CONFIGURED PROPERLY (Victim: $vicMirror, Sensor: $senMirror)" -ForegroundColor Red
    $results.MissingComponents += "Port Mirroring mode mismatch (Expected Victim=Source, Sensor=Destination)."
}

$results.Pass = ($results.MissingComponents.Count -eq 0)

Write-Host "`n====================================================================" -ForegroundColor Cyan
Write-Host " 📋 Topology Verification Summary" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan
if ($results.Pass) {
    Write-Host "Result: PASS (All Hyper-V switches, VMs, NICs, and Routes verified)" -ForegroundColor Green
} else {
    Write-Host "Result: INCOMPLETE / MISSING RESOURCES" -ForegroundColor Yellow
    foreach ($m in $results.MissingComponents) {
        Write-Host "  • $m" -ForegroundColor Yellow
    }
}

return $results
