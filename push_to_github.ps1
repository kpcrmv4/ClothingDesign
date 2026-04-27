# Push Baby Fashion Engine to GitHub + prep for GitHub Pages.
# Run from PowerShell:
#   powershell -ExecutionPolicy Bypass -File push_to_github.ps1
#
# What it does:
#   1. Cleans any stale .git/index.lock
#   2. Stages all changes (Thai PDFs, gallery, subfolder structure)
#   3. Commits with a descriptive message
#   4. Pushes to origin on the current branch
#   5. Prints the URL to enable GitHub Pages

$ErrorActionPreference = 'Stop'
Set-Location -Path 'C:\clothingdesign'

function Write-Step($msg) { Write-Host ""; Write-Host "==> $msg" -ForegroundColor Cyan }
function Write-OK($msg)   { Write-Host "    [OK]   $msg" -ForegroundColor Green }
function Write-Fail($msg) { Write-Host "    [FAIL] $msg" -ForegroundColor Red; exit 1 }

# 1. Lock cleanup
Write-Step "Clearing stale git locks"
$lock = '.git\index.lock'
if (Test-Path $lock) {
    Remove-Item $lock -Force
    Write-OK "Removed $lock"
} else {
    Write-OK "No stale lock"
}

# 2. Make sure git knows who you are
Write-Step "Checking git identity"
$email = git config user.email
if (-not $email) {
    git config user.email "kpcrmv4@gmail.com"
    git config user.name  "kpcrmv4"
    Write-OK "Set local git identity"
} else {
    Write-OK "user.email = $email"
}

# 3. Stage + commit
Write-Step "Staging changes"
git add -A
$staged = git diff --cached --name-only
if (-not $staged) {
    Write-OK "Nothing to commit; tree is clean"
} else {
    Write-Host "    $($staged.Count) file(s) staged"
    Write-Step "Committing"
    $msg = @"
Add Thai-localized PDFs, gallery index.html, per-call output subfolders

- drawing.py: register Tahoma TTF for Thai glyph support
- patterns/*.py: pattern titles + cover instructions translated to Thai
- preview.py: Thai labels in preview thumbnails
- baby_pattern_server.py:
  - chdir to project folder on startup (fixes cwd=System32 bug)
  - per-call subfolder: outputs/<key>_<size>_<timestamp>/
  - auto-build Tailwind index.html gallery after each generation
  - auto-generate preview PNG alongside every PDF
  - new tool: rebuild_gallery_index
- migrate_from_system32.ps1: recover legacy outputs from System32
- outputs/: legacy dress + bloomers 3-6m from earlier session
"@
    git commit -m $msg
    Write-OK "Committed"
}

# 4. Push
Write-Step "Pushing to origin"
$branch = git branch --show-current
Write-Host "    branch: $branch"
git push -u origin $branch
if ($LASTEXITCODE -ne 0) {
    Write-Fail "git push failed (exit $LASTEXITCODE). Check your GitHub credentials / token."
}
Write-OK "Pushed"

# 5. GitHub Pages instructions
$repo = git config --get remote.origin.url
$repo = $repo -replace '\.git$', ''
$repo = $repo -replace 'https://github\.com/', ''
$user = $repo.Split('/')[0]
$name = $repo.Split('/')[1]

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Pushed! Now enable GitHub Pages:"                            -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  1. Open: https://github.com/$repo/settings/pages"            -ForegroundColor Yellow
Write-Host "  2. Build and deployment:"
Write-Host "       Source: Deploy from a branch"
Write-Host "       Branch: $branch  /  (root)"
Write-Host "  3. Click Save. Wait 1-2 minutes for deploy."
Write-Host ""
Write-Host "  Your gallery URL will be:"
Write-Host "    https://$user.github.io/$name/"                            -ForegroundColor Cyan
Write-Host ""
Write-Host "  (If branch is not 'main', GitHub may show a warning. Just"
Write-Host "   pick the same branch you pushed: $branch)"
Write-Host ""
