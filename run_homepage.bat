@echo off
chcp 65001 >nul
cls
echo =======================================================
echo     PAI HUB : Global Academic Archive System (Core)
echo     [PAI AI Agent Lab 글로벌 다국어 관제탑 가동 시스템]
echo =======================================================
echo.

:: 작업 디렉토리 강제 전환 및 가상환경 가동
cd /d "%~dp0"
set VENV_ACTIVATE="D:\python_envs\pai_env\Scripts\activate.bat"
call %VENV_ACTIVATE%

:: 서버 가동 시 로컬 테스트임을 명시하기 위해 IS_SERVER 환경변수 False 설정
set IS_SERVER=False

:: 백엔드 인프라 구동엔진 비동기 기동 (8080 포트 사용)
start /b python app.py
echo 아카이브 허브 서버 예열 및 인터페이스 준비 중입니다...

:WAIT_SERVER
:: 8080 포트로 실시간 검증
curl -s http://localhost:8080 >nul
if %errorlevel% neq 0 (
    timeout /t 1 /nobreak >nul
    goto WAIT_SERVER
)

echo.
echo [완료] 서버 가동이 확인되었습니다. 글로벌 관제탑 UI를 전개합니다.
:: 서버가 개통된 즉시 8080 포트로 브라우저 전개
start "" "http://localhost:8080"

:LOOP
timeout /t 10 >nul
goto LOOP