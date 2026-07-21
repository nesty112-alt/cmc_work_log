@echo off
echo =========================================
echo Windows EXE 빌드 스크립트 시작
echo =========================================

echo [1/3] 필수 패키지 설치 중...
pip install -r requirements.txt

echo [2/3] PyInstaller로 EXE 파일 생성 중...
pyinstaller --noconfirm --onefile --windowed --icon="static\app_icon.ico" --hidden-import=xlsxwriter --hidden-import=openpyxl --name "재원점검 퇴원분석 업무일지" main.py

echo =========================================
echo 빌드 완료!
echo 생성된 파일: dist\discharge_analysis.exe
echo =========================================
pause
