# Collect Pre-Change State for Phase 32A
$ErrorActionPreference = "Continue"

$baseDir = "C:\Users\user\Documents\ChatGPT\Suricata-Snort-SOC-Lab\evidence\EV-HYPERV-002"
if (-not (Test-Path $baseDir)) {
    New-Item -ItemType Directory -Path $baseDir -Force | Out-Null
}

# 1. Identity and Elevation
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
$isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

# 2. Network State
$adapters = Get-NetAdapter | Select-Object Name, InterfaceDescription, ifIndex, Status, MacAddress, LinkSpeed
$ipAddresses = Get-NetIPAddress | Select-Object InterfaceAlias, InterfaceIndex, IPAddress, IPv4Address, PrefixLength, AddressFamily, Type
$routes = Get-NetRoute | Select-Object DestinationPrefix, NextHop, InterfaceAlias, InterfaceIndex, RouteMetric, Protocol
$dns = Get-DnsClientServerAddress | Select-Object InterfaceAlias, InterfaceIndex, ServerAddresses

$netState = [PSObject]@{
    CollectedAt = (Get-Date).ToString("o")
    User = $identity.Name
    IsAdmin = $isAdmin
    Adapters = $adapters
    IPAddresses = $ipAddresses
    Routes = $routes
    DNS = $dns
}
$netState | ConvertTo-Json -Depth 5 | Set-Content -Path (Join-Path $baseDir 'prechange_network_state.json') -Encoding utf8

# 3. Hyper-V State
$vmSwitches = Get-VMSwitch -ErrorAction SilentlyContinue | Select-Object Name, SwitchType, NetAdapterInterfaceDescription, AllowManagementOS
$vms = Get-VM -ErrorAction SilentlyContinue | Select-Object Name, State, Status, CPUUsage, MemoryAssigned, Uptime, Generation
$vmNics = Get-VMNetworkAdapter -All -ErrorAction SilentlyContinue | Select-Object VMName, Name, SwitchName, IPAddresses, MacAddress, PortMirroringMode

$hypervState = [PSObject]@{
    CollectedAt = (Get-Date).ToString("o")
    VMSwitches = $vmSwitches
    VMs = $vms
    VMNetworkAdapters = $vmNics
    VmmsService = (Get-Service -Name vmms -ErrorAction SilentlyContinue | Select-Object Name, Status, StartType)
}
$hypervState | ConvertTo-Json -Depth 5 | Set-Content -Path (Join-Path $baseDir 'prechange_hyperv_state.json') -Encoding utf8

# 4. VMware and VMnet10 Check
$vmwareProcs = Get-Process -Name "*vmware*", "*vmnat*", "*vmnet*", "*vmx*" -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, Path, Company
$vmwareServices = Get-Service -Name "*VMware*", "*VMnet*" -ErrorAction SilentlyContinue | Select-Object Name, DisplayName, Status, StartType
$vmnet10Adapter = Get-NetAdapter -Name "*VMnet10*" -ErrorAction SilentlyContinue | Select-Object Name, InterfaceDescription, Status, MacAddress
$vmnet10IP = Get-NetIPAddress -InterfaceAlias "*VMnet10*" -ErrorAction SilentlyContinue | Select-Object InterfaceAlias, IPAddress, PrefixLength
$routes1077 = Get-NetRoute -DestinationPrefix "10.77.*" -ErrorAction SilentlyContinue | Select-Object DestinationPrefix, NextHop, InterfaceAlias, RouteMetric

$vmsPath = "C:\Users\user\Documents\Virtual Machines"
$lckFiles = Get-ChildItem -Path $vmsPath -Recurse -Filter "*.lck" -ErrorAction SilentlyContinue | Select-Object FullName

$depLines = @(
    "================================================================================",
    "VMware & VMnet10 Dependency & State Check",
    "Collected: $((Get-Date).ToString('o'))",
    "Host: $env:COMPUTERNAME",
    "User: $($identity.Name)",
    "IsAdmin: $isAdmin",
    "================================================================================",
    "",
    "1. VMware Services:",
    ($vmwareServices | Format-Table -AutoSize | Out-String),
    "2. VMware Running Processes:",
    ($vmwareProcs | Format-Table -AutoSize | Out-String),
    "3. VMnet10 Adapter Details:",
    ($vmnet10Adapter | Format-Table -AutoSize | Out-String),
    "4. VMnet10 IP Configuration:",
    ($vmnet10IP | Format-Table -AutoSize | Out-String),
    "5. 10.77.x.x Active Routes:",
    ($routes1077 | Format-Table -AutoSize | Out-String),
    "6. VMware Virtual Machines Directory Lock Files (*.lck):",
    ($lckFiles | Format-Table -AutoSize | Out-String),
    "7. Summary of Lock Files Count: $($lckFiles.Count)",
    "================================================================================"
)

$depLines -join "`r`n" | Set-Content -Path (Join-Path $baseDir 'vmnet10_dependency_check.txt') -Encoding utf8

Write-Host "[+] Pre-change evidence collection completed successfully in $baseDir" -ForegroundColor Green
