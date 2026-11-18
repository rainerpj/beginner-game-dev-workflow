@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
if not errorlevel 1 goto run_py
python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
if not errorlevel 1 goto run_python
if not exist "%USERPROFILE%\.codex\tools\runtime\python.ps1" goto unavailable
powershell -NoProfile -File "%USERPROFILE%\.codex\tools\runtime\python.ps1" -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
if errorlevel 1 goto unavailable
powershell -NoProfile -File "%USERPROFILE%\.codex\tools\runtime\python.ps1" "start_progress.py" --open
set "WORKFLOW_EXIT=%errorlevel%"
goto end
:run_py
py -3 "start_progress.py" --open
set "WORKFLOW_EXIT=%errorlevel%"
goto end
:run_python
python "start_progress.py" --open
set "WORKFLOW_EXIT=%errorlevel%"
goto end
:unavailable
set "WORKFLOW_EXIT=1"
type "%~dp0python-required.txt"
echo.
:end
pause
exit /b %WORKFLOW_EXIT%
