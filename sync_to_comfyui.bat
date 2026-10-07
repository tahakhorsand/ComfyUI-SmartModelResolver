@echo off
setlocal enabledelayedexpansion
title ComfyUI-SmartModelResolver - Sync to Local ComfyUI

echo =======================================================
echo    ComfyUI-SmartModelResolver - Local Sync Tool
echo =======================================================
echo.

:: 1. Locate Python executable (prefer ComfyUI venv)
set "PYTHON_EXE=python"
if exist "E:\ComfyUI\ComfyUI\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=E:\ComfyUI\ComfyUI\.venv\Scripts\python.exe"
) else if exist "..\ComfyUI\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=..\ComfyUI\.venv\Scripts\python.exe"
)

:: 2. Syntax check before sync
echo [1/3] Verifying Python syntax...
"!PYTHON_EXE!" -m py_compile __init__.py nodes\smart_nodes.py core\model_indexer.py
if %errorlevel% neq 0 (
    echo [ERROR] Python syntax error detected! Fix errors before syncing.
    goto :END
)
echo [OK] Syntax check passed.
echo.

:: 3. Determine target ComfyUI custom_nodes path
echo [2/3] Locating local ComfyUI custom_nodes folder...

set "TARGET_NODES="

:: Check direct known path E:\ComfyUI\ComfyUI\custom_nodes
if exist "E:\ComfyUI\ComfyUI\custom_nodes" (
    set "TARGET_NODES=E:\ComfyUI\ComfyUI\custom_nodes"
)

:: Check relative path (..\..\ComfyUI\custom_nodes or ..\custom_nodes)
if "!TARGET_NODES!"=="" (
    if exist "..\..\ComfyUI\custom_nodes" (
        pushd "..\..\ComfyUI\custom_nodes"
        set "TARGET_NODES=!CD!"
        popd
    )
)
if "!TARGET_NODES!"=="" (
    if exist "..\custom_nodes" (
        pushd "..\custom_nodes"
        set "TARGET_NODES=!CD!"
        popd
    )
)

:: If not found automatically, prompt user
if "!TARGET_NODES!"=="" (
    echo [NOTICE] Could not automatically find ComfyUI custom_nodes folder.
    set /p TARGET_NODES="Please enter full path to ComfyUI custom_nodes folder: "
)

if not exist "!TARGET_NODES!" (
    echo [ERROR] Target folder does not exist: "!TARGET_NODES!"
    goto :END
)

set "DEST_DIR=!TARGET_NODES!\ComfyUI-SmartModelResolver"
echo Target path: "!DEST_DIR!"
echo.

:: 4. Copy files to destination
echo [3/3] Copying files to ComfyUI custom_nodes...
if not exist "!DEST_DIR!" mkdir "!DEST_DIR!"

robocopy "%CD%" "!DEST_DIR!" /E /XF *.bat *.git* *.log /XD .git __pycache__ .venv .idea .vscode /R:1 /W:1 >nul 2>nul
set ROBO_EXIT=%errorlevel%

:: Robocopy exit codes 0-7 indicate success
if %ROBO_EXIT% leq 7 (
    echo.
    echo =======================================================
    echo [SUCCESS] ComfyUI-SmartModelResolver synced successfully!
    echo Destination: !DEST_DIR!
    echo.
    echo You can now refresh your browser or restart ComfyUI.
    echo =======================================================
) else (
    echo [ERROR] Failed to copy files. Robocopy error code: %ROBO_EXIT%
)

:END
echo.
pause
