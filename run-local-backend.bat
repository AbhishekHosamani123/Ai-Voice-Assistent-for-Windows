@echo off
setlocal
title Runamarga Voice Agent - Local PC Worker

echo ======================================================================
echo    Runamarga Voice Agent - Local PC Backend
echo ======================================================================
echo.
echo  This worker powers your Vercel frontend directly from your PC.
echo.
echo  Architecture:
echo    [User on Vercel] ---^> [LiveKit Cloud] ^<--- [This Local PC Worker]
echo.
echo  - No 512 MB memory limit!
echo  - No Render cold starts or sleeping!
echo  - No port forwarding or public IP needed (outbound connection).
echo.
echo ======================================================================
echo.

cd /d "%~dp0backend"

if not exist ".env" (
    if not exist ".env.local" (
        echo [WARNING] Neither .env nor .env.local found in the backend folder!
        echo Please ensure your LiveKit and Groq credentials are set up.
        echo.
    )
)

echo [*] Starting LiveKit Agent Worker...
echo [*] Waiting for registration with LiveKit Cloud...
echo.

where uv >nul 2>nul
if %errorlevel% equ 0 (
    uv run agent.py dev
) else (
    if exist ".venv\Scripts\python.exe" (
        .venv\Scripts\python.exe agent.py dev
    ) else (
        python agent.py dev
    )
)

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Agent worker exited with error code %errorlevel%.
    echo Please check the output above.
)

echo.
pause
