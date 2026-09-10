@echo off
REM Weekly history backfill (trowel). Schedule mid-week, off-peak.
REM
REM   schtasks /Create /TN "TGJU-Weekly" /SC WEEKLY /D SUN /ST 22:30 /TR "\"%~dp0weekly_job.bat\""

setlocal
cd /d "%~dp0.."

if exist .env (
  for /f "usebackq delims=" %%a in (".env") do (
    echo %%a | findstr /b /c:"TGJU_" >nul && set "%%a"
  )
)

if "%PYTHON%"=="" set "PYTHON=python"
if "%TGJU_DB_URL%"=="" set "TGJU_DB_URL=sqlite:///tgju_collector.db"
if "%TGJU_TROWEL_MAX_DAYS%"=="" set "TGJU_TROWEL_MAX_DAYS=365"

set "PYTHONPATH=%CD%\src"

echo [%date% %time%] refresh catalog
"%PYTHON%" -m tgju_collector.cli sync-catalog
if errorlevel 1 goto :fail

echo [%date% %time%] trowel backfill (%TGJU_TROWEL_MAX_DAYS% days)
"%PYTHON%" -m tgju_collector.cli trowel --max-days %TGJU_TROWEL_MAX_DAYS%
if errorlevel 1 goto :fail

echo [%date% %time%] quality
"%PYTHON%" -m tgju_collector.cli quality

echo [%date% %time%] weekly done
exit /b 0

:fail
echo [%date% %time%] weekly job failed
exit /b 1
