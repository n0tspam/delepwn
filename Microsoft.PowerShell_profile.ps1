function spamcommit {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Message,
        
        [Parameter(Mandatory=$false)]
        [string]$Branch = "main"
    )
    
    try {
        # Check if we're in a git repository
        $gitStatus = git rev-parse --is-inside-work-tree 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Not in a git repository!"
            return
        }

        # Stage all changes
        Write-Host "Staging all changes..." -ForegroundColor Yellow
        git add .
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to stage changes"
        }

        # Commit with the provided message
        Write-Host "Committing changes..." -ForegroundColor Yellow
        git commit -m "$Message"
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to commit changes"
        }

        # Push to the specified branch
        Write-Host "Pushing to $Branch..." -ForegroundColor Yellow
        git push origin $Branch
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to push changes"
        }

        Write-Host "Successfully committed and pushed changes!" -ForegroundColor Green
    }
    catch {
        Write-Error "An error occurred: $_"
    }
}

# Add an alias for easier use (optional)
Set-Alias -Name spamc -Value spamcommit