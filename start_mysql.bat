@echo off
echo Starting MySQL 8.0 Service...
net start MYSQL80
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ==============================================
    echo MySQL service started successfully!
    echo You can now close this window and return to IDE.
    echo ==============================================
) else (
    echo.
    echo Failed to start. Please make sure you right-clicked and selected "Run as administrator".
)
pause
