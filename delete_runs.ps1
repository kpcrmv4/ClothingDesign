# Delete runs from outputs/, rebuild index.html via project Python,
# commit and push.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File delete_runs.ps1
#   powershell -ExecutionPolicy Bypass -File delete_runs.ps1 -Patterns "dress_*"

[CmdletBinding()]
param(
    [string[]]$Patterns = @("legacy_*")
)

$ErrorActionPreference = 'Continue'
Set-Location -Path 'C:\clothingdesign'

function Step($m){ Write-Host ""; Write-Host "==> $m" -ForegroundColor Cyan }
function OK($m)  { Write-Host "    [OK]   $m" -ForegroundColor Green }
function Warn($m){ Write-Host "    [WARN] $m" -ForegroundColor Yellow }
function Fail($m){ Write-Host "    [FAIL] $m" -ForegroundColor Red }

# 1. Delete matching folders
Step "Deleting matching runs"
$deleted = 0
$outputsDir = Join-Path $PWD "outputs"
if (Test-Path $outputsDir) {
    foreach ($pat in $Patterns) {
        $found = Get-ChildItem -Path $outputsDir -Directory -Filter $pat -ErrorAction SilentlyContinue
        if (-not $found) {
            Warn "no match for '$pat'"
            continue
        }
        foreach ($f in $found) {
            try {
                Write-Host "    removing $($f.Name)"
                Remove-Item -Recurse -Force $f.FullName -ErrorAction Stop
                $deleted++
            } catch {
                Fail "could not delete $($f.Name): $($_.Exception.Message)"
            }
        }
    }
} else {
    Warn "outputs/ folder missing"
}
OK "Deleted $deleted folder(s)"

# 2. Rebuild index.html by importing the server module (triggers _rebuild_index)
Step "Rebuilding index.html via baby_pattern_server"
$venvPy = "C:\clothingdesign\.venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
    Warn "venv python not found, falling back to system python"
    $venvPy = "python"
}
& $venvPy -c "import baby_pattern_server" 2>&1 | Out-Host
if ($LASTEXITCODE -ne 0) {
    Fail "import failed (exit $LASTEXITCODE)"
    Read-Host "Press Enter to close"
    exit 1
}
OK "index.html rebuilt"

# 3. git add + commit + push
Step "git add"
git add -A 2>&1 | Out-Host
if ($LASTEXITCODE -ne 0) {
    Fail "git add failed"
    Read-Host "Press Enter to close"
    exit 1
}

Step "git commit"
$msg = "delete $deleted run(s) from gallery"
$out = git commit -m $msg 2>&1
$out | Out-Host
if ($LASTEXITCODE -ne 0) {
    if ($out -match "nothing to commit|working tree clean") {
        Warn "Nothing to commit"
    } else {
        Fail "git commit failed"
        Read-Host "Press Enter to close"
        exit 1
    }
}

Step "git push"
$branch = (git branch --show-current).Trim()
git push origin $branch 2>&1 | Out-Host
if ($LASTEXITCODE -ne 0) {
    Fail "git push failed (auth?)"
    Read-Host "Press Enter to close"
    exit 1
}
OK "pushed to $branch"

Write-Host ""
Write-Host "Done. Wait ~1 min then refresh:" -ForegroundColor Green
Write-Host "  https://kpcrmv4.github.io/ClothingDesign/" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to close"
