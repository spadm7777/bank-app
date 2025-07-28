@echo off
echo 🚀 Flask Bank App - 외부 접속 모드
echo.
echo 📍 접속 주소:
echo    로컬: http://localhost:5000
echo    내부망: http://192.168.228.129:5000
echo.
echo 🌐 외부 접속 방법:
echo    1. 라우터 포트포워딩: router_setup_guide.txt 참조
echo    2. ngrok 사용: python setup_ngrok.py
echo    3. 클라우드 배포: Heroku, AWS 등
echo.
echo 🔒 보안 주의사항:
echo    - 외부 접속 시 보안에 주의하세요
echo    - 강력한 비밀번호를 사용하세요
echo    - 사용 후 서버를 종료하세요
echo.
echo ⏳ 서버 시작 중...
venv\Scripts\python.exe app.py
pause 