# sync_repos.ps1
# Script to sync changes from organization repo to personal fork for Vercel deployment
# Author: iNezerr

Write-Host "🔄 Starting synchronization between Hues-Apply/HA_backend and iNezerr/HA_backend..." -ForegroundColor Cyan

# Store the current directory
$CURRENT_DIR = Get-Location

# Check if the local repo exists
if (Test-Path "c:\src\HuesApply\HA_backend") {
    Set-Location -Path "c:\src\HuesApply\HA_backend"
    
    Write-Host "📋 Checking for uncommitted changes in Hues-Apply repo..." -ForegroundColor Yellow
    $status = git status --porcelain
    
    if ($status) {
        Write-Host "⚠️ Uncommitted changes detected. Committing them first..." -ForegroundColor Yellow
        git add .
        git commit -m "Auto-commit before sync: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        git push
        Write-Host "✅ Changes committed and pushed to Hues-Apply repo." -ForegroundColor Green
    } else {
        Write-Host "✅ No uncommitted changes in Hues-Apply repo." -ForegroundColor Green
    }
    
    # Make sure we have the latest changes
    Write-Host "⬇️ Pulling latest changes from Hues-Apply repo..." -ForegroundColor Blue
    git pull origin main
    
    # Now let's handle the personal fork
    Write-Host "🔍 Checking if iNezerr fork is configured as a remote..." -ForegroundColor Yellow
    $remotes = git remote
    
    if ($remotes -notcontains "personal") {
        Write-Host "➕ Adding iNezerr fork as 'personal' remote..." -ForegroundColor Yellow
        git remote add personal https://github.com/iNezerr/HA_backend.git
    } else {
        Write-Host "✅ Remote 'personal' already configured." -ForegroundColor Green
    }
    
    # Fetch from personal fork to make sure we're up to date
    Write-Host "⬇️ Fetching from iNezerr fork..." -ForegroundColor Blue
    git fetch personal
    
    # Push changes to personal fork
    Write-Host "⬆️ Pushing changes to iNezerr fork..." -ForegroundColor Blue
    git push personal main
    
    Write-Host "🎉 Synchronization complete! Vercel should now start deploying automatically." -ForegroundColor Green
    Write-Host "📊 Check deployment status at: https://vercel.com/inezerr/ha-backend" -ForegroundColor Cyan
    
    # Return to original directory
    Set-Location -Path $CURRENT_DIR
} else {
    Write-Host "❌ Error: Repository directory not found at c:/src/HuesApply/HA_backend" -ForegroundColor Red
    exit 1
}

Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
