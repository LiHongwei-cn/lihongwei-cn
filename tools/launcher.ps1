$workDir = "C:\Users\HP\Desktop\1"

$wtArgs = '-w -1 new-tab --title "Claude Code" -d "' + $workDir + '" cmd /k "set CLAUDE_CODE_ENTRYPOINT=cli && claude --dangerously-skip-permissions --no-chrome"'

Start-Process -FilePath wt.exe -ArgumentList $wtArgs
