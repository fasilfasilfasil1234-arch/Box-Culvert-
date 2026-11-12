@echo off
REM Run the STAAD stages (stage1, stage2, stage3 ...) into the OPEN STAAD file.
REM Before: open STAAD.Pro, start a blank file in kN and m, save it where you want, keep it open.
REM The script pauses after each stage: Enter = next stage, Q = stop. It never saves the STAAD file.
cd /d "%~dp0"
".venv\Scripts\python.exe" "Culvert_Design_Automation\02_Python\culvert_tool\run.py"
if errorlevel 1 pause
