@echo off
REM HealthAI backend - installation Windows
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt
echo.
echo OK - Lance ensuite: run.bat
pause
