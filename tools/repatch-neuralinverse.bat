@echo off
REM Re-applies NeuralInverse dev patches after an app update.
REM Right-click -> Run as administrator (or it will self-elevate).
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)
python "C:\Users\jobal\dev\neuralinverse\tools\live-patch.py"
echo.
echo Done. If any patch reported a missing pattern (app update changed the
echo bundle), tell ZCode so the patterns can be updated.
pause
