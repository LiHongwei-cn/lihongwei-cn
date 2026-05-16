$workDir = "C:\Users\HP\Desktop\1"
$psPath = "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
$icoPath = "$workDir\tools\claude-icon.ico"
$launcherPath = "$workDir\tools\launcher.ps1"
$shortcutPath = "$env:USERPROFILE\Desktop\Claude Code.lnk"

$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut($shortcutPath)
$sc.TargetPath = $psPath
$sc.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$launcherPath`""
$sc.WorkingDirectory = $workDir
$sc.Description = "Claude Code - AI 编程助手 (DeepSeek)"
$sc.IconLocation = $icoPath
$sc.WindowStyle = 7
$sc.Save()

if (Test-Path $shortcutPath) {
    Write-Host "OK: 桌面快捷方式已更新 -> PowerShell 直达 wt.exe"
} else {
    Write-Host "FAIL: 更新失败"
}
