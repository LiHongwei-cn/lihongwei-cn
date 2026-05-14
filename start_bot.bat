@echo off
cd C:\Users\HP\Desktop\1
set HTTPS_PROXY=http://127.0.0.1:7897
start /min python autosave.py
start /min python tgbot.py
