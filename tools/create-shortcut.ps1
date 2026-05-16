$desktop = [Environment]::GetFolderPath('Desktop')
$vbsPath = "C:\Users\HP\Desktop\1\tools\claude-launcher.vbs"
$icoPath = "C:\Users\HP\Desktop\1\tools\claude-icon.ico"
$shortcutPath = Join-Path $desktop "Claude Code.lnk"

$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut($shortcutPath)
$sc.TargetPath = $vbsPath
$sc.WorkingDirectory = "C:\Users\HP\Desktop\1"
$sc.Description = "Claude Code - AI 编程助手 (DeepSeek)"
$sc.IconLocation = $icoPath
$sc.WindowStyle = 7
$sc.Save()

if (Test-Path $shortcutPath) {
    Write-Host "OK: 桌面快捷方式已创建 ->" $shortcutPath
} else {
    Write-Host "FAIL: 创建失败"
}
