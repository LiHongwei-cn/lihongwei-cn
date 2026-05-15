$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut("$env:USERPROFILE\Desktop\MATLAB AI.lnk")
$sc.TargetPath = "$env:USERPROFILE\Desktop\1\matlab.bat"
$sc.WorkingDirectory = "$env:USERPROFILE\Desktop\1"
$sc.Description = "MATLAB + CarSim"
$sc.Save()
Write-Output "Shortcut created"
