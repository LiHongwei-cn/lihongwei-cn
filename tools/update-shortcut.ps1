$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut("$env:USERPROFILE\Desktop\Claude Code.lnk")
$sc.TargetPath = "C:\Users\HP\Desktop\1\tools\claude-launcher.vbs"
$sc.WorkingDirectory = "C:\Users\HP\Desktop\1"
$sc.Description = "Claude Code - AI 编程助手 (DeepSeek)"
$sc.IconLocation = "C:\Users\HP\Desktop\1\tools\claude-icon.ico"
$sc.WindowStyle = 7
$sc.Save()

if (Test-Path "$env:USERPROFILE\Desktop\Claude Code.lnk") {
    Write-Host "OK: 桌面快捷方式已更新 -> claude-launcher.vbs"
} else {
    Write-Host "FAIL: 更新失败"
}
