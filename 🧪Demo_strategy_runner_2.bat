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

start "45" cmd /k "python m1_3LH_1021_t150.py"
start "46" cmd /k "python m2_3LH_1021_t150.py"
start "47" cmd /k "python m1_3LH1021_ST150.py"
start "48" cmd /k "python m2_3LH1021_ST150.py"
start "49" cmd /k "python m1_3LH_r150r200.py"
start "50" cmd /k "python m2_3LH_r150r200.py"
start "51" cmd /k "python m1_3LH_S150_tinf.py"
start "52" cmd /k "python m2_3LH_S150_tinf.py"
start "53" cmd /k "python m1_3S150TinfTS21.py"
start "54" cmd /k "python m2_3S150TinfTS21.py"





 
echo All Live Trading Strategies have been launched in separate terminal windows.
pause
