<#
.SYNOPSIS
    Phase 0: Host Readiness Verification Script
.DESCRIPTION
    Checks all host requirements: Hyper-V, Virtualization, WSL2, Docker, Git, RAM, Disk.
#>

$results = [ordered]@{}

# 1. OS & Build
$os = Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion, OsBuildNumber
$results["OS"] = "$($os.WindowsProductName) (Build $($os.OsBuildNumber))"

# 2. Hyper-V
$hv = Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -ErrorAction SilentlyContinue
$results["Hyper-V"] = $hv.State

# 3. CPU Virtualization
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1 Name, VirtualizationFirmwareEnabled, SecondLevelAddressTranslationExtensions
$results["CPU Virtualization"] = if ($cpu.VirtualizationFirmwareEnabled) { "Enabled" } else { "Disabled" }

# 4. RAM
$ram = Get-CimInstance Win32_ComputerSystem
$ramGB = [math]::Round($ram.TotalPhysicalMemory / 1GB, 2)
$results["Total RAM (GB)"] = $ramGB

# 5. Volumes
$volumes = Get-Volume | Where-Object DriveLetter -ne $null | ForEach-Object {
    "$($_.DriveLetter): $([math]::Round($_.SizeRemaining/1GB, 1)) GB Free / $([math]::Round($_.Size/1GB, 1)) GB Total"
}
$results["Disks"] = ($volumes -join ", ")

# 6. WSL
try {
    $wslOut = wsl --version 2>&1 | Out-String
    $results["WSL"] = ($wslOut.Trim() -split "`n")[0]
} catch {
    $results["WSL"] = "Not found"
}

# 7. Docker
try {
    $dockerVer = docker version --format '{{.Server.Version}}' 2>&1
    $results["Docker Server"] = $dockerVer.Trim()
} catch {
    $results["Docker Server"] = "Not running/Not found"
}

# 8. Git
try {
    $gitVer = git --version 2>&1
    $results["Git"] = $gitVer.Trim()
} catch {
    $results["Git"] = "Not found"
}

# 9. Existing ISOs or C:\SOC-Lab directory
$results["C:\SOC-Lab exists"] = Test-Path "C:\SOC-Lab"
$results["Ubuntu ISO exists"] = Test-Path "C:\SOC-Lab\iso\ubuntu-22.04.5-live-server-amd64.iso"
$results["Kali ISO exists"] = Test-Path "C:\SOC-Lab\iso\kali-linux-2026.2-installer-amd64.iso"

# Output
$results.GetEnumerator() | Format-Table -AutoSize
