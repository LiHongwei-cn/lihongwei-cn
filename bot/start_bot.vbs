Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = scriptDir

' Check environment variables
token = WshShell.ExpandEnvironmentStrings("%TELEGRAM_TOKEN%")
key = WshShell.ExpandEnvironmentStrings("%DEEPSEEK_API_KEY%")
If token = "%TELEGRAM_TOKEN%" Or key = "%DEEPSEEK_API_KEY%" Then
    MsgBox "请先设置 TELEGRAM_TOKEN 和 DEEPSEEK_API_KEY 环境变量", 48, "Bot 启动失败"
    WScript.Quit 1
End If

WshShell.Run "pythonw tgbot.py", 0, False
