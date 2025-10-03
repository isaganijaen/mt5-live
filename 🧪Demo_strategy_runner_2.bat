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
REM ---     BASELINE STAGE (Initial Data Collection)          ---
REM -------------------------------------------------------------

REM start "39" cmd /k "python m1_3LH_1021_t300.py"
REM start "40" cmd /k "python m1_3LH_1021_t350.py"
REM start "41" cmd /k "python m1_3LH_1021_tinf.py"
start "42" cmd /k "python m2_3LH_1021_t300.py"
start "43" cmd /k "python m2_3LH_1021_t350.py"
start "44" cmd /k "python m2_3LH_1021_tinf.py"
REM start "45" cmd /k "python m1_3LH_1021_t150.py"
start "46" cmd /k "python m2_3LH_1021_t150.py"
REM start "47" cmd /k "python m1_3LH1021_ST150.py"
start "48" cmd /k "python m2_3LH1021_ST150.py"
REM start "49" cmd /k "python m1_3LH_r150r200.py"
start "50" cmd /k "python m2_3LH_r150r200.py"
REM start "51" cmd /k "python m1_3LH_S150_tinf.py"
start "52" cmd /k "python m2_3LH_S150_tinf.py"
REM start "53" cmd /k "python m1_3S150TinfTS21.py"  - Best in 1-4am and 10-5pm only 🟡
start "54" cmd /k "python m2_3S150TinfTS21.py"
start "55/90" cmd /k "python m1_3S300TinfTS21.py"
start "56/91" cmd /k "python m2_3S300TinfTS21.py"
REM start "57" cmd /k "python m15_S350T350.py"
REM start "58" cmd /k "python m15_S350T600.py"
REM start "59" cmd /k "python m15_S350T16k.py"
REM start "60" cmd /k "python m1_3S300T350TS21.py"
start "61" cmd /k "python m1_3S300T450TS21.py"
start "62" cmd /k "python strategy_01_1am_4am_10am_5pm.py"




 
echo All Live Trading Strategies have been launched in separate terminal windows.
pause
