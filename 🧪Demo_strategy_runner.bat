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

REM -------------------------------------------------------------
REM ---                  UTILITIES                            ---
REM -------------------------------------------------------------
start "DB_Baseline" cmd /k "python database_baseline.py"  
start "Market Data" cmd /k "python market_data.py"


REM -------------------------------------------------------------
REM ---     BASELINE STAGE (Initial Data Collection)          ---
REM -------------------------------------------------------------
start "HFT-11-Wide-R1.2" cmd /k "python strategy_11_demo.py" 
start "HFT-11-Wide-R0.5" cmd /k "python strategy_12_demo.py" 

REM -------------------------------------------------------------
REM ---         CURRENT PROFITABLE STRATEGIES                 ---
REM -------------------------------------------------------------
start "HFT-09-Wide-R1" cmd /k "python strategy_09_demo.py" 
start "HFT-10-Wide-R1.2" cmd /k "python strategy_10_demo.py" 
start "Str-01" cmd /k "python strategy_01.py" 
start "Str-02" cmd /k "python strategy_02.py" 
start "Str-03" cmd /k "python strategy_03.py" 





REM -------------------------------------------------------------
REM ---                     ARCHIVED                          ---
REM -------------------------------------------------------------
REM start "Strategy 07" cmd /k "python strategy_07.py" 
REM start "HFT-09" cmd /k "python strategy_09.py" 




 
echo All Live Trading Strategies have been launched in separate terminal windows.
pause
