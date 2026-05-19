Add-Type -AssemblyName System.Windows.Forms

# Wait for IDE to stabilize
Start-Sleep -Seconds 3

# Find WeChat IDE window by process
$procs = Get-Process -Name "wechatdevtools" -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -ne '' }
foreach ($p in $procs) {
    Write-Host ("Found window: '" + $p.MainWindowTitle + "' PID:" + $p.Id)
}

# Find the main IDE window - try to find by searching process windows
Add-Type @'
using System;
using System.Runtime.InteropServices;
using System.Text;
using System.Collections.Generic;

public class Win32API {
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();

    [DllImport("user32.dll")]
    public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);

    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

    [DllImport("user32.dll")]
    public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);

    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);

    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    public static List<IntPtr> FindWindowsByProcessId(uint processId) {
        List<IntPtr> windows = new List<IntPtr>();
        EnumWindows(delegate(IntPtr hWnd, IntPtr lParam) {
            uint pid;
            GetWindowThreadProcessId(hWnd, out pid);
            if (pid == processId) {
                StringBuilder sb = new StringBuilder(256);
                GetWindowText(hWnd, sb, 256);
                if (sb.Length > 0) {
                    windows.Add(hWnd);
                    Console.WriteLine("  Window: '" + sb.ToString() + "' Handle:" + hWnd);
                }
            }
            return true;
        }, IntPtr.Zero);
        return windows;
    }

    public const uint KEYEVENTF_KEYUP = 0x0002;
    public const int SW_RESTORE = 9;
    public const uint SWP_SHOWWINDOW = 0x0040;
    public static readonly IntPtr HWND_TOP = IntPtr.Zero;
}
'@

$KEYEVENTF_KEYUP = 0x0002
$VK_CONTROL = 0x11
$VK_SHIFT = 0x10

# Find IDE windows
foreach ($p in $procs) {
    $windows = [Win32API]::FindWindowsByProcessId($p.Id)
    foreach ($hwnd in $windows) {
        if ($hwnd -ne [IntPtr]::Zero) {
            Write-Host "Activating window handle: $hwnd"

            # Restore and focus
            [Win32API]::ShowWindow($hwnd, 9)  # SW_RESTORE
            Start-Sleep -Milliseconds 200
            [Win32API]::SetForegroundWindow($hwnd)
            Start-Sleep -Milliseconds 500

            # Try the upload keyboard shortcut
            # Many WeChat IDE versions use Ctrl+Shift+U for upload
            Write-Host "Trying upload shortcut..."

            # Ctrl+Shift+U
            [Win32API]::keybd_event($VK_CONTROL, 0, 0, [UIntPtr]::Zero)
            Start-Sleep -Milliseconds 30
            [Win32API]::keybd_event($VK_SHIFT, 0, 0, [UIntPtr]::Zero)
            Start-Sleep -Milliseconds 30
            [Win32API]::keybd_event(0x55, 0, 0, [UIntPtr]::Zero)  # U
            Start-Sleep -Milliseconds 100
            [Win32API]::keybd_event(0x55, 0, $KEYEVENTF_KEYUP, [UIntPtr]::Zero)
            [Win32API]::keybd_event($VK_SHIFT, 0, $KEYEVENTF_KEYUP, [UIntPtr]::Zero)
            [Win32API]::keybd_event($VK_CONTROL, 0, $KEYEVENTF_KEYUP, [UIntPtr]::Zero)

            Start-Sleep -Seconds 2

            # Type version and description into the upload dialog
            Write-Host "Typing version..."
            [System.Windows.Forms.SendKeys]::SendWait('1.0.2')
            Start-Sleep -Milliseconds 300
            [System.Windows.Forms.SendKeys]::SendWait('{TAB}')
            Start-Sleep -Milliseconds 300
            Write-Host "Typing description..."
            [System.Windows.Forms.SendKeys]::SendWait('v1.0.2: loading states, pull-refresh, med edit, quick nav')
            Start-Sleep -Milliseconds 500
            [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')

            Write-Host "Done - check if upload dialog appeared and submitted"
            break
        }
    }
}
