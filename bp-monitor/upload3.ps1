Add-Type -AssemblyName System.Windows.Forms

Add-Type @'
using System;
using System.Runtime.InteropServices;
public class W32 {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")] public static extern bool AttachThreadInput(uint idAttach, uint idAttachTo, bool fAttach);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
    [DllImport("kernel32.dll")] public static extern uint GetCurrentThreadId();
    public const int SW_RESTORE = 9;
    public const int SW_SHOW = 5;
}
'@

# Find IDE window
$proc = Get-Process -Name "wechatdevtools" -ErrorAction SilentlyContinue |
    Where-Object { $_.MainWindowTitle -like "*bp-monitor*" } |
    Select-Object -First 1

if (-not $proc) {
    # Try any IDE window
    $proc = Get-Process -Name "wechatdevtools" -ErrorAction SilentlyContinue |
        Where-Object { $_.MainWindowTitle -ne '' } |
        Select-Object -First 1
}

if (-not $proc) {
    Write-Host "No IDE window found"
    exit 1
}

$hWnd = $proc.MainWindowHandle
Write-Host "Activating: $($proc.MainWindowTitle) (handle: $hWnd)"

# Force window to foreground
[W32]::ShowWindow($hWnd, 9)
Start-Sleep -Milliseconds 200
$foregroundThread = [W32]::GetWindowThreadProcessId($hWnd, [ref]0)
$currentThread = [W32]::GetCurrentThreadId()
[W32]::AttachThreadInput($currentThread, $foregroundThread, $true)
[W32]::SetForegroundWindow($hWnd)
[W32]::AttachThreadInput($currentThread, $foregroundThread, $false)
Start-Sleep -Milliseconds 500

Write-Host "Window activated. Trying upload..."

# Try keyboard shortcuts for Upload
# Method: Alt key to activate menu, then find Upload option

# Cancel any existing dialog first
[System.Windows.Forms.SendKeys]::SendWait('{ESC}')
Start-Sleep -Milliseconds 300

# Approach: Click toolbar area then try button
# Toolbar is at y=70 (below title bar at y=0-30, below menu bar at y=30-70)
# Upload button is on the right side of the toolbar
$rect = New-Object System.Drawing.Rectangle
$sig = @'
[DllImport("user32.dll")]
public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
[StructLayout(LayoutKind.Sequential)]
public struct RECT { public int Left, Top, Right, Bottom; }
[DllImport("user32.dll")]
public static extern bool SetCursorPos(int X, int Y);
[DllImport("user32.dll")]
public static extern void mouse_event(uint dwFlags, uint dx, uint dy, uint dwData, UIntPtr dwExtraInfo);
'@
$WinAPI = Add-Type -MemberDefinition $sig -Name "WinAPI2" -Namespace "Util" -PassThru
$rect = New-Object Util.RECT
[Util.WinAPI2]::GetWindowRect($hWnd, [ref]$rect)

# Try multiple click positions for the Upload button
# v2.01.2510290 toolbar: Upload is typically around 85-90% from left, ~70px from top
$toolbarY = $rect.Top + 70
# Try clicking at several right-side positions
$positions = @(
    @{X = $rect.Right - 90; Y = $toolbarY},
    @{X = $rect.Right - 130; Y = $toolbarY},
    @{X = $rect.Right - 170; Y = $toolbarY}
)

foreach ($pos in $positions) {
    Write-Host "Clicking at $($pos.X), $($pos.Y)"
    [Util.WinAPI2]::SetCursorPos($pos.X, $pos.Y)
    Start-Sleep -Milliseconds 100
    [Util.WinAPI2]::mouse_event(0x0002, 0, 0, 0, [UIntPtr]::Zero)  # LEFTDOWN
    Start-Sleep -Milliseconds 50
    [Util.WinAPI2]::mouse_event(0x0004, 0, 0, 0, [UIntPtr]::Zero)  # LEFTUP
    Start-Sleep -Seconds 1

    # Try to type into upload dialog if it appeared
    [System.Windows.Forms.SendKeys]::SendWait('1.0.2')
    Start-Sleep -Milliseconds 300
    [System.Windows.Forms.SendKeys]::SendWait('{TAB}')
    Start-Sleep -Milliseconds 200
    [System.Windows.Forms.SendKeys]::SendWait('loading states, pull-refresh, medication edit, quick nav')
    Start-Sleep -Milliseconds 300
    [System.Windows.Forms.SendKeys]::SendWait('{TAB}')
    Start-Sleep -Milliseconds 200
    [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
    Start-Sleep -Milliseconds 500
    # Escape to close dialog if it was the wrong button
    [System.Windows.Forms.SendKeys]::SendWait('{ESC}')
    Start-Sleep -Milliseconds 300
}

Write-Host "Done - check if upload dialog appeared"
