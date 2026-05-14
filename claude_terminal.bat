@echo off
cd /d C:\Users\HP\Desktop\1
set HTTPS_PROXY=http://127.0.0.1:7897
start "Claude Code" cmd /k "cd /d C:\Users\HP\Desktop\1 && set HTTPS_PROXY=http://127.0.0.1:7897 && claude"