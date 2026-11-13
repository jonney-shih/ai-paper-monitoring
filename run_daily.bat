@echo off
REM Daily AI paper monitoring. Output goes to data\run.log, then a dialog is shown.
REM Keep this file ASCII-only: cmd reads it in the OEM codepage and non-ASCII
REM comments can swallow line breaks.
REM If a real Python gets installed later, change PY below to just: python
set "PY=C:\Program Files\PostgreSQL\17\pgAdmin 4\python\python.exe"
set PYTHONUTF8=1
cd /d "%~dp0"
echo ==== %date% %time% ==== >> data\run.log
"%PY%" src\main.py >> data\run.log 2>&1
REM Use start so the dialog runs on its own and does not block the scheduled task.
REM Otherwise, if nobody clicks OK, the next scheduled run is refused.
REM notify.vbs starts powershell with a hidden window, so no black console flashes.
start "" wscript //nologo "%~dp0notify.vbs" %ERRORLEVEL%
