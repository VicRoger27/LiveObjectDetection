@echo off
setlocal enabledelayedexpansion

echo =====================================================================
echo  Building Live Object Detection & Auto-Labeling Suite Installer
echo =====================================================================
echo.

cd /d "%~dp0"

echo [1/3] Compiling multi-file application directory with PyInstaller...
python -m PyInstaller packaging/pyinstaller/specs/x-anylabeling-win-cpu.spec --clean -y
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed!
    exit /b 1
)

echo.
echo [2/3] Verifying output directory dist\LiveAnyLabeling...
if not exist "dist\LiveAnyLabeling\LiveAnyLabeling.exe" (
    echo [ERROR] LiveAnyLabeling.exe was not found in dist\LiveAnyLabeling!
    exit /b 1
)

echo.
echo [3/3] Compiling Windows NSIS Setup Wizard with makensis.exe...
where makensis.exe >nul 2>nul
if errorlevel 1 (
    if exist "C:\Users\Victor\w64\w64devkit\bin\makensis.exe" (
        set "MAKENSIS=C:\Users\Victor\w64\w64devkit\bin\makensis.exe"
    ) else (
        echo [ERROR] makensis.exe not found on PATH!
        exit /b 1
    )
) else (
    set "MAKENSIS=makensis.exe"
)

"!MAKENSIS!" packaging\installer\installer.nsi
if errorlevel 1 (
    echo [ERROR] NSIS installer compilation failed!
    exit /b 1
)

echo.
echo [4/4] Deploying executables to root directory...
copy /y dist\LiveAnyLabeling_Setup.exe .\LiveAnyLabeling_Setup.exe >nul
copy /y dist\LiveAnyLabeling\LiveAnyLabeling.exe .\LiveAnyLabeling.exe >nul
if exist dist\LiveAnyLabeling\_internal (
    robocopy dist\LiveAnyLabeling\_internal .\_internal /E /NFL /NDL /NJH /NJS /nc /ns /np >nul
)

echo.
echo =====================================================================
echo  SUCCESS! Application executables ready in root directory:
echo    - LiveAnyLabeling.exe        (Direct desktop app - instant launch)
echo    - LiveAnyLabeling_Setup.exe  (Windows Setup Wizard installer)
echo =====================================================================
echo.
pause
