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
start "db" cmd /k "python database_baseline.py"  
start "mk" cmd /k "python market_data.py"


REM -------------------------------------------------------------
REM ---     BASELINE STAGE (Initial Data Collection)          ---
REM -------------------------------------------------------------
start "7" cmd /k "python strategy_07_demo.py"  
start "8" cmd /k "python strategy_08_demo.py" 
REM start "Str-09" MOVED to Profitiable Section
REM start "Str-10" MOVED to Profitiable Section
start "11" cmd /k "python strategy_11_demo.py"
start "12" cmd /k "python strategy_12_demo.py"
start "13" cmd /k "python strategy_13_demo.py"
start "14" cmd /k "python strategy_14_demo.py"
start "15" cmd /k "python strategy_15_demo.py"
start "16" cmd /k "python strategy_16_demo.py"
start "17" cmd /k "python strategy_17_demo.py"
start "18" cmd /k "python strategy_18_demo.py"

REM -------------------------------------------------------------
REM ---         CURRENT PROFITABLE STRATEGIES                 ---
REM -------------------------------------------------------------

start "1" cmd /k "python strategy_01.py" 
start "2" cmd /k "python strategy_02.py" 
start "3" cmd /k "python strategy_03.py" 

start "9" cmd /k "python strategy_09_demo.py" 
start "10" cmd /k "python strategy_10_demo.py" 





REM -------------------------------------------------------------
REM ---                     ARCHIVED                          ---
REM -------------------------------------------------------------
REM start "Strategy 07" cmd /k "python strategy_07.py" 
REM start "HFT-09" cmd /k "python strategy_09.py" 




 
echo All Live Trading Strategies have been launched in separate terminal windows.
pause
