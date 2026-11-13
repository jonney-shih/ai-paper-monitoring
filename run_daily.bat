@echo off
REM Daily AI paper monitoring. Output goes to data\run.log, then a dialog is shown.
REM Keep this file ASCII-only: cmd reads it in the OEM codepage and non-ASCII
REM comments can swallow line breaks.
set PYTHONUTF8=1
cd /d "%~dp0"
if not exist data mkdir data

REM Find a working Python: py launcher, then python on PATH, then pgAdmin's bundled one.
REM (The Microsoft Store "python" stub fails the --version test, so it is skipped.)
set "PY="
py -3 --version >nul 2>&1 && set "PY=py -3"
if not defined PY (
  python --version >nul 2>&1 && set "PY=python"
)
if not defined PY set PY="C:\Program Files\PostgreSQL\17\pgAdmin 4\python\python.exe"

echo ==== %date% %time% ==== >> data\run.log
%PY% src\main.py >> data\run.log 2>&1
REM Use start so the dialog runs on its own and does not block the scheduled task.
REM Otherwise, if nobody clicks OK, the next scheduled run is refused.
REM notify.vbs starts powershell with a hidden window, so no black console flashes.
start "" wscript //nologo "%~dp0notify.vbs" %ERRORLEVEL%
