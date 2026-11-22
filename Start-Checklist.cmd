@echo off
py -3 -B "%~dp0launch_checklist.py"
if errorlevel 1 pause
