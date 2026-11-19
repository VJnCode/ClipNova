@echo off
title ClipNova - one-time setup
setlocal
cd /d "%~dp0"
echo.
echo  ClipNova one-time setup
echo  =======================
echo.

rem 1. Python
where py >nul 2>&1 && (set "PY=py -3") || (set "PY=python")
%PY% -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 (
  echo  [X] Python 3.10 or newer was not found.
  echo      Install it from https://www.python.org/downloads/  and tick "Add Python to PATH",
  echo      or run:  winget install Python.Python.3.12
  echo      Then run setup.bat again.
  pause & exit /b 1
)
for /f "delims=" %%V in ('%PY% -c "import sys; print(sys.version.split()[0])"') do echo  [ok] Python %%V

rem 2. ffmpeg
where ffmpeg >nul 2>&1
if errorlevel 1 (
  set "FOUND="
  for /d %%D in ("%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*") do set "FOUND=1"
  if not defined FOUND (
    echo  [..] ffmpeg is missing: installing it with winget...
    winget install -e --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements
  )
)
echo  [ok] ffmpeg

rem 3. The app's own Python environment and packages
if not exist ".venv\Scripts\python.exe" (
  echo  [..] Making the Python environment ^(.venv^)...
  %PY% -m venv .venv || (echo  [X] Could not make .venv & pause & exit /b 1)
)
echo  [..] Installing packages (a few minutes the first time)...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
".venv\Scripts\python.exe" -m pip install -r requirements.txt || (echo  [X] Installing packages failed. & pause & exit /b 1)
echo  [ok] Packages installed

rem 4. Settings file: ClipNova runs on port 8766
if not exist ".env" (
  > ".env" echo # ClipNova settings. Port 8766: Google's redirect URI must use the same port.
  >> ".env" echo PEAKCUT_PORT=8766
  echo  [ok] Made .env ^(port 8766^)
) else (
  echo  [ok] .env already there, left as it is
)

echo.
echo  Setup done. Start ClipNova by double-clicking "Start ClipNova.bat", then follow SETUP.md (AI key, Google, YouTube).
echo.
rem Called from Start ClipNova.bat ("auto"): no pause, it starts the app next.
if /i not "%~1"=="auto" pause
exit /b 0
