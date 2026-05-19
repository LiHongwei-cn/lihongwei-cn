# Simplified approach: try multiple keyboard shortcuts for upload
Add-Type -AssemblyName System.Windows.Forms

# Wait for things to settle
Start-Sleep -Seconds 2

# Activate the IDE window - use Alt+TAB simulation or process activation
$procs = Get-Process -Name "wechatdevtools" | Where-Object { $_.MainWindowTitle -like "*bp-monitor*" }
if ($procs.Count -eq 0) {
    Write-Host "IDE window not found"
    exit 1
}

$proc = $procs[0]
Write-Host "Found IDE: $($proc.MainWindowTitle)"

# Try approach: click in the middle of the IDE window, then navigate via keyboard
# First, set focus to IDE window by using its process
$proc.Refresh()
Start-Sleep -Milliseconds 500

# Method 1: Try Alt+Shift+U (common WeChat IDE upload shortcut)
Write-Host "Method 1: Alt+Shift+U"
[System.Windows.Forms.SendKeys]::SendWait('%+U')
Start-Sleep -Seconds 2
# Check if dialog opened by trying to type
[System.Windows.Forms.SendKeys]::SendWait('{ESC}')
Start-Sleep -Milliseconds 300

# Method 2: Alt then P then U (Project menu -> Upload)
Write-Host "Method 2: Alt, P, U"
[System.Windows.Forms.SendKeys]::SendWait('%')
Start-Sleep -Milliseconds 300
[System.Windows.Forms.SendKeys]::SendWait('P')
Start-Sleep -Milliseconds 500
[System.Windows.Forms.SendKeys]::SendWait('U')
Start-Sleep -Seconds 2
# Try to fill version
[System.Windows.Forms.SendKeys]::SendWait('1.0.2')
Start-Sleep -Milliseconds 300
[System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
Start-Sleep -Seconds 2

# Method 3: Alt then T then U (Tools menu -> Upload)
Write-Host "Method 3: Alt, T, U"
[System.Windows.Forms.SendKeys]::SendWait('{ESC}')
Start-Sleep -Milliseconds 300
[System.Windows.Forms.SendKeys]::SendWait('%')
Start-Sleep -Milliseconds 300
[System.Windows.Forms.SendKeys]::SendWait('T')
Start-Sleep -Milliseconds 500
[System.Windows.Forms.SendKeys]::SendWait('U')
Start-Sleep -Seconds 2
[System.Windows.Forms.SendKeys]::SendWait('1.0.2')
Start-Sleep -Milliseconds 300
[System.Windows.Forms.SendKeys]::SendWait('{TAB}')
Start-Sleep -Milliseconds 200
[System.Windows.Forms.SendKeys]::SendWait('optimized: loading, pull-refresh, med-edit, quick-nav')
Start-Sleep -Milliseconds 300
[System.Windows.Forms.SendKeys]::SendWait('{TAB}')
Start-Sleep -Milliseconds 200
[System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
Write-Host "Done - check IDE for upload dialog"
