@echo off
REM Write the load calculation sheet (EDRC format) from the INPUTS blocks of the stage files.
REM No STAAD needed. Close the .xlsx in Excel first if it is open.
cd /d "%~dp0"
".venv\Scripts\python.exe" "Culvert_Design_Automation\02_Python\culvert_tool\build_loadcalc_excel.py"
if errorlevel 1 (
    echo.
    echo BUILD FAILED - copy everything above and send it to me.
    pause
    exit /b 1
)
echo.
echo Done. Open Culvert_Design_Automation\05_Output\Load_Calculation_Single_Cell.xlsx
pause
