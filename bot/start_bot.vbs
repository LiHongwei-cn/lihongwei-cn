Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\HP\Desktop\1\bot"
WshShell.Run "C:\Users\HP\AppData\Local\Programs\Python\Python312\pythonw.exe tgbot.py", 0, False
