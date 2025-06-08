@echo off
REM setup_sync_task.bat
REM Creates a scheduled task to automatically sync repos

echo Creating scheduled task for repo synchronization...

REM Create a scheduled task to run every 30 minutes
schtasks /create /tn "HuesApply Repo Sync" /tr "PowerShell.exe -ExecutionPolicy Bypass -File \"c:\src\HuesApply\HA_backend\sync_repos.ps1\"" /sc HOURLY /mo 1 /st 00:00

echo.
echo Task created! The repositories will sync automatically every hour.
echo You can run the sync manually by:
echo  1. Running sync_repos.bat directly
echo  2. Running the PowerShell script: PowerShell.exe -ExecutionPolicy Bypass -File "c:\src\HuesApply\HA_backend\sync_repos.ps1"
echo  3. Running the bash script in Git Bash: ./sync_repos.sh
echo.

pause
