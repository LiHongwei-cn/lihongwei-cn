$cli = "C:\Program Files (x86)\Tencent\微信web开发者工具\cli.bat"
$project = "C:\Users\HP\Desktop\1\bp-monitor\miniprogram"

Write-Host "Starting upload via CLI..."
$result = & $cli upload --project $project --version "1.0.2" --desc "optimized: loading, pull-refresh, med-edit, quick-nav" 2>&1
Write-Host "CLI output:"
Write-Host $result
Write-Host "Exit code: $LASTEXITCODE"
