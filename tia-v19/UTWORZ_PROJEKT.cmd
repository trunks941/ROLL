@echo off
setlocal
set "ROLL_POWERSHELL=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if exist "%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe" set "ROLL_POWERSHELL=%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe"
"%ROLL_POWERSHELL%" -NoProfile -ExecutionPolicy RemoteSigned -File "%~dp0openness\Build-Roll.ps1" -Root "%~dp0."
set "ROLL_RESULT=%ERRORLEVEL%"
echo.
echo Kod zakonczenia: %ROLL_RESULT%. Raport: Dokumenty\ROLL_TIA_V19.
pause
exit /b %ROLL_RESULT%
