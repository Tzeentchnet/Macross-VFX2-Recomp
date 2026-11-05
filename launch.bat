@echo off
setlocal

set "launcher=%~dp0build-release\Macross_VF_X2_Recompiled.exe"
if not exist "%launcher%" (
    set "launcher=%~dp0build-setup\Macross_VF_X2_Recompiled.exe"
)

if not exist "%launcher%" (
    echo Macross VF-X2 Recompiled has not been built.
    echo Build the runtime or setup host first, then run this file again.
    echo See README.md for build instructions.
    pause
    exit /b 1
)

start "" /D "%~dp0" "%launcher%" %*
if errorlevel 1 (
    echo Failed to start Macross VF-X2 Recompiled.
    pause
    exit /b 1
)
