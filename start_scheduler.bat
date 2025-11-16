@echo off
cd /d D:\cursor\Backtothestart
C:\Python313\python.exe auto_cycle_scheduler.py >> D:\cursor\Backtothestart\logs\auto_cycle.log 2>&1
@echo ExitCode %errorlevel%
pause

