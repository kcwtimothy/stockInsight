@echo off

REM Activate the virtual environment
call stockinsight\Scripts\activate.bat

REM Add the current directory to Python path
set PYTHONPATH=%PYTHONPATH%;%CD%

REM Set default values
set ticker_file=tickers.txt
set ec_date_file=eco_calendar_date.txt

REM Parse command line arguments
if not "%~1"=="" set ticker_file=%~1
if not "%~2"=="" set ec_date_file=%~2

REM Check if files exist
if not exist "%ticker_file%" (
    echo Error: Ticker file '%ticker_file%' not found.
    goto :eof
)

if not exist "%ec_date_file%" (
    echo Error: Economic calendar date file '%ec_date_file%' not found.
    goto :eof
)


echo Using ticker file: %ticker_file%
echo Using Date range provided by economic calendar date file: %ec_date_file%

REM Run the stock analysis script
python run_stockanalysis.py

REM Read dates from eco_calendar_date.txt and run the economic calendar script
for /f "tokens=1,2 delims=:" %%a in (%ec_date_file%) do (
    if "%%a"=="start_date" set ec_start_date=%%b
    if "%%a"=="end_date" set ec_end_date=%%b
)

REM Run the economic calendar script
python eco_calendar.py %ec_start_date% %ec_end_date%

REM Deactivate the virtual environment
conda deactivate

pause
