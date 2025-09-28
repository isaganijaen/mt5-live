@echo off

REM Set the directory where your Python files are located
set SCRIPT_DIR=D:\MT5-LIVE

REM Change to the script directory
cd "%SCRIPT_DIR%"

REM Delete all .lock and .log files in the directory.
REM The /F switch forces deletion of read-only files.
REM The /Q switch runs in quiet mode, suppressing a confirmation prompt.
REM 2>nul redirects error messages (like "file not found" or "in use") to a null device,
REM effectively hiding them so the script doesn't stop.
del /F /Q "*.lock" 2>nul
del /F /Q "*.log" 2>nul

REM Start a new terminal for each script
REM start "App" cmd /k "python app.py"
start "Mk" cmd /k "python market_data.py"
start "Database" cmd /k "python database_live.py"  
REM start "LIVE - 14" cmd /k "python strategy_14_demo.py" 
start "LIVE - 20" cmd /k "python strategy_20_demo.py" 
 
echo All Live Trading Strategies have been launched in separate terminal windows.
pause
