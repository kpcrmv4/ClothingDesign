# Baby Fashion Engine - Windows installer
# Run from PowerShell:
#     powershell -ExecutionPolicy Bypass -File install.ps1
# Or right-click the file -> Run with PowerShell.
#
# What it does:
#   1. Checks Python 3.10+ and git are available
#   2. Clones / updates the repo at C:\clothingdesign
#   3. Creates a Python virtual environment + installs dependencies
#   4. Smoke-tests the server import
#   5. Adds 'baby-fashion-engine' to claude_desktop_config.json
#      (preserves any other MCP servers already configured;
#       backs up the existing file as *.backup)

[CmdletBinding()]
param(
    [string]$InstallPath = "C:\clothingdesign",
    [string]$Branch      = "claude/baby-dress-pattern-ZUGM7",
    [string]$RepoUrl     = "https://github.com/kpcrmv4/clothingdesign.git",
    [string]$ServerKey   = "baby-fashion-engine"
)

$ErrorActionPreference = "Stop"

function Write-Step($msg) {
    Write-Host ""
    Write-Host "==> $msg" -ForegroundColor Cyan
}
function Write-OK($msg)   { Write-Host "    [OK]   $msg" -ForegroundColor Green }
function Write-Warn2($msg){ Write-Host "    [WARN] $msg" -ForegroundColor Yellow }
function Write-Fail($msg) {
    Write-Host "    [FAIL] $msg" -ForegroundColor Red
    Write-Host ""
    Write-Host "Installation aborted." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=================================================="  -ForegroundColor Cyan
Write-Host "  Baby Fashion Engine - Windows Installer"           -ForegroundColor Cyan
Write-Host "=================================================="  -ForegroundColor Cyan
Write-Host "  Install path: $InstallPath"
Write-Host "  Branch:       $Branch"

# ------------------------------------------------------------
# 1. Prerequisites
# ------------------------------------------------------------
Write-Step "Checking prerequisites"

$pythonCmd = $null
foreach ($cmd in @("python", "py", "python3")) {
    $found = Get-Command $cmd -ErrorAction SilentlyContinue
    if ($found) {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python 3\.(\d+)") {
            $minor = [int]$Matches[1]
            if ($minor -ge 10) {
                $pythonCmd = $cmd
                Write-OK "Python: $ver  (using '$cmd')"
                break
            } else {
                Write-Warn2 "$cmd is $ver  (need 3.10+)"
            }
        }
    }
}
if (-not $pythonCmd) {
    Write-Fail "Python 3.10+ not found. Install from https://www.python.org/downloads/ and check 'Add Python to PATH'."
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Fail "git not found. Install Git for Windows from https://git-scm.com/."
}
Write-OK "git: $((git --version) -join '')"

# ------------------------------------------------------------
# 2. Repository
# ------------------------------------------------------------
Write-Step "Setting up repository at $InstallPath"

if (Test-Path (Join-Path $InstallPath ".git")) {
    Write-Host "    Existing repo detected; fetching updates"
    Push-Location $InstallPath
    try {
        & git fetch origin            | Out-Null
        & git checkout $Branch        | Out-Null
        & git pull origin $Branch     | Out-Null
        Write-OK "Updated to latest $Branch"
    } finally {
        Pop-Location
    }
} elseif (Test-Path $InstallPath) {
    Write-Fail "$InstallPath exists but is not a git repository. Move or delete it and re-run."
} else {
    & git clone --branch $Branch $RepoUrl $InstallPath
    if (-not (Test-Path (Join-Path $InstallPath ".git"))) {
        Write-Fail "git clone failed"
    }
    Write-OK "Repository cloned"
}

# ------------------------------------------------------------
# 3. Virtual environment
# ------------------------------------------------------------
Write-Step "Creating Python virtual environment"

$venvPath   = Join-Path $InstallPath ".venv"
$venvPython = Join-Path $venvPath    "Scripts\python.exe"

