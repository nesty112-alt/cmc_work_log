import os
import json
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import auto_report

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
AUTO_CONFIG_FILE = os.path.join(BASE_DIR, "auto_report_config.json")

def load_json(file_path, default_val):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return default_val

def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

class AutoReportUI:
    def __init__(self, root):
        self.root = root
        self.root.title("자동 발송 제어 패널")
        self.root.geometry("600x550")
        self.scheduler_process = None

        self.main_config = load_json(MAIN_CONFIG_FILE, {})
        self.auto_config = load_json(AUTO_CONFIG_FILE, {"AUTO_REPORT_TIME": "18:00"})

        self.create_widgets()

    def create_widgets(self):
        # 타이틀
        title_lbl = tk.Label(self.root, text="자동 발송 및 네이버웍스 봇 설정", font=("Arial", 16, "bold"))
        title_lbl.pack(pady=15)

        # 설정 프레임
        config_frame = tk.LabelFrame(self.root, text="설정 정보", padx=15, pady=15)
        config_frame.pack(fill="x", padx=20, pady=10)

        # 1. 예약 발송 시간
        time_frame = tk.Frame(config_frame)
        time_frame.pack(fill="x", pady=5)
        tk.Label(time_frame, text="자동 발송 시간 (HH:MM) :", width=25, anchor="w").pack(side="left")
        self.time_var = tk.StringVar(value=self.auto_config.get("AUTO_REPORT_TIME", "18:00"))
        tk.Entry(time_frame, textvariable=self.time_var, width=15).pack(side="left")

        # 2. Naver Works 설정들
        tk.Label(config_frame, text="[네이버웍스 봇 설정]", font=("Arial", 10, "bold")).pack(anchor="w", pady=(15, 5))

        self.nw_vars = {}
        fields = [
            ("NAVER_WORKS_API_URL", "API 주소 (URL)"),
            ("NAVER_WORKS_BOT_ID", "Bot ID"),
            ("NAVER_WORKS_SECRET_KEY", "Secret Key"),
            ("NAVER_WORKS_TARGET_EMAIL", "수신자 이메일")
        ]

        for key, label_text in fields:
            row = tk.Frame(config_frame)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=label_text + " :", width=25, anchor="w").pack(side="left")
            var = tk.StringVar(value=self.main_config.get(key, ""))
            self.nw_vars[key] = var
            tk.Entry(row, textvariable=var, width=40).pack(side="left")

        # 저장 버튼
        tk.Button(config_frame, text="설정 저장", command=self.save_settings, width=15, fg="black").pack(pady=10)

        # 액션 프레임 (즉시 발송 / 스케줄러)
        action_frame = tk.LabelFrame(self.root, text="제어 액션", padx=15, pady=15)
        action_frame.pack(fill="x", padx=20, pady=10)

        # 즉시 발송 버튼
        send_now_btn = tk.Button(action_frame, text="🚀 즉시 발송하기", command=self.send_immediately, 
                                 font=("Arial", 12, "bold"), height=2, fg="black")
        send_now_btn.pack(fill="x", pady=5)
        tk.Label(action_frame, text="* 현재까지 취합된 업무일지를 즉시 HTML로 만들고 발송합니다.", fg="gray", font=("Arial", 9)).pack()

        # 스케줄러 제어 프레임
        sched_frame = tk.Frame(action_frame)
        sched_frame.pack(fill="x", pady=(15, 5))

        self.status_lbl = tk.Label(sched_frame, text="현재 상태: 스케줄러 정지됨", fg="red", font=("Arial", 11, "bold"))
        self.status_lbl.pack(side="left", padx=10)

        self.toggle_btn = tk.Button(sched_frame, text="스케줄러 시작", command=self.toggle_scheduler, width=15, fg="black")
        self.toggle_btn.pack(side="right", padx=10)

    def save_settings(self):
        # Auto Time 저장
        self.auto_config["AUTO_REPORT_TIME"] = self.time_var.get().strip()
        save_json(AUTO_CONFIG_FILE, self.auto_config)

        # Naver Works 설정 저장
        for key, var in self.nw_vars.items():
            self.main_config[key] = var.get().strip()
        
        # main_config 에 LOCAL_BASE_PATH 가 없으면 덮어쓰지 않도록 기존 데이터 다시 로드 후 병합
        existing_main = load_json(MAIN_CONFIG_FILE, {})
        existing_main.update(self.main_config)
        save_json(MAIN_CONFIG_FILE, existing_main)

        messagebox.showinfo("저장 완료", "설정이 성공적으로 저장되었습니다.")

    def send_immediately(self):
        answer = messagebox.askyesno("즉시 발송", "현재 시간 기준으로 즉시 리포트를 생성하고 발송하시겠습니까?")
        if not answer:
            return
            
        try:
            # 설정 갱신을 위해 저장 진행
            self.save_settings()
            
            # auto_report.py 의 함수 직접 호출
            auto_report.generate_daily_report()
            messagebox.showinfo("완료", "즉시 발송 루틴이 실행되었습니다.\n콘솔 로그를 확인해주세요.")
        except Exception as e:
            messagebox.showerror("오류", f"즉시 발송 중 오류가 발생했습니다: {e}")

    def toggle_scheduler(self):
        if self.scheduler_process is None:
            # 시작
            try:
                # subprocess로 실행
                script_path = os.path.join(BASE_DIR, "auto_report.py")
                # 파이썬 실행 경로 (가상환경 고려)
                import sys
                self.scheduler_process = subprocess.Popen([sys.executable, script_path])
                
                self.status_lbl.config(text="현재 상태: 스케줄러 실행 중", fg="green")
                self.toggle_btn.config(text="스케줄러 중지")
            except Exception as e:
                messagebox.showerror("오류", f"스케줄러를 시작할 수 없습니다: {e}")
        else:
            # 중지
            try:
                self.scheduler_process.terminate()
                self.scheduler_process.wait(timeout=3)
            except:
                self.scheduler_process.kill()
            finally:
                self.scheduler_process = None
                self.status_lbl.config(text="현재 상태: 스케줄러 정지됨", fg="red")
                self.toggle_btn.config(text="스케줄러 시작")

    def on_closing(self):
        if self.scheduler_process is not None:
            if messagebox.askokcancel("종료", "스케줄러가 실행 중입니다. 프로그램을 종료하면 스케줄러도 종료됩니다.\n종료하시겠습니까?"):
                self.toggle_scheduler()
                self.root.destroy()
        else:
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoReportUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
