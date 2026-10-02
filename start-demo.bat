@echo off
REM ============================================================
REM  Runamarga Voice Agent - ONE-CLICK DEMO LAUNCHER
REM  Starts: agent worker + token server + frontend
REM  Then open:  http://localhost:3000  and click "Start conversation"
REM ============================================================
title Runamarga Demo Launcher
echo.
echo  [1/3] Starting agent worker...
cd /d "D:\Ai-Voice-Agent-Runamarga\backend"
start "voice-agent-worker" cmd /c "uv run agent.py dev > worker-test.log 2>&1"

echo  [2/3] Starting token server...
start "token-server" cmd /c "uv run python -m uvicorn token_api:app --port 8000 > token-server.log 2>&1"

echo  [3/3] Starting frontend...
cd /d "D:\Ai-Voice-Agent-Runamarga\frontend"
start "next-frontend" cmd /c "npm run dev > frontend.log 2>&1"

echo.
echo  Waiting for services to come up (about 25 seconds)...
timeout /t 25 /nobreak >nul

set READY=1
netstat -ano | findstr "LISTENING" | findstr ":3000" >nul
if errorlevel 1 (
  echo  [PROBLEM] Frontend NOT running on port 3000
  set READY=0
) else (
  echo  [OK] Frontend running on port 3000
)
netstat -ano | findstr "LISTENING" | findstr ":8000" >nul
if errorlevel 1 (
  echo  [PROBLEM] Token server NOT running on port 8000
  set READY=0
) else (
  echo  [OK] Token server running on port 8000
)
findstr /c:"registered worker" "D:\Ai-Voice-Agent-Runamarga\backend\worker-test.log" >nul
if errorlevel 1 (
  echo  [PROBLEM] Agent worker not registered with LiveKit
  set READY=0
) else (
  echo  [OK] Agent worker registered with LiveKit
)

echo.
if %READY%==1 (
  echo  ============================================
  echo   DEMO READY  --  open  http://localhost:3000
  echo   Click "Start conversation" and start talking
  echo  ============================================
  start http://localhost:3000
) else (
  echo  ============================================
  echo   NOT READY - check the three service windows
  echo  ============================================
)
echo.
pause
