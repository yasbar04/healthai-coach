@echo off
setlocal
call venv\Scripts\activate

echo ==========================================
echo   HealthAI BACKEND (FastAPI)
echo   URL : http://localhost:8010
echo   Docs: http://localhost:8010/docs
echo ==========================================
echo.

REM Lancement sur le port 8010 (precaution)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8010

echo.
echo Le serveur s'est arrete (ou une erreur est survenue).
pause
