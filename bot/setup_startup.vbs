Set WshShell = CreateObject("WScript.Shell")
StartupPath = WshShell.SpecialFolders("Startup")
Set Shortcut = WshShell.CreateShortcut(StartupPath & "\TG-Bot.lnk")
Shortcut.TargetPath = "C:\Users\HP\Desktop\1\bot\start_bot.vbs"
Shortcut.WorkingDirectory = "C:\Users\HP\Desktop\1\bot"
Shortcut.WindowStyle = 7
Shortcut.Save
