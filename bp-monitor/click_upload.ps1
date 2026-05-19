# Simplified click script using pure PowerShell + Win32
Add-Type -AssemblyName System.Windows.Forms

$sig = @'
using System;
using System.Runtime.InteropServices;
using System.Text;

public class Win32Click {
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hWnd, ref RECT lpRect);

    [DllImport("user32.dll")]
    public static extern bool SetCursorPos(int X, int Y);

    [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

    [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    public static extern int GetWindowTextLength(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern IntPtr FindWindowEx(IntPtr hWndParent, IntPtr hWndChildAfter, string lpszClass, string lpszWindow);

    [DllImport("user32.dll")]
    public static extern bool EnumChildWindows(IntPtr hWndParent, EnumChildProc lpEnumFunc, IntPtr lParam);

    public delegate bool EnumChildProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);

    [DllImport("user32.dll")]
    public static extern bool AttachThreadInput(uint idAttach, uint idAttachTo, bool fAttach);

    [DllImport("kernel32.dll")]
    public static extern uint GetCurrentThreadId();

    [StructLayout(LayoutKind.Sequential)]
    public struct RECT {
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }

    public const uint MOUSEEVENTF_LEFTDOWN = 0x0002;
    public const uint MOUSEEVENTF_LEFTUP = 0x0004;
    public const int SW_RESTORE = 9;
    public const int SW_SHOW = 5;

    public static void MouseClick(int x, int y) {
        SetCursorPos(x, y);
        System.Threading.Thread.Sleep(30);
        mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, UIntPtr.Zero);
        System.Threading.Thread.Sleep(30);
        mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, UIntPtr.Zero);
    }

    [DllImport("user32.dll")]
    static extern void mouse_event(uint dwFlags, uint dx, uint dy, uint dwData, UIntPtr dwExtraInfo);
}
'@

Add-Type -TypeDefinition $sig -ErrorAction Stop

# Find the WeChat IDE window
$proc = Get-Process -Name "wechatdevtools" -ErrorAction SilentlyContinue |
    Where-Object { $_.MainWindowTitle -like "*bp-monitor*" } |
    Select-Object -First 1

if (-not $proc) {
    Write-Host "bp-monitor IDE window not found. Looking for any IDE window..."
    $proc = Get-Process -Name "wechatdevtools" -ErrorAction SilentlyContinue |
        Where-Object { $_.MainWindowTitle.Length -gt 0 } |
        Select-Object -First 1
}

if (-not $proc) {
    Write-Host "No IDE window found at all"
    exit 1
}

$hWnd = $proc.MainWindowHandle
Write-Host "Found window: $($proc.MainWindowTitle)"

# Activate window
[Win32Click]::ShowWindow($hWnd, 9)
Start-Sleep -Milliseconds 200

$fgThread = 0
[Win32Click]::GetWindowThreadProcessId($hWnd, [ref]$fgThread)
$curThread = [Win32Click]::GetCurrentThreadId()
[Win32Click]::AttachThreadInput($curThread, $fgThread, $true)
[Win32Click]::SetForegroundWindow($hWnd)
[Win32Click]::AttachThreadInput($curThread, $fgThread, $false)
Start-Sleep -Milliseconds 500

# Get window size
$rect = New-Object Win32Click+RECT
[Win32Click]::GetWindowRect($hWnd, [ref]$rect)
$width = $rect.Right - $rect.Left
$height = $rect.Bottom - $rect.Top
Write-Host "Window: ${width}x${height} at ($($rect.Left), $($rect.Top))"

# Title bar is ~30px, menu bar is ~25px, toolbar is ~40px
# Toolbar bottom edge is at ~95px from window top
# Upload button is on the right side of toolbar, around 85-95% from left

# Try multiple positions for the Upload button
$clickPositions = @()
for ($pct = 95; $pct -ge 80; $pct -= 5) {
    $x = $rect.Left + [int]($width * $pct / 100)
    $y = $rect.Top + 85  # middle of toolbar area
    $clickPositions += @{X=$x; Y=$y}
}

Write-Host "Trying $($clickPositions.Count) positions for upload button..."

foreach ($pos in $clickPositions) {
    Write-Host "Clicking ($($pos.X), $($pos.Y))..."
    [Win32Click]::MouseClick($pos.X, $pos.Y)
    Start-Sleep -Seconds 1

    # Try typing into dialog
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
    # Close dialog if wrong button
    [System.Windows.Forms.SendKeys]::SendWait('{ESC}')
    Start-Sleep -Milliseconds 300
}

Write-Host "Done. Check if upload dialog appeared in IDE."
