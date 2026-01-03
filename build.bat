@echo off
REM Build script for PyInstaller bundling (Windows)
REM Run this from the project root in PowerShell or CMD: build.bat

setlocal enabledelayedexpansion

echo === Waiter System Build Script ===
echo.

REM 1. Ensure frontend is built
if not exist "frontend" (
    echo FAILED: Frontend folder not found. Please ensure your React app is in .\frontend\
    exit /b 1
)

echo Collecting Django static files...
python manage.py collectstatic --noinput

if errorlevel 1 (
    echo ERROR: collectstatic failed
    exit /b 1
)

echo.
echo Building frontend...
cd frontend
call npm run build
if errorlevel 1 (
    echo ERROR: npm build failed
    exit /b 1
)
cd ..

echo.
echo Building .exe with PyInstaller...
pyinstaller waiter.spec

if errorlevel 1 (
    echo ERROR: PyInstaller build failed
    exit /b 1
)

echo.
echo ===== BUILD COMPLETE =====
echo Executable: dist\Restaurant\Restaurant.exe
echo.
pause
