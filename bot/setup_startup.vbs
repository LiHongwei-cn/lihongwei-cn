Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

Set WshShell = CreateObject("WScript.Shell")
StartupPath = WshShell.SpecialFolders("Startup")
Set Shortcut = WshShell.CreateShortcut(StartupPath & "\TG-Bot.lnk")
Shortcut.TargetPath = scriptDir & "\start_bot.vbs"
Shortcut.WorkingDirectory = scriptDir
Shortcut.WindowStyle = 7
Shortcut.Save
