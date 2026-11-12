@echo off
REM ONE-TIME SETUP: creates .venv in this folder and installs comtypes, openpyxl, pillow.
REM Double-click once. Run again only if I tell you a new package is needed.
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating .venv with Python 3.13 64-bit ...
    py -3.13 -m venv .venv
    if errorlevel 1 (
        echo.
        echo SETUP FAILED - is 64-bit Python 3.13 installed? Try:  py -3.13 --version
        pause
        exit /b 1
    )
)

".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install comtypes openpyxl pillow
if errorlevel 1 (
    echo.
    echo SETUP FAILED - copy everything above and send it to me.
    pause
    exit /b 1
)

echo.
echo Setup done. Use run.bat (STAAD) and build_loadcalc.bat (Excel).
pause
