# Use UI Automation to find and click the Upload button in WeChat IDE
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

$automation = [System.Windows.Automation.AutomationElement]
$desktop = $automation::RootElement

# Find the WeChat IDE window
$condition = New-Object System.Windows.Automation.PropertyCondition(
    [System.Windows.Automation.AutomationElement]::NameProperty,
    "bp-monitor"
)
$ideWindow = $desktop::FindFirst([System.Windows.Automation.TreeScope]::Children, $condition)

if ($ideWindow -eq $null) {
    # Try finding WeChat IDE main window
    $condition2 = New-Object System.Windows.Automation.PropertyCondition(
        [System.Windows.Automation.AutomationElement]::NameProperty,
        "微信开发者工具"
    )
    $ideWindow = $desktop::FindFirst([System.Windows.Automation.TreeScope]::Children, $condition2)
}

if ($ideWindow -eq $null) {
    Write-Host "Could not find IDE window"
    exit 1
}

Write-Host "Found IDE window: $($ideWindow.Current.Name)"

# Focus the window
$ideWindow.SetFocus()
Start-Sleep -Milliseconds 500

# Search for "Upload" button - check all toolbar buttons
# In WeChat IDE, the upload button might be labeled "上传" or have a tooltip
$buttonCondition = New-Object System.Windows.Automation.PropertyCondition(
    [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
    [System.Windows.Automation.ControlType]::Button
)

$allButtons = $ideWindow.FindAll([System.Windows.Automation.TreeScope]::Descendants, $buttonCondition)

Write-Host "Found $($allButtons.Count) buttons"
$uploadBtn = $null

foreach ($btn in $allButtons) {
    $name = $btn.Current.Name
    $autoId = $btn.Current.AutomationId
    $helpText = $btn.Current.HelpText

    if ($name -or $autoId) {
        Write-Host "  Button: name='$name' autoId='$autoId' helpText='$helpText'"
    }

    # Look for upload button
    if ($name -like "*上传*" -or $name -like "*upload*" -or $name -like "*Upload*" -or
        $autoId -like "*upload*" -or $helpText -like "*上传*" -or $helpText -like "*upload*") {
        $uploadBtn = $btn
        Write-Host "  >>> FOUND UPLOAD BUTTON: $name"
        break
    }
}

if ($uploadBtn -eq $null) {
    # Try invoking via shortcut: Ctrl+Shift+U didn't work, try the toolbar
    # In some versions, the upload button is a ToolBar button without automation name
    # Let's try keyboard navigation: Alt then navigate
    Write-Host "Upload button not found via automation. Trying keyboard method..."

    # Try Alt+P for Project menu, then U for Upload
    [System.Windows.Forms.SendKeys]::SendWait('%PU')
    Start-Sleep -Seconds 3

    # Try if dialog appeared
    [System.Windows.Forms.SendKeys]::SendWait('1.0.2')
    Start-Sleep -Milliseconds 200
    [System.Windows.Forms.SendKeys]::SendWait('{TAB}')
    Start-Sleep -Milliseconds 200
    [System.Windows.Forms.SendKeys]::SendWait('loading states, pull-refresh, medication edit, quick nav')
    Start-Sleep -Milliseconds 200
    [System.Windows.Forms.SendKeys]::SendWait('{TAB}')
    Start-Sleep -Milliseconds 200
    [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
    Write-Host "Sent keyboard sequence: Alt+P, U, version, desc, Enter"
} else {
    # Click the upload button
    $invokePattern = $uploadBtn.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
    if ($invokePattern) {
        $invokePattern.Invoke()
        Write-Host "Clicked Upload button!"
        Start-Sleep -Seconds 2

        # Now the upload dialog should be open
        [System.Windows.Forms.SendKeys]::SendWait('1.0.2')
        Start-Sleep -Milliseconds 200
        [System.Windows.Forms.SendKeys]::SendWait('{TAB}')
        Start-Sleep -Milliseconds 200
        [System.Windows.Forms.SendKeys]::SendWait('optimized: loading states, pull-refresh, medication edit, quick nav')
        Start-Sleep -Milliseconds 300
        [System.Windows.Forms.SendKeys]::SendWait('{TAB}')
        Start-Sleep -Milliseconds 200
        [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
        Write-Host "Filled upload dialog and submitted"
    }
}
