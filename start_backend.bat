@echo off
echo Starting Spam Detection Backend Server...
call .\spam_env\Scripts\activate.bat
python app.py
pause
