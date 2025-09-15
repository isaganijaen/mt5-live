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
start "App" cmd /k "python app.py"
start "Database" cmd /k "python database_live.py"  
REM Increased interval from 1 minute to 17 minutes. Real Time data is not suitable for live trading because of latency issues
REM and frequent gaps in data. Will use this as initial data then append with broker data during live trading.
start "Market Data" cmd /k "python market_data.py"
REM start "Strategy 01" cmd /k "python strategy_01.py"        
REM start "Strategy 02" cmd /k "python strategy_02.py"           
REM start "Strategy 03" cmd /k "python strategy_03.py"      
start "Strategy 07" cmd /k "python strategy_07.py" 
start "Strategy 08 - FULL TS" cmd /k "python strategy_08.py" 

echo All Live Trading Strategies have been launched in separate terminal windows.
pause
