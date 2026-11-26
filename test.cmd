@echo off
setlocal
cd /d "%~dp0"
set PYTHONDONTWRITEBYTECODE=1
where py >nul 2>nul
if errorlevel 1 goto python
py -3 -m unittest discover -s tests -v
exit /b %errorlevel%
:python
python -m unittest discover -s tests -v
exit /b %errorlevel%
