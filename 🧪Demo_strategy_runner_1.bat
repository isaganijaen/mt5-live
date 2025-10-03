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
start "13" cmd /k "python strategy_13_demo.py"
start "26" cmd /k "python strategy_26.py"
start "28" cmd /k "python strategy_28.py"




REM -------------------------------------------------------------
REM ---   ⚠️ 39 ONWARD: See Demo_strategy_runner_2.bat          ---
REM start "39"  ......
REM .
REM .
REM .



REM -------------------------------------------------------------
REM ---         CURRENT PROFITABLE STRATEGIES                 ---
REM -------------------------------------------------------------




REM start "9" cmd /k "python strategy_09_demo.py" 







REM -------------------------------------------------------------
REM ---                     ARCHIVED                          ---
REM -------------------------------------------------------------
REM start "Strategy 07" cmd /k "python strategy_07.py" 
REM start "HFT-09" cmd /k "python strategy_09.py" 
REM start "8" cmd /k "python strategy_08_demo.py" 
REM start "17" cmd /k "python strategy_17_demo.py"

REM start "1" cmd /k "python strategy_01.py"  - Best in 1-4am and 10-5pm only 🟡
REM start "2" cmd /k "python strategy_02.py" 
REM start "3" cmd /k "python strategy_03.py" - Best in 1-4am and 10-5pm only 🟡
REM start "7" cmd /k "python strategy_07_demo.py"  
REM start "8" ARCHIVED 
REM start "Str-09" - MOVED to Profitiable Section
REM start "Str-10" - MOVED to Profitiable Section
REM start "10" cmd /k "python strategy_10_demo.py" - Best in 1-4am and 10-5pm only 🟡
REM start "11" cmd /k "python strategy_11_demo.py"
REM start "12" cmd /k "python strategy_12_demo.py"

REM start "14" cmd /k "python strategy_14_demo.py"
REM start "15" cmd /k "python strategy_15_demo.py"
REM start "16" cmd /k "python strategy_16_demo.py" - Best in 1-4am and 10-5pm only 🟡
REM start "17" ARCHIVED 
REM start "18" cmd /k "python strategy_18_demo.py"
REM start "19" cmd /k "python strategy_19_demo.py" - Best in 1-4am and 10-5pm only 🟡
REM start "20" cmd /k "python strategy_20_demo.py" - Best in 1-4am and 10-5pm only 🟡
REM start "21" cmd /k "python strategy_21_demo.py"
REM start "22" cmd /k "python strategy_22_demo.py"
REM start "23" cmd /k "python strategy_23_demo.py" - Best in 1-4am and 10-5pm only 🟡
REM start "24" cmd /k "python strategy_24_demo.py" - 24/7 high win rate but negative profit 🟡
REM start "25" cmd /k "python strategy_25.py"

REM start "27" cmd /k "python strategy_27.py"

REM start "29" cmd /k "python strategy_29.py"
REM start "30" cmd /k "python strategy_30.py" - Best in 1-4am and 10-5pm only 🟡
REM start "31" cmd /k "python strategy_31.py"
REM start "32" cmd /k "python strategy_32.py" - Best in 1-4am and 10-5pm only 🟡
REM start "33" cmd /k "python strategy_33.py"
REM start "34" cmd /k "python strategy_34.py"
REM start "35" cmd /k "python strategy_35.py"
REM start "36" cmd /k "python strategy_36.py"
REM start "37" cmd /k "python strategy_37.py"
REM start "38" cmd /k "python strategy_38.py"



 
echo All Live Trading Strategies have been launched in separate terminal windows.
pause
