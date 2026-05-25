@echo off
chcp 65001 >nul
cls
echo =======================================================
echo     PAI HUB : Global Academic Archive System (Core)
echo     [PAI AI Agent Lab 글로벌 다국어 관제탑 가동 시스템]
echo =======================================================
echo.
cd /d "%~dp0"
set VENV_ACTIVATE="D:\python_envs\pai_env\Scripts\activate.bat"
call %VENV_ACTIVATE%

:: 백엔드 인프라 구동엔진 비동기 기동
start /b python app.py
echo 아카이브 허브 서버 예열 및 인터페이스 준비 중입니다...

:WAIT_SERVER
:: 플라스크 통신 터널 개통 여부를 정밀 타격하여 실시간 검증
curl -s http://localhost:5004 >nul
if %errorlevel% neq 0 (
    timeout /t 1 /nobreak >nul
    goto WAIT_SERVER
)

echo.
echo [완료] 서버 가동이 확인되었습니다. 글로벌 관제탑 UI를 전개합니다.
:: 서버가 개통된 즉시 단 1초의 지체도 없이 브라우저 화면 전개 후 통제 루프 전환
start "" "http://localhost:5004"

:LOOP
timeout /t 10 >nul
goto LOOP