@echo off
setlocal
title SPYSCALP Builder

:menu
cls
echo ========================================================
echo   SPYSCALP Nuitka Build System
echo ========================================================
echo.
echo   1. Build SPYSCALP (Standalone)
echo   2. Clean Build Artifacts
echo   3. Exit
echo.
set /p choice="Select an option (1-3): "

if "%choice%"=="1" goto build
if "%choice%"=="2" goto clean
if "%choice%"=="3" goto end

echo Invalid choice.
timeout /t 2 >nul
goto menu

:build
echo.
echo [BUILD] Starting Nuitka compilation...
echo.
:: Nuitka Command
:: --onefile: Bundles everything into a single EXE
:: --enable-console: Keeps console window (needed for TUI? Textual usually needs it or a shim. 
::                   For now keeping console to see errors.)
:: --include-package: Force inclusion of critical packages
:: --output-dir: Output to nuitka_dist
:: --force-stdout-spec: Ensure output is visible
nuitka --onefile --enable-console --include-package=textual --include-package=rich --include-package=rich._unicode_data --include-package=tastytrade --include-package=zoneinfo --include-package=pytz --include-package=tzdata --windows-icon-from-ico=spyscalp.ico --include-data-file=spyscalp.ico=spyscalp.ico --include-data-file=spyscalp_logo.png=spyscalp_logo.png --output-dir=nuitka_dist spyscalp.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed with error code %errorlevel%
    pause
    goto menu
)

echo.
echo [SUCCESS] Build complete!
echo Output: nuitka_dist\spyscalp.dist\spyscalp.exe
pause
goto menu

:clean
echo.
echo [CLEAN] Removing nuitka_dist directory...
if exist nuitka_dist (
    rmdir /s /q nuitka_dist
    echo Cleaned.
) else (
    echo Nothing to clean.
)
pause
goto menu

:end
exit /b
