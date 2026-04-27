# One-shot migration: move pattern files Claude Desktop generated into
# C:\Windows\System32 (because of the cwd issue) back to C:\clothingdesign.
# After this runs once and the MCP server is restarted with the chdir fix,
# future generations will land here automatically.

$ErrorActionPreference = 'Stop'
$src = 'C:\Windows\System32'
$dst = 'C:\clothingdesign'

$patterns = @(
    'dress_pattern_*.pdf',
    'bloomers_pattern_*.pdf',
    'bib_pattern_*.pdf',
    'bonnet_pattern_*.pdf',
    'kimono_top_pattern_*.pdf',
    'pants_pattern_*.pdf',
    'tshirt_pattern_*.pdf',
    'romper_pattern_*.pdf',
    'flutter_romper_pattern_*.pdf',
    'sleep_sack_pattern_*.pdf',
    'preview_*.png',
    'cutting_layout_*.png'
)

$moved = 0
foreach ($pat in $patterns) {
    Get-ChildItem -Path $src -Filter $pat -ErrorAction SilentlyContinue | ForEach-Object {
        $target = Join-Path $dst $_.Name
        Move-Item -Path $_.FullName -Destination $target -Force
        Write-Host "  moved $($_.Name)" -ForegroundColor Green
        $moved++
    }
}

Write-Host ""
Write-Host "Done. Moved $moved file(s) to $dst" -ForegroundColor Cyan
Write-Host "You can close this window."
Start-Sleep -Seconds 3
