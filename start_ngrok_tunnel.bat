@echo off
echo 🌐 ngrok 터널 시작
echo.
echo 📍 외부 접속 URL이 생성됩니다.
echo ⏹️ Ctrl+C로 중지
echo.
echo ⏳ ngrok 터널 시작 중...
ngrok.exe http 5000
pause 