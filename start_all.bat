@echo off
setlocal
echo ==========================================
echo   HealthAI Coach - Lancement complet
echo ==========================================
echo.
echo BACKEND : http://localhost:8010 (Swagger: /docs)
echo FRONT   : http://localhost:5173
echo.

REM --- BACKEND ---
start "HealthAI BACKEND" cmd /k "cd /d %~dp0backend\healthai-backend && if exist setup_windows.bat (echo [BACKEND] Si premiere fois, lance setup_windows.bat) && call run_windows.bat"

REM --- FRONT ---
start "HealthAI FRONT" cmd /k "cd /d %~dp0front\healthai-front && if not exist node_modules (echo [FRONT] Installation npm... && npm install) else (echo [FRONT] node_modules OK) && npm run dev"

echo.
echo Ouvre ensuite:
echo - Swagger : http://localhost:8010/docs
echo - Front   : http://localhost:5173
echo.
pause
