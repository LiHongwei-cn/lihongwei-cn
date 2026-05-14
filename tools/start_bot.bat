@echo off
cd /d C:\Users\HP\Desktop\1
set HTTPS_PROXY=http://127.0.0.1:7897
start /min python tools/autosave.py
start /min python bot/tgbot.py
