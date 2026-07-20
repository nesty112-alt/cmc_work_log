#!/bin/bash
# MacOS / Linux 용 자동 리포트 실행 스크립트

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# 가상환경이 있다면 활성화
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "백그라운드에서 자동 리포트 생성기를 시작합니다..."
echo "종료하려면 'kill $(pgrep -f auto_report.py)' 명령어를 사용하거나, 아래 백그라운드 프로세스를 종료하세요."

# 백그라운드 실행 후 로그 파일에 출력 저장
nohup python3 auto_report.py > auto_report.log 2>&1 &

echo "실행 완료! (로그 확인: tail -f auto_report.log)"
