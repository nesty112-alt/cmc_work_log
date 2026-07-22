import os
import json

main_file = r"d:\Users\vmfort\PycharmProjects\cmc_codi_log\main.py"
with open(main_file, "r", encoding="utf-8") as f:
    content = f.read()

# Fix window title and other missed strings
content = content.replace("IRDA log", "CODI log")
content = content.replace("재원점검 퇴원분석 업무일지", "코딩 과담당 모니터링 업무일지")
content = content.replace("재원점검 퇴원분석", "코딩 과담당 모니터링")
content = content.replace("재원점검", "모니터링")

# Fix default_staff
default_staff_str = """default_staff = [
        "고미경",
        "이용화",
        "김산들",
        "조선옥",
        "김성진",
        "박찬용",
        "강민정",
        "성수지",
        "유민지",
        "이푸른",
        "이은혜"
    ]"""

# Replace the old default_staff
import re
content = re.sub(r'default_staff\s*=\s*\[.*?\]', default_staff_str, content, count=1, flags=re.DOTALL)

# Fix default_tasks
default_tasks_str = """default_tasks = {
        "코딩": ["진코딩", "가코딩", "Cofirm", "재원코딩"],
        "미비정리": ["재원", "퇴원"],
        "DRG": ["확정", "임시", "Pathology"],
        "모니터링": ["외래", "퇴원", "응급"],
        "POA 질지표 점검": ["점검"],
        "인증서 발급": ["발급"],
        "서식": ["생성", "수정"]
    }"""
content = re.sub(r'default_tasks\s*=\s*\{.*?\}', default_tasks_str, content, count=1, flags=re.DOTALL)

with open(main_file, "w", encoding="utf-8") as f:
    f.write(content)

# Update HTML as well
html_file = r"d:\Users\vmfort\PycharmProjects\cmc_codi_log\static\report_template.html"
with open(html_file, "r", encoding="utf-8") as f:
    html_content = f.read()

html_content = html_content.replace("IRDA log", "CODI log")
html_content = html_content.replace("재원점검 퇴원분석 업무일지", "코딩 과담당 모니터링 업무일지")
html_content = html_content.replace("재원점검 퇴원분석", "코딩 과담당 모니터링")
html_content = html_content.replace("재원점검", "모니터링")

with open(html_file, "w", encoding="utf-8") as f:
    f.write(html_content)

print("Patch complete")
