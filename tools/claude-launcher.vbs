Set WshShell = CreateObject("WScript.Shell")
workDir = "C:\Users\HP\Desktop\1"
WshShell.Run "wt.exe -d """ & workDir & """ cmd /k ""set CLAUDE_CODE_ENTRYPOINT=cli && claude --dangerously-skip-permissions --no-chrome""", 0, False
