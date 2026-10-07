@echo off
setlocal enabledelayedexpansion
title ComfyUI-SmartModelResolver - Comfy Registry Direct Publisher

echo =======================================================
echo    ComfyUI-SmartModelResolver - Direct Comfy Registry
echo =======================================================
echo.

:: 1. Locate comfy CLI executable
set "COMFY_CLI=comfy"
if exist "E:\ComfyUI\ComfyUI\.venv\Scripts\comfy.exe" (
    set "COMFY_CLI=E:\ComfyUI\ComfyUI\.venv\Scripts\comfy.exe"
)

:: 2. Read version from pyproject.toml
set "CURRENT_VER=1.0.0"
for /f "tokens=2 delims==" %%A in ('findstr /r "^version" pyproject.toml 2^>nul') do (
    set "RAW_VER=%%A"
    set "RAW_VER=!RAW_VER: =!"
    set "RAW_VER=!RAW_VER:"=!"
    set "CURRENT_VER=!RAW_VER!"
)
echo [INFO] Publishing version: !CURRENT_VER!
echo.

:: 3. Validate node
echo [1/2] Running node validation...
set PYTHONIOENCODING=utf-8
"!COMFY_CLI!" node validate
if %errorlevel% neq 0 (
    echo [ERROR] Validation failed. Please fix issues before publishing.
    goto :END
)
echo.

:: 4. Direct publish with token
echo [2/2] Publishing to Comfy Registry...
set "PAT_TOKEN=pat-c2c9db7f-a38c-4785-95b3-17da26e96d2a"

set /p CHANGELOG="Enter changelog (press Enter for default: 'Release v!CURRENT_VER! update'): "
if "!CHANGELOG!"=="" set "CHANGELOG=Release v!CURRENT_VER! update"

"!COMFY_CLI!" node publish --token "!PAT_TOKEN!" --changelog "!CHANGELOG!"

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Version !CURRENT_VER! successfully published to Comfy Registry!
) else (
    echo.
    echo [NOTICE] If local publish had network timeout, remember you can also push tag 'v!CURRENT_VER!'
    echo to GitHub (via upload_github.bat) which will publish via GitHub Actions automatically!
)

:END
echo.
pause
