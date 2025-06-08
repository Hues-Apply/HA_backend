# Repository Sync Scripts

These scripts help synchronize changes between the organization repository (Hues-Apply/HA_backend) and your personal fork (iNezerr/HA_backend) to trigger automatic deployments on Vercel.

## Available Scripts

1. **sync_repos.bat** - Windows batch file for manual synchronization
2. **sync_repos.ps1** - PowerShell script for manual synchronization (prettier output)
3. **sync_repos.sh** - Bash script for use in Git Bash or WSL
4. **setup_sync_task.bat** - Creates a Windows scheduled task for automatic synchronization

## How to Use

### Manual Synchronization

Choose one of these methods:

1. Double-click on `sync_repos.bat` to run the batch file version
2. Right-click on `sync_repos.ps1` and select "Run with PowerShell"
3. In Git Bash or WSL, run: `./sync_repos.sh`

### Automatic Synchronization

1. Run `setup_sync_task.bat` as Administrator
2. This will create a scheduled task that runs every hour to sync your repositories

## What the Scripts Do

1. Check if there are any uncommitted changes in the local repository
2. Commit and push any changes to the organization repository
3. Pull the latest changes from the organization repository
4. Set up your personal repository as a remote (if not already done)
5. Push all changes to your personal fork
6. Vercel will automatically deploy from your personal fork

## Troubleshooting

- If you get Git authentication errors, make sure you're logged in to Git with credentials that have access to both repositories
- You might need to use a Personal Access Token for authentication with GitHub
- The scheduled task requires PowerShell to be allowed to run scripts (`Set-ExecutionPolicy RemoteSigned` or `-ExecutionPolicy Bypass` parameter)

## Manual Setup (if scripts don't work)

```bash
# Add your personal fork as a remote
git remote add personal https://github.com/iNezerr/HA_backend.git

# Push changes to your fork
git push personal main
```
