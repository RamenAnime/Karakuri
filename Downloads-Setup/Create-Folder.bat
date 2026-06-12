@echo off
REM Double-click to create Downloads\Karakuri and open it in Explorer
set KARAKURI=%USERPROFILE%\Downloads\Karakuri
if not exist "%KARAKURI%" mkdir "%KARAKURI%"
echo Created: %KARAKURI%
echo.
echo Next: open COPY-PASTE.txt in this repo and follow Step 2 in PowerShell.
explorer "%KARAKURI%"
pause
