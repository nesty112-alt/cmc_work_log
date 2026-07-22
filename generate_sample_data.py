import sys
import os
import glob
import random
import json

import main

base_path = main.LOCAL_BASE_PATH
if not base_path:
    print("LOCAL_BASE_PATH is empty!")
    sys.exit(1)

staff = main.STAFF_LIST
tasks = main.TASK_CATEGORIES

target_dir = os.path.join(base_path, "2026-07")
if os.path.exists(target_dir):
    for f in glob.glob(os.path.join(target_dir, "*.json")):
        try:
            os.remove(f)
        except Exception as e:
            print(f"Error removing {f}: {e}")
else:
    os.makedirs(target_dir, exist_ok=True)

print(f"Cleared existing data in {target_dir}")

for day in range(1, 23): # July 1 to 22
    date_str = f"2026-07-{day:02d}"
    file_date = date_str.replace("-", "")
    
    # Introduce dynamic variance per day
    daily_multiplier = random.choice([0, 0.5, 1, 3, 8]) 

    for user in staff:
        task_data = {}
        for cat, fields in tasks.items():
            for field in fields:
                unique_key = f"{cat}_{field}"
                # Generate a very bumpy workload
                base_val = random.randint(0, 10)
                task_data[unique_key] = int(base_val * daily_multiplier * random.choice([0, 1, 1.5]))
        
        payload = {
            "date": date_str,
            "name": user,
            "tasks": task_data,
            "other_progress": "테스트입니다.",
            "req_in_progress": "1",
            "req_out_progress": "2",
            "mail_progress": "3",
            "saved_at": "2026-07-22 13:40:00",
            "ip": "127.0.0.1",
            "history": []
        }
        
        file_path = os.path.join(target_dir, f"{file_date}_{user}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

print(f"Generated dynamic sample data for 2026-07-01 to 2026-07-22 in {target_dir}")
