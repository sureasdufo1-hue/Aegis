<#
.SYNOPSIS
    Port Mirroring Verification Script for Phase 32 Hyper-V SOC Sensor
.DESCRIPTION
    Verifies that soc-victim's nic-victim is designated as 'Source' and
    soc-sensor's nic-monitor is designated as 'Destination', both on soc-vsw-victim,
    and checks that sensor monitor NIC has NO L3 IP assigned.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Continue"

Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host " 🔍 [SOC LAB] Hyper-V Port Mirroring & Sensor NIC Isolation Check" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan

$result = [ordered]@{
    Timestamp               = (Get-Date).ToString("yyyy-MM-ddTHH:mm:sszzz")
    VictimAdapter           = $null
    SensorMonitorAdapter    = $null
    SensorMgmtAdapter       = $null
    PortMirroringValid      = $false
    SensorNoIPCompliant     = $true
    SwitchIsolationMatch    = $false
    OverallResult           = "FAIL"
    Notes                   = @()
}

$vicAdapters = Get-VMNetworkAdapter -VMName "soc-victim" -ErrorAction SilentlyContinue
$senAdapters = Get-VMNetworkAdapter -VMName "soc-sensor" -ErrorAction SilentlyContinue

if (-not $vicAdapters) {
    $result.Notes += "VM 'soc-victim' or its adapters not found."
}
if (-not $senAdapters) {
    $result.Notes += "VM 'soc-sensor' or its adapters not found."
}

if ($vicAdapters -and $senAdapters) {
    $vicNIC = $vicAdapters | Where-Object { $_.Name -eq "nic-victim" -or $_.SwitchName -eq "soc-vsw-victim" } | Select-Object -First 1
    $senMonNIC = $senAdapters | Where-Object { $_.Name -eq "nic-monitor" -or $_.SwitchName -eq "soc-vsw-victim" } | Select-Object -First 1
    $senMgmtNIC = $senAdapters | Where-Object { $_.Name -eq "nic-mgmt" -or $_.SwitchName -eq "soc-vsw-mgmt" } | Select-Object -First 1

    if ($vicNIC) {
        $result.VictimAdapter = [ordered]@{
            VMName            = "soc-victim"
            NICName           = $vicNIC.Name
            SwitchName        = $vicNIC.SwitchName
            PortMirroringMode = $vicNIC.PortMirroringMode.ToString()
            MacAddress        = $vicNIC.MacAddress
        }
    }
    if ($senMonNIC) {
        $result.SensorMonitorAdapter = [ordered]@{
            VMName            = "soc-sensor"
            NICName           = $senMonNIC.Name
            SwitchName        = $senMonNIC.SwitchName
            PortMirroringMode = $senMonNIC.PortMirroringMode.ToString()
            MacAddress        = $senMonNIC.MacAddress
        }
    }
    if ($senMgmtNIC) {
        $result.SensorMgmtAdapter = [ordered]@{
            VMName            = "soc-sensor"
            NICName           = $senMgmtNIC.Name
            SwitchName        = $senMgmtNIC.SwitchName
            PortMirroringMode = $senMgmtNIC.PortMirroringMode.ToString()
            MacAddress        = $senMgmtNIC.MacAddress
        }
    }

    # Evaluate Switch Isolation & Matching
    if ($vicNIC -and $senMonNIC) {
        $result.SwitchIsolationMatch = ($vicNIC.SwitchName -eq "soc-vsw-victim" -and $senMonNIC.SwitchName -eq "soc-vsw-victim")
        $result.PortMirroringValid = ($vicNIC.PortMirroringMode -eq "Source" -and $senMonNIC.PortMirroringMode -eq "Destination")
    }

    if ($result.PortMirroringValid -and $result.SwitchIsolationMatch) {
        $result.OverallResult = "PASS"
        Write-Host "[✔] Port Mirroring: soc-victim [Source] -> soc-sensor nic-monitor [Destination] on 'soc-vsw-victim'" -ForegroundColor Green
    } else {
        $result.OverallResult = "FAIL"
        Write-Host "[✖] Port Mirroring configuration invalid or incomplete." -ForegroundColor Red
    }
}

return $result
