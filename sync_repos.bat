@echo off
REM sync_repos.bat
REM Script to sync changes from organization repo to personal fork for Vercel deployment
REM Author: iNezerr

echo 🔄 Starting synchronization between Hues-Apply/HA_backend and iNezerr/HA_backend...

REM Store the current directory
set CURRENT_DIR=%CD%

REM Check if the local repo exists
if exist "c:\src\HuesApply\HA_backend" (
  cd "c:\src\HuesApply\HA_backend"
  
  echo 📋 Checking for uncommitted changes in Hues-Apply repo...
  git status --porcelain > temp.txt
  set /p GIT_STATUS=<temp.txt
  del temp.txt
  
  if defined GIT_STATUS (
    echo ⚠️ Uncommitted changes detected. Committing them first...
    git add .
    git commit -m "Auto-commit before sync: %DATE% %TIME%"
    git push
    echo ✅ Changes committed and pushed to Hues-Apply repo.
  ) else (
    echo ✅ No uncommitted changes in Hues-Apply repo.
  )
  
  REM Make sure we have the latest changes
  echo ⬇️ Pulling latest changes from Hues-Apply repo...
  git pull origin main
  
  REM Now let's handle the personal fork
  echo 🔍 Checking if iNezerr fork is configured as a remote...
  git remote | findstr personal > nul
  if errorlevel 1 (
    echo ➕ Adding iNezerr fork as 'personal' remote...
    git remote add personal https://github.com/iNezerr/HA_backend.git
  ) else (
    echo ✅ Remote 'personal' already configured.
  )
  
  REM Fetch from personal fork to make sure we're up to date
  echo ⬇️ Fetching from iNezerr fork...
  git fetch personal
  
  REM Push changes to personal fork
  echo ⬆️ Pushing changes to iNezerr fork...
  git push personal main
  
  echo 🎉 Synchronization complete! Vercel should now start deploying automatically.
  echo 📊 Check deployment status at: https://vercel.com/inezerr/ha-backend
  
  REM Return to original directory
  cd "%CURRENT_DIR%"
) else (
  echo ❌ Error: Repository directory not found at c:/src/HuesApply/HA_backend
  exit /b 1
)

pause
