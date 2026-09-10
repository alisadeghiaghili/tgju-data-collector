@echo off
REM Daily collection job. Schedule via Task Scheduler (recommended off-peak).
REM
REM Example (schtasks):
REM   schtasks /Create /TN "TGJU-Daily" /SC DAILY /ST 21:15 /TR "\"%~dp0daily_job.bat\""

setlocal
cd /d "%~dp0.."

if exist .env (
  for /f "usebackq delims=" %%a in (".env") do (
    echo %%a | findstr /b /c:"TGJU_" >nul && set "%%a"
  )
)

if "%PYTHON%"=="" set "PYTHON=python"
if "%TGJU_DB_URL%"=="" set "TGJU_DB_URL=sqlite:///tgju_collector.db"

set "PYTHONPATH=%CD%\src"

echo [%date% %time%] sync-live
"%PYTHON%" -m tgju_collector.cli sync-live --pages home
if errorlevel 1 goto :fail

echo [%date% %time%] sync-news
"%PYTHON%" -m tgju_collector.cli sync-news --count 40
if errorlevel 1 goto :fail

echo [%date% %time%] sync-history (recent window from catalog)
"%PYTHON%" -m tgju_collector.cli sync-history --from-catalog --days 5
if errorlevel 1 goto :fail

echo [%date% %time%] quality
"%PYTHON%" -m tgju_collector.cli quality

echo [%date% %time%] done
exit /b 0

:fail
echo [%date% %time%] job failed
exit /b 1
