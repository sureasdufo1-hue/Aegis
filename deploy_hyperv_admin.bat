@echo off
:: ============================================================================
:: SOC Lab: Run Hyper-V Deployment with Administrator Privileges
:: ============================================================================
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Running with Administrator privileges.
    powershell.exe -NoExit -ExecutionPolicy Bypass -File "%~dp0infrastructure\hyper-v\deploy_all.ps1" -StartVMs
) else (
    echo [!] Requesting Administrator elevation...
    powershell.exe -Command "Start-Process cmd.exe -ArgumentList '/c `"%~f0`"' -Verb RunAs"
)
