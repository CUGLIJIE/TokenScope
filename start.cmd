@echo off
setlocal
cd /d "%~dp0"
set PYTHONDONTWRITEBYTECODE=1
if not exist "tools\runtime\python.exe" goto system_python
tools\runtime\python.exe -m tools %*
goto done
:system_python
where py >nul 2>nul
if errorlevel 1 goto python
py -3 -m tools %*
goto done
:python
python -m tools %*
:done
if errorlevel 1 pause
