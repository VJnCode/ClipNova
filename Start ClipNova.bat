@echo off
title ClipNova (keep this window open while you use it)
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

rem First time on this PC: install everything by itself, then carry on and start.
if not exist ".venv\Scripts\python.exe" (
  echo ClipNova isn't installed on this PC yet: setting it up first ^(a few minutes, only once^)...
  call "%~dp0setup.bat" auto
  if not exist ".venv\Scripts\python.exe" (
    echo Setup didn't finish. Fix the problem above, then double-click Start ClipNova.bat again.
    pause & exit /b 1
  )
  title ClipNova ^(keep this window open while you use it^)
)

rem The port comes from .env (8766 by default)
set "PORT=8766"
if exist ".env" for /f "tokens=2 delims==" %%P in ('findstr /b /c:"PEAKCUT_PORT=" ".env"') do set "PORT=%%P"

rem ffmpeg from WinGet is not always on PATH in an older window: add it.
for /d %%D in ("%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*") do (
  for /r "%%D" %%F in (ffmpeg.exe) do if exist "%%F" set "PATH=%%~dpF;%PATH%"
)

rem Already running? Just open it.
powershell -NoProfile -Command "try { Invoke-WebRequest -UseBasicParsing -TimeoutSec 3 http://127.0.0.1:%PORT%/api/status | Out-Null; exit 0 } catch { exit 1 }"
if %errorlevel%==0 (
  echo ClipNova is already running. Opening it...
  start "" http://127.0.0.1:%PORT%/app
  timeout /t 3 >nul
  exit /b
)

echo Starting ClipNova on http://127.0.0.1:%PORT%/app ... the browser opens by itself in a few seconds.
start "" /min powershell -NoProfile -Command "Start-Sleep 6; Start-Process 'http://127.0.0.1:%PORT%/app'"
".venv\Scripts\python.exe" -m studio.server
echo.
echo ClipNova stopped.
pause
