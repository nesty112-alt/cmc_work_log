@echo off
chcp 65001 >nul
title 자동 리포트 생성기
echo =======================================
echo     자동 일일 리포트 생성 스크립트
echo =======================================
echo.
echo 지정된 시간(auto_report_config.json 참고)에
echo 리포트가 자동으로 생성됩니다.
echo 이 창을 닫으면 자동 생성이 중단됩니다.
echo.

cd /d "%~dp0"

REM 가상환경이 있다면 활성화
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

python auto_report.py

pause
