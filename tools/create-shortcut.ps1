$desktop = [Environment]::GetFolderPath('Desktop')
$batPath = "C:\Users\HP\Desktop\1\tools\claude-desktop.bat"
$icoPath = "C:\Users\HP\Desktop\1\tools\claude-icon.ico"
$shortcutPath = Join-Path $desktop "Claude Code.lnk"

$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut($shortcutPath)
$sc.TargetPath = $batPath
$sc.WorkingDirectory = "C:\Users\HP\Desktop\1"
$sc.Description = "Claude Code - AI 编程助手 (DeepSeek)"
$sc.IconLocation = $icoPath
$sc.Save()

if (Test-Path $shortcutPath) {
    Write-Host "OK: 桌面快捷方式已创建 ->" $shortcutPath
} else {
    Write-Host "FAIL: 创建失败"
}
