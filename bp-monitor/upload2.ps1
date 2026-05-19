# Try clicking the Upload button via the toolbar
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

Add-Type @'
using System;
using System.Runtime.InteropServices;
using System.Text;
using System.Collections.Generic;

public class Win32API2 {
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);

    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);

    [DllImport("user32.dll")]
    public static extern bool SetCursorPos(int X, int Y);

    [DllImport("user32.dll")]
    public static extern void mouse_event(uint dwFlags, uint dx, uint dy, uint dwData, UIntPtr dwExtraInfo);

    [DllImport("user32.dll")]
    public static extern bool EnumChildWindows(IntPtr hWndParent, EnumWindowsProc lpEnumFunc, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern IntPtr SendMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern IntPtr SendMessage(IntPtr hWnd, uint Msg, IntPtr wParam, StringBuilder lParam);

    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [StructLayout(LayoutKind.Sequential)]
    public struct RECT {
        public int Left, Top, Right, Bottom;
    }

    public const uint MOUSEEVENTF_LEFTDOWN = 0x0002;
    public const uint MOUSEEVENTF_LEFTUP = 0x0004;
    public const int SW_RESTORE = 9;
    public const uint BM_CLICK = 0x00F5;
    public const uint WM_GETTEXT = 0x000D;
    public const uint WM_GETTEXTLENGTH = 0x000E;

    public static IntPtr FindWindowByTitle(string titlePart) {
        IntPtr found = IntPtr.Zero;
        EnumWindows(delegate(IntPtr hWnd, IntPtr lParam) {
            StringBuilder sb = new StringBuilder(256);
            GetWindowText(hWnd, sb, 256);
            if (sb.ToString().Contains(titlePart)) {
                found = hWnd;
                return false;
            }
            return true;
        }, IntPtr.Zero);
        return found;
    }

    public static void ClickAt(int x, int y) {
        SetCursorPos(x, y);
        mouse_event(MOUSEEVENTF_LEFTDOWN, (uint)x, (uint)y, 0, UIntPtr.Zero);
        System.Threading.Thread.Sleep(50);
        mouse_event(MOUSEEVENTF_LEFTUP, (uint)x, (uint)y, 0, UIntPtr.Zero);
    }
}
'@

# Find bp-monitor window
$hwnd = [Win32API2]::FindWindowByTitle("bp-monitor")
if ($hwnd -eq [IntPtr]::Zero) {
    Write-Host "Could not find IDE window"
    exit 1
}

# Show and focus
[Win32API2]::ShowWindow($hwnd, 9)
Start-Sleep -Milliseconds 300
[Win32API2]::SetForegroundWindow($hwnd)
Start-Sleep -Milliseconds 500

# Get window rect to calculate toolbar position
$rect = New-Object Win32API2+RECT
[Win32API2]::GetWindowRect($hwnd, [ref]$rect)
Write-Host "Window rect: L=$($rect.Left) T=$($rect.Top) R=$($rect.Right) B=$($rect.Bottom)"

# Toolbar is typically at the top. "Upload" button is on the right side of toolbar.
# Toolbar height ~40px from top. Upload button is ~120px from right edge.
$toolbarY = $rect.Top + 38  # Just below title bar, in toolbar area

# Try clicking "Upload" button area. It's typically on the right side of toolbar.
# First try: far right area of toolbar
$uploadX = $rect.Right - 80
$uploadY = $toolbarY

Write-Host "Clicking at X=$uploadX Y=$uploadY"
[Win32API2]::ClickAt($uploadX, $uploadY)
Start-Sleep -Seconds 1

# If a dialog appeared, it should be focused now
# Type version
[System.Windows.Forms.SendKeys]::SendWait('1.0.2')
Start-Sleep -Milliseconds 200
[System.Windows.Forms.SendKeys]::SendWait('{TAB}')
Start-Sleep -Milliseconds 200
[System.Windows.Forms.SendKeys]::SendWait('optimized: loading, pull-refresh, medication edit, quick nav')
Start-Sleep -Milliseconds 300
# Tab to next field or confirm
[System.Windows.Forms.SendKeys]::SendWait('{TAB}')
Start-Sleep -Milliseconds 200
[System.Windows.Forms.SendKeys]::SendWait('{ENTER}')

Write-Host "Done - check IDE for upload dialog"
