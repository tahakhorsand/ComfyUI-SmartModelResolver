@echo off
setlocal enabledelayedexpansion
title ComfyUI-SmartModelResolver - Git ^& Comfy Registry Publisher

echo =======================================================
echo    ComfyUI-SmartModelResolver - GitHub ^& Registry Sync
echo =======================================================
echo.

:: 1. Verify Git installation
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Git is not installed or not in your system PATH.
    echo Please install Git from https://git-scm.com/
    goto :END
)

:: 2. Locate Python executable (prefer ComfyUI venv)
set "PYTHON_EXE=python"
if exist "E:\ComfyUI\ComfyUI\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=E:\ComfyUI\ComfyUI\.venv\Scripts\python.exe"
) else if exist "..\ComfyUI\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=..\ComfyUI\.venv\Scripts\python.exe"
)

:: 3. Read current version from pyproject.toml
set "CURRENT_VER=1.0.0"
for /f "tokens=2 delims==" %%A in ('findstr /r "^version" pyproject.toml 2^>nul') do (
    set "RAW_VER=%%A"
    set "RAW_VER=!RAW_VER: =!"
    set "RAW_VER=!RAW_VER:"=!"
    set "CURRENT_VER=!RAW_VER!"
)
echo [INFO] Detected project version: !CURRENT_VER!
echo.

:: 4. Check remote origin
git remote get-url origin >nul 2>nul
if %errorlevel% neq 0 (
    echo [NOTICE] Remote 'origin' is not configured yet.
    set /p REPO_URL="Enter your GitHub repository URL: "
    if "!REPO_URL!"=="" (
        echo [WARNING] No repository URL provided. Skipping remote setup.
    ) else (
        git remote add origin !REPO_URL!
        echo [SUCCESS] Added remote origin: !REPO_URL!
    )
    echo.
)

:: 5. Python syntax & test check
echo [1/4] Checking Python syntax and test suite...
"!PYTHON_EXE!" -m py_compile __init__.py nodes\smart_nodes.py core\model_indexer.py
if %errorlevel% neq 0 (
    echo [ERROR] Python syntax check failed! Please fix errors before pushing.
    goto :END
)
if exist "tests\test_resolver.py" (
    "!PYTHON_EXE!" tests\test_resolver.py >nul 2>nul
    if %errorlevel% neq 0 (
        echo [WARNING] Unit tests failed! Proceed with caution.
    ) else (
        echo [OK] All unit tests passed cleanly.
    )
)
echo [OK] Syntax check passed.
echo.

:: 6. Stage files
echo [2/4] Staging files...
git add -A
git status --short
echo.

:: 7. Commit
set "DEFAULT_MSG=Release v!CURRENT_VER!: update and optimizations"
set /p COMMIT_MSG="[3/4] Enter commit message (press Enter for default: '!DEFAULT_MSG!'): "
if "!COMMIT_MSG!"=="" set "COMMIT_MSG=!DEFAULT_MSG!"

git commit -m "!COMMIT_MSG!"
if %errorlevel% neq 0 (
    echo [INFO] No new changes to commit or working tree clean.
)
echo.

:: 8. Push to GitHub
echo [4/4] Push to GitHub
set /p DO_PUSH="Do you want to push commits to GitHub now? (Y/N, default Y): "
if "!DO_PUSH!"=="" set "DO_PUSH=Y"
if /i "!DO_PUSH!"=="Y" (
    echo Pushing to origin main...
    git push -u origin main
    if %errorlevel% equ 0 (
        echo [SUCCESS] Successfully pushed to GitHub!
        echo.
        
        :: 9. Push version tag to trigger automated Comfy Registry deployment
        set "TAG_NAME=v!CURRENT_VER!"
        set /p DO_TAG="Push tag !TAG_NAME! to trigger Comfy Registry auto-publish via GitHub Actions? (Y/N, default Y): "
        if "!DO_TAG!"=="" set "DO_TAG=Y"
        if /i "!DO_TAG!"=="Y" (
            echo Creating and pushing tag !TAG_NAME!...
            git tag -a "!TAG_NAME!" -m "Release !TAG_NAME!" 2>nul
            git push origin "!TAG_NAME!"
            if %errorlevel% equ 0 (
                echo [SUCCESS] Tag !TAG_NAME! pushed! GitHub Actions is now publishing to Comfy Registry.
                echo Check progress: https://github.com/tahakhorsand/ComfyUI-SmartModelResolver/actions
            ) else (
                echo [NOTICE] Tag might already exist on remote.
            )
        )
    ) else (
        echo.
        echo [WARNING] Git push failed. Please check your GitHub remote URL and credentials.
    )
) else (
    echo [INFO] Push skipped by user.
)

:END
echo.
echo =======================================================
pause
