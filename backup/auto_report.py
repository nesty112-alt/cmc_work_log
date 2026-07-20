import os
import json
import glob
import time
from datetime import datetime
import pandas as pd
from html_export import generate_html_report
from backup.naver_works_notifier import send_naver_works_message

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
AUTO_CONFIG_FILE = os.path.join(BASE_DIR, "auto_report_config.json")

def load_json(file_path, default_val):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    return default_val

def get_config():
    # 1. LOCAL_BASE_PATH
    main_config = load_json(MAIN_CONFIG_FILE, {})
    local_base_path = main_config.get("LOCAL_BASE_PATH", os.path.join(BASE_DIR, "업무일지_테스트"))
    
    # 2. AUTO_REPORT_TIME
    auto_config = load_json(AUTO_CONFIG_FILE, {"AUTO_REPORT_TIME": "18:00"})
    report_time = auto_config.get("AUTO_REPORT_TIME", "18:00")
    
    # 3. STAFF_LIST
    staff_master_path = os.path.join(local_base_path, "staff_master.json") if local_base_path else ""
    staff_list = load_json(staff_master_path, [
        "이지연", "신준호", "박선우", "박유진", "박연정",
        "이재희", "김정현", "이윤혜", "박민영"
    ])
    
    # 4. TASK_CATEGORIES
    task_master_path = os.path.join(local_base_path, "task_master.json") if local_base_path else ""
    task_categories = load_json(task_master_path, {
        "퇴원": ["퇴원분석", "pathology 확인", "미비정리"],
        "재원": ["특수서식", "경과기록", "미비정리"],
        "차트검수": ["차트검수"],
        "모니터링": ["외래", "응급", "입원"],
        "코딩": ["진코딩", "가코딩"]
    })
    
    # 5. Naver Works Config
    nw_api_url = main_config.get("NAVER_WORKS_API_URL", "")
    nw_bot_id = main_config.get("NAVER_WORKS_BOT_ID", "")
    nw_secret_key = main_config.get("NAVER_WORKS_SECRET_KEY", "")
    nw_target_email = main_config.get("NAVER_WORKS_TARGET_EMAIL", "")
    
    return local_base_path, report_time, staff_list, task_categories, nw_api_url, nw_bot_id, nw_secret_key, nw_target_email

def generate_daily_report():
    local_base_path, _, staff_list, task_categories, nw_api_url, nw_bot_id, nw_secret_key, nw_target_email = get_config()
    
    now = datetime.now()
    date_input = now.strftime("%Y-%m-%d")
    folder_month = now.strftime("%Y-%m")
    file_date = now.strftime("%Y%m%d")
    
    target_dir = os.path.join(local_base_path, folder_month)
    file_pattern = os.path.join(target_dir, "*.json")
    json_files = glob.glob(file_pattern)

    if not json_files:
        print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 해당 월({folder_month})에 저장된 데이터가 없습니다.")
        return

    all_rows = []
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                row = {"일자": data.get("date", ""), "담당자": data.get("name", ""), "other_progress": data.get("other_progress", "")}
                
                tasks = data.get("tasks", {})
                migrated_tasks = {}
                for category, fields in task_categories.items():
                    for field in fields:
                        unique_key = f"{category}_{field}"
                        migrated_tasks[unique_key] = tasks.get(unique_key, tasks.get(field, 0))
                row.update(migrated_tasks)
                
                all_rows.append(row)
        except Exception as e:
            print(f"파일 로드 실패 ({file_path}): {e}")

    if not all_rows:
        print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 유효한 데이터가 없어 리포트를 생성할 수 없습니다.")
        return

    df_all = pd.DataFrame(all_rows)

    # 라이브 마스터 리스트와 실제 데이터 사용자 통합 및 정렬
    all_unique_users = df_all["담당자"].unique().tolist()
    ordered_users = staff_list + [u for u in all_unique_users if u not in staff_list]

    # 1. 데일리 취합 요약 (오늘 날짜 기준)
    df_daily = df_all[df_all["일자"] == date_input].copy()
    if df_daily.empty:
        print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 당일({date_input}) 작성된 업무일지 데이터가 없습니다.")
        return
        
    df_daily.set_index("담당자", inplace=True)
    df_daily = df_daily.reindex(ordered_users)
    df_daily.index.name = "담당자"
    df_daily.reset_index(inplace=True)
    df_daily.fillna(0, inplace=True)

    # 2. 월간 취합 요약 (해당 월 전체)
    if "일자" in df_all.columns:
        df_monthly_base = df_all.drop(columns=["일자"])
    else:
        df_monthly_base = df_all
        
    # 3. HTML 생성용 딕셔너리 준비
    daily_dict = df_daily.set_index("담당자").to_dict('index')
    monthly_dict = df_monthly_base.groupby("담당자").sum(numeric_only=True).to_dict('index')

    # 4. 공통 메모 로드
    memo_path = os.path.join(target_dir, f"{file_date}_memo.txt")
    memo_content = ""
    if os.path.exists(memo_path):
        try:
            with open(memo_path, 'r', encoding='utf-8') as f:
                memo_content = f.read()
        except:
            pass

    out_file, err = generate_html_report(date_input, target_dir, daily_dict, monthly_dict, memo_content, ordered_users, task_categories)
    if out_file:
        print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 자동 리포트 생성 완료: {out_file}")
        
        # 네이버웍스 발송 (API URL이 있을 경우)
        if nw_api_url and nw_bot_id and nw_secret_key and nw_target_email:
            send_naver_works_message(
                api_base_url=nw_api_url,
                secret_key=nw_secret_key,
                bot_id=nw_bot_id,
                target_email=nw_target_email,
                report_path=out_file
            )
    else:
        print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] HTML 리포트 생성 실패: {err}")

def run_scheduler():
    print("=== 일일 자동 리포트 생성기 실행 중 ===")
    _, report_time, _, _, _, _, _, _ = get_config()
    print(f"초기 설정된 실행 시간: {report_time}")
    print("설정 파일(auto_report_config.json)을 수정하면 즉시 적용됩니다.")
    print("종료하려면 Ctrl+C를 누르세요.\n")

    while True:
        try:
            _, report_time, _, _, _, _, _, _ = get_config()
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            
            if current_time == report_time:
                generate_daily_report()
                # 중복 실행을 막기 위해 해당 분(minute)이 지나갈 때까지 대기
                time.sleep(60)
            
            # 매 10초마다 시간을 체크 (config 변경사항 반영 위해 자주 체크)
            time.sleep(10)
        except KeyboardInterrupt:
            print("\n자동 리포트 생성기를 종료합니다.")
            break
        except Exception as e:
            print(f"스케줄러 에러 발생: {e}")
            time.sleep(10)

if __name__ == "__main__":
    run_scheduler()