if (Test-Path $venvPython) {
    Write-OK "venv already exists, reusing"
} else {
    & $pythonCmd -m venv $venvPath
    if (-not (Test-Path $venvPython)) {
        Write-Fail "Failed to create venv at $venvPath"
    }
    Write-OK "venv created"
}

# ------------------------------------------------------------
# 4. Dependencies
# ------------------------------------------------------------
Write-Step "Installing dependencies (mcp, reportlab, Pillow)"

& $venvPython -m pip install --upgrade pip --quiet
$reqFile = Join-Path $InstallPath "requirements.txt"
& $venvPython -m pip install -r $reqFile --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Fail "pip install failed (exit code $LASTEXITCODE)"
}
Write-OK "Dependencies installed"

# ------------------------------------------------------------
# 5. Smoke test
# ------------------------------------------------------------
Write-Step "Testing server import"

$smoke = & $venvPython -c "import sys; sys.path.insert(0, r'$InstallPath'); import baby_pattern_server; print('ok')" 2>&1
if ($smoke -notmatch "^ok$") {
    Write-Host "    Output: $smoke" -ForegroundColor Red
    Write-Fail "Server failed to import"
}
Write-OK "Server imports successfully"

# ------------------------------------------------------------
# 6. Claude Desktop config
# ------------------------------------------------------------
Write-Step "Configuring Claude Desktop"

$configDir  = Join-Path $env:APPDATA "Claude"
$configFile = Join-Path $configDir "claude_desktop_config.json"
$serverPath = Join-Path $InstallPath "baby_pattern_server.py"

if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
    Write-OK "Created $configDir"
}

# Build new server entry as PSCustomObject
$newServer = [PSCustomObject]@{
    command = $venvPython
    args    = @($serverPath)
    cwd     = $InstallPath
}

if (Test-Path $configFile) {
    $raw = Get-Content $configFile -Raw -Encoding UTF8
    if ($raw.Trim().Length -gt 0) {
        try {
            $config = $raw | ConvertFrom-Json
        } catch {
            Write-Warn2 "Existing config is not valid JSON; starting fresh"
            $config = [PSCustomObject]@{}
        }
    } else {
        $config = [PSCustomObject]@{}
    }
    Copy-Item $configFile "$configFile.backup" -Force
    Write-OK "Backed up existing config -> claude_desktop_config.json.backup"
} else {
    $config = [PSCustomObject]@{}
}

# Ensure mcpServers exists
if (-not (Get-Member -InputObject $config -Name "mcpServers" -ErrorAction SilentlyContinue)) {
    $config | Add-Member -MemberType NoteProperty -Name "mcpServers" -Value ([PSCustomObject]@{})
}

# Add or replace our server entry
if (Get-Member -InputObject $config.mcpServers -Name $ServerKey -ErrorAction SilentlyContinue) {
    $config.mcpServers.$ServerKey = $newServer
    Write-OK "Replaced existing '$ServerKey' entry"
} else {
    $config.mcpServers | Add-Member -MemberType NoteProperty -Name $ServerKey -Value $newServer
    Write-OK "Added '$ServerKey' to mcpServers"
}

$config | ConvertTo-Json -Depth 10 | Out-File $configFile -Encoding utf8 -Force
Write-OK "Wrote $configFile"

# ------------------------------------------------------------
# Done
# ------------------------------------------------------------
Write-Host ""
Write-Host "=================================================="  -ForegroundColor Green
Write-Host "  Installation complete!"                            -ForegroundColor Green
Write-Host "=================================================="  -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Quit Claude Desktop completely"
Write-Host "       (system tray icon -> right click -> Quit)"
Write-Host "  2. Reopen Claude Desktop"
Write-Host "  3. Open any chat, look for the hammer icon (tools menu)"
Write-Host "       You should see 16 tools under 'baby-fashion-engine'"
Write-Host ""
Write-Host "Try it:"  -ForegroundColor Yellow
Write-Host "  Type in chat: 'list_all_patterns'  or  'show me all patterns'"
Write-Host ""
Write-Host "Generated PDF / PNG files will be saved to:"
Write-Host "  $InstallPath"  -ForegroundColor Yellow
Write-Host ""
