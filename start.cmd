@echo off
setlocal
cd /d "%~dp0"
set PYTHONDONTWRITEBYTECODE=1
where py >nul 2>nul
if errorlevel 1 goto python
py -3 -m tools %*
goto done
:python
python -m tools %*
:done
if errorlevel 1 pause
