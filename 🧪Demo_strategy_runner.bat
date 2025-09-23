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
REM start "8" ARCHIVED 
REM start "Str-09" - MOVED to Profitiable Section
REM start "Str-10" - MOVED to Profitiable Section
start "11" cmd /k "python strategy_11_demo.py"
start "12" cmd /k "python strategy_12_demo.py"
start "13" cmd /k "python strategy_13_demo.py"
start "14" cmd /k "python strategy_14_d                                     emo.py"
start "15" cmd /k "python strategy_15_demo.py"
start "16" cmd /k "python strategy_16_demo.py"
REM start "17" ARCHIVED 
start "18" cmd /k "python strategy_18_demo.py"
start "19" cmd /k "python strategy_19_demo.py"
start "20" cmd /k "python strategy_20_demo.py"
start "21" cmd /k "python strategy_21_demo.py"
start "22" cmd /k "python strategy_22_demo.py"
start "23" cmd /k "python strategy_23_demo.py"
start "24" cmd /k "python strategy_24_demo.py"
start "25" cmd /k "python strategy_25.py"
start "26" cmd /k "python strategy_26.py"
start "27" cmd /k "python strategy_27.py"
start "28" cmd /k "python strategy_28.py"
start "29" cmd /k "python strategy_29.py"
start "30" cmd /k "python strategy_30.py"

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
REM start "8" cmd /k "python strategy_08_demo.py" 
REM start "17" cmd /k "python strategy_17_demo.py"


 
echo All Live Trading Strategies have been launched in separate terminal windows.
pause
