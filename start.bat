@echo off
echo.
echo   LUO OS v1.0 — by Luo Kai
echo.
pip install flask flask-cors requests pyttsx3 SpeechRecognition -q
echo.
echo Starting LuoOS...
echo Open: http://localhost:3000
python luo_server.py
pause
