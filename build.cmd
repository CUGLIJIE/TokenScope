@echo off
setlocal
cd /d "%~dp0"
set PYTHONDONTWRITEBYTECODE=1
set "builder=py -3"
if exist "tools\runtime\python.exe" set "builder=tools\runtime\python.exe"
%builder% -m PyInstaller --noconfirm --clean --onefile --windowed --name TokenScope --paths "%CD%" --add-data "%~dp0web;web" --distpath "dist" --workpath "build\cache" --specpath "build" "%~dp0tools\__main__.py"
exit /b %errorlevel%
