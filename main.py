import sys
import os
import json
import glob
import time
from datetime import datetime
import socket
import pandas as pd

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QTextEdit, QComboBox, QPushButton,
    QGroupBox, QTreeWidget, QTreeWidgetItem, QDialog,
    QMessageBox, QScrollArea, QFrame, QGridLayout, QDateEdit, QTabWidget, QListWidget,
    QHeaderView
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QAction, QIcon

# --- HTML Export Code ---
import webbrowser
import urllib.request
import urllib.parse
import base64

QUICKCHART_OFFLINE = False

def get_quickchart_b64(chart_config, width=700, height=300):
    global QUICKCHART_OFFLINE
    if QUICKCHART_OFFLINE:
        return ""
        
    url = "https://quickchart.io/chart"
    payload = {
        "backgroundColor": "white",
        "width": width,
        "height": height,
        "format": "png",
        "version": "3",
        "chart": chart_config
    }
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=10.0) as response:
            image_data = response.read()
            b64 = base64.b64encode(image_data).decode('utf-8')
            return f"data:image/png;base64,{b64}"
    except Exception as e:
        print("QuickChart fallback error:", e)
        QUICKCHART_OFFLINE = True
        return ""

COLOR_PALETTE = [
    '#9B81DD', # ?곕낫??
    '#4EBC9D', # 泥?��
    '#3984C6', # ?����
    '#F2A154', # 二쇳��
    '#E76F51', # 鍮④��
    '#2A9D8F', # 吏����??
    '#E9C46A', # ?몃��
    '#6D6875', # ?����
    '#B5838D', # ?����遺����
    '#E5989B', # ?����
    '#FFB4A2', # ?닿뎄
    '#84A59D', # ?�硫�?����
    '#F6BD60', # ?����
    '#F28482', # 濡�利�
]

def generate_html_report(date_input, target_dir, daily_dict, monthly_dict, memo_content, staff_list, task_categories, is_preview=False, df_monthly_base=None):
    # (Copied from original)
    try:
        date_obj = datetime.strptime(date_input, "%Y-%m-%d")
        weekdays = ["?����??, "?����??, "?����??, "紐⑹��??, "湲����??, "?����??, "?쇱��??]
        day_str = weekdays[date_obj.weekday()]
        report_date_str = f"{date_obj.year}??{date_obj.month}??{date_obj.day}??({day_str})"
        file_date = date_obj.strftime("%Y%m%d")
    except:
        report_date_str = date_input
        file_date = date_input.replace("-", "")

    all_tasks = []
    task_colors = {}
    color_idx = 0
    for cat, tasks in task_categories.items():
        for t in tasks:
            unique_key = f"{cat}_{t}"
            all_tasks.append((unique_key, t, cat))
            task_colors[unique_key] = COLOR_PALETTE[color_idx % len(COLOR_PALETTE)]
            color_idx += 1

    daily_datasets = []
    for unique_key, t, cat in all_tasks:
        data_arr = []
        for staff in staff_list:
            val = daily_dict.get(staff, {}).get(unique_key, daily_dict.get(staff, {}).get(t, 0))
            data_arr.append(val if val else 0)
        
        if any(data_arr):
            daily_datasets.append({
                "label": f"[{cat}] {t}",
                "data": data_arr,
                "backgroundColor": task_colors[unique_key]
            })

    monthly_datasets = []
    for unique_key, t, cat in all_tasks:
        data_arr = []
        for staff in staff_list:
            val = monthly_dict.get(staff, {}).get(unique_key, monthly_dict.get(staff, {}).get(t, 0))
            data_arr.append(val if val else 0)
            
        if any(data_arr):
            monthly_datasets.append({
                "label": f"[{cat}] {t}",
                "data": data_arr,
                "backgroundColor": task_colors[unique_key]
            })

    task_labels = []
    task_daily_totals = []
    task_monthly_totals = []
    task_bar_colors = []
    for unique_key, t, cat in all_tasks:
        d_total = 0
        m_total = 0
        for staff in staff_list:
            v_d = daily_dict.get(staff, {}).get(unique_key, daily_dict.get(staff, {}).get(t, 0))
            if v_d: d_total += int(float(v_d))
            v_m = monthly_dict.get(staff, {}).get(unique_key, monthly_dict.get(staff, {}).get(t, 0))
            if v_m: m_total += int(float(v_m))
        
        if d_total > 0 or m_total > 0:
            task_labels.append(t)
            task_daily_totals.append(d_total)
            task_monthly_totals.append(m_total)
            task_bar_colors.append(task_colors[unique_key])

    task_daily_datasets = [{"label": "?쇱�� ?⑷��", "data": task_daily_totals, "backgroundColor": task_bar_colors}]
    task_monthly_datasets = [{"label": "?���� ?⑷��", "data": task_monthly_totals, "backgroundColor": task_bar_colors}]

    qc_daily_config = {
        "type": "bar",
        "data": { "labels": staff_list, "datasets": daily_datasets },
        "options": {
            "plugins": { "legend": { "display": False }, "datalabels": { "color": "white", "font": { "weight": "bold", "size": 16 } } },
            "scales": { "x": { "stacked": True, "ticks": { "font": { "size": 15 } } }, "y": { "stacked": True, "ticks": { "font": { "size": 15 } } } }
        }
    }
    daily_b64 = get_quickchart_b64(qc_daily_config)

    qc_monthly_config = {
        "type": "bar",
        "data": { "labels": staff_list, "datasets": monthly_datasets },
        "options": {
            "plugins": { "legend": { "display": False }, "datalabels": { "color": "white", "font": { "weight": "bold", "size": 16 } } },
            "scales": { "x": { "stacked": True, "ticks": { "font": { "size": 15 } } }, "y": { "stacked": True, "ticks": { "font": { "size": 15 } } } }
        }
    }
    monthly_b64 = get_quickchart_b64(qc_monthly_config)

    qc_task_daily_config = {
        "type": "bar",
        "data": { "labels": task_labels, "datasets": task_daily_datasets },
        "options": {
            "plugins": { "legend": { "display": False }, "datalabels": { "color": "#4b5563", "anchor": "end", "align": "top", "font": { "weight": "bold", "size": 22 } } },
            "scales": { "x": { "ticks": { "font": { "size": 16 } } }, "y": { "beginAtZero": True, "ticks": { "font": { "size": 16 } } } }, "layout": { "padding": { "top": 30 } }
        }
    }
    task_daily_b64 = get_quickchart_b64(qc_task_daily_config, height=500)

    qc_task_monthly_config = {
        "type": "bar",
        "data": { "labels": task_labels, "datasets": task_monthly_datasets },
        "options": {
            "plugins": { "legend": { "display": False }, "datalabels": { "color": "#4b5563", "anchor": "end", "align": "top", "font": { "weight": "bold", "size": 22 } } },
            "scales": { "x": { "ticks": { "font": { "size": 16 } } }, "y": { "beginAtZero": True, "ticks": { "font": { "size": 16 } } } }, "layout": { "padding": { "top": 30 } }
        }
    }

    task_monthly_b64 = get_quickchart_b64(qc_task_monthly_config, height=500)

    # ------------------ ?���� 異���� ?곗��???���� ------------------
    trend_b64 = ""
    trend_chart_json_str = "{}"
    if df_monthly_base is not None and not df_monthly_base.empty:
        import pandas as pd
        task_cols = [c for c in df_monthly_base.columns if c not in ['?쇱��', '?대��??, 'other_progress', 'req_in_progress', 'req_out_progress', 'mail_progress']]
        df_trend = df_monthly_base[['?쇱��'] + task_cols].copy()
        
        df_trend[task_cols] = df_trend[task_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
        df_trend_daily = df_trend.groupby('?쇱��')[task_cols].sum()
        
        dates = df_trend_daily.index.tolist()
        daily_totals = df_trend_daily.sum(axis=1).tolist()
        cum_totals = pd.Series(daily_totals).cumsum().tolist()
        
        datasets = []
        
        max_daily_sum = int(max(daily_totals)) if daily_totals else 0
        y_max = max_daily_sum * 2 if max_daily_sum > 0 else 10
        
        max_cum = int(max(cum_totals)) if cum_totals else 10
        y1_max = int(max_cum * 1.1)
        if y1_max < 10: y1_max = 10
        
        for task_key in task_cols:
            daily_vals = df_trend_daily[task_key].tolist()
            if sum(daily_vals) > 0:
                color = task_colors.get(task_key, "#cccccc")
                datasets.append({
                    "label": f"{task_key}",
                    "data": daily_vals,
                    "backgroundColor": color,
                    "type": "bar",
                    "stack": "Stack 0",
                    "yAxisID": "y",
                    "datalabels": { "display": False }
                })
                
        datasets.append({
            "label": "?쇱�� ?�臾�??,
            "data": daily_totals,
            "type": "line",
            "borderColor": "transparent",
            "backgroundColor": "transparent",
            "pointRadius": 0,
            "pointHoverRadius": 0,
            "yAxisID": "y",
            "datalabels": {
                "display": True,
                "align": "top",
                "anchor": "end",
                "color": "#3B82F6",
                "font": { "weight": "bold", "size": 8 }
            }
        })
        
        datasets.append({
            "label": "?���� ?�臾�??,
            "data": cum_totals,
            "borderColor": "#10B981",
            "backgroundColor": "transparent",
            "type": "line",
            "yAxisID": "y1",
            "tension": 0.1,
            "datalabels": {
                "display": True,
                "align": "top",
                "color": "#10B981",
                "font": { "weight": "bold", "size": 8 }
            }
        })

        qc_trend_config = {
            "type": "line",
            "data": {
                "labels": dates,
                "datasets": datasets
            },
            "options": {
                "plugins": { "legend": { "display": False } },
                "scales": { 
                    "x": { "grid": { "display": False }, "stacked": True, "ticks": { "font": { "size": 10 } } },
                    "y": { 
                        "type": "linear", "display": True, "position": "left", "beginAtZero": True, "stacked": True, 
                        "max": y_max, 
                        "title": {"display": True, "text": "?쇱�� ?�臾�??, "font": { "size": 10 }},
                        "ticks": { "font": { "size": 10 } }
                    },
                    "y1": { 
                        "type": "linear", "display": True, "position": "right", 
                        "min": -y1_max, "max": y1_max, 
                        "grid": { "drawOnChartArea": False }, 
                        "title": {"display": True, "text": "?���� ?�臾�??, "font": { "size": 10 }},
                        "ticks": { "font": { "size": 10 } }
                    }
                }
            }
        }
        
        trend_b64 = get_quickchart_b64(qc_trend_config, height=220)
        import json
        trend_chart_json_str = json.dumps(qc_trend_config)
    # ---------------------------------------------------------


    daily_img_tag = f'<img id="dailyChartFallback" src="{daily_b64}" style="width:100%; max-width:700px; display:block; margin:0 auto;" alt="?쇱�� ?ㅼ�� 李⑦��">' if daily_b64 else ''
    monthly_img_tag = f'<img id="monthlyChartFallback" src="{monthly_b64}" style="width:100%; max-width:700px; display:block; margin:0 auto;" alt="???���� ?ㅼ�� 李⑦��">' if monthly_b64 else ''
    task_daily_img_tag = f'<img id="taskDailyChartFallback" src="{task_daily_b64}" style="width:100%; max-width:700px; display:block; margin:0 auto;" alt="?�臾대�??쇱�� ?ㅼ�� 李⑦��">' if task_daily_b64 else ''
    task_monthly_img_tag = f'<img id="taskMonthlyChartFallback" src="{task_monthly_b64}" style="width:100%; max-width:700px; display:block; margin:0 auto;" alt="?�臾대�??���� ?ㅼ�� 李⑦��">' if task_monthly_b64 else ''
    trend_img_tag = f'<img id="trendChartFallback" src="{trend_b64}" style="width:100%; display:block; margin:0 auto;" alt="?���� 異���� 洹몃��??>' if trend_b64 else ''

    custom_legend_html = '<div class="custom-legend">'
    for unique_key, t, cat in all_tasks:
        color = task_colors[unique_key]
        custom_legend_html += f'<div class="legend-item"><span class="color-box" style="background-color: {color};"></span> [{cat}] {t}</div>'
    custom_legend_html += '</div>'

    table_html = """
    <table class="report-table">
        <thead>
            <tr>
                <th rowspan="2">?�臾대��瑜�</th>
                <th rowspan="2">?�臾대�?/th>
    """
    for staff in staff_list:
        table_html += f'<th colspan="2">{staff}</th>'
    table_html += "</tr><tr>"
    for _ in staff_list:
        table_html += "<th>?쇨��</th><th>?�怨�</th>"
    table_html += "</tr></thead><tbody>"

    for cat, tasks in task_categories.items():
        for idx, t in enumerate(tasks):
            table_html += "<tr>"
            if idx == 0:
                table_html += f'<td rowspan="{len(tasks)}" class="cat-cell">{cat}</td>'
            table_html += f'<td>{t}</td>'
            
            unique_key = f"{cat}_{t}"
            for staff in staff_list:
                val_d = daily_dict.get(staff, {}).get(unique_key, daily_dict.get(staff, {}).get(t, 0))
                val_m = monthly_dict.get(staff, {}).get(unique_key, monthly_dict.get(staff, {}).get(t, 0))
                
                str_d = f"{int(val_d):,}" if val_d else "-"
                str_m = f"{int(val_m):,}" if val_m else "-"
                
                table_html += f'<td class="num-cell">{"-" if str_d=="0" else str_d}</td>'
                table_html += f'<td class="num-cell">{"-" if str_m=="0" else str_m}</td>'
            table_html += "</tr>"
    table_html += "</tbody></table>"

    other_progress_html = ""
    for staff in staff_list:
        other_text = str(daily_dict.get(staff, {}).get("other_progress", "")).strip()
        if not other_text or other_text in ["0", "nan"]:
            other_text = "-"
        else:
            other_text = other_text.replace("\n", "<br>")
            
        other_progress_html += f"""
        <div class="memo-card">
            <div class="memo-card-title">{staff}</div>
            <div class="memo-card-content">{other_text}</div>
        </div>
        """

    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(script_dir, "static", "report_template.html")
    
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()
            
        html_content = html_content.replace("{{REPORT_DATE}}", report_date_str)
        html_content = html_content.replace("{{PAGE_TITLE}}", f"?ъ��?��? ?댁��遺���� ?�臾� ?�?�蹂�??{file_date}")
        try:
            with open(os.path.join(script_dir, "static", "chart.min.js"), "r", encoding="utf-8") as js_f:
                html_content = html_content.replace("{CHART_JS}", js_f.read())
            with open(os.path.join(script_dir, "static", "chartjs-plugin-datalabels.min.js"), "r", encoding="utf-8") as d_f:
                html_content = html_content.replace("{DATALABELS_JS}", d_f.read())
        except Exception as e:
            print("Failed to load chart js:", e)
            html_content = html_content.replace("{CHART_JS}", "").replace("{DATALABELS_JS}", "")
        html_content = html_content.replace("{{MEMO_CONTENT}}", memo_content.replace("\n", "<br>"))
        html_content = html_content.replace("{{TABLE_HTML}}", table_html)
        html_content = html_content.replace("{{CUSTOM_LEGEND}}", custom_legend_html)
        html_content = html_content.replace("{{OTHER_PROGRESS_HTML}}", other_progress_html)
        
        html_content = html_content.replace("{{DAILY_CHART_JSON}}", json.dumps(qc_daily_config))
        html_content = html_content.replace("{{MONTHLY_CHART_JSON}}", json.dumps(qc_monthly_config))
        html_content = html_content.replace("{{TASK_DAILY_CHART_JSON}}", json.dumps(qc_task_daily_config))
        html_content = html_content.replace("{{TASK_MONTHLY_CHART_JSON}}", json.dumps(qc_task_monthly_config))
        html_content = html_content.replace("{{TREND_CHART_JSON}}", trend_chart_json_str)

        html_content = html_content.replace("{{DAILY_B64}}", daily_img_tag)
        html_content = html_content.replace("{{MONTHLY_B64}}", monthly_img_tag)
        html_content = html_content.replace("{{TASK_DAILY_B64}}", task_daily_img_tag)
        html_content = html_content.replace("{{TASK_MONTHLY_B64}}", task_monthly_img_tag)
        html_content = html_content.replace("{{TREND_B64}}", trend_img_tag)

        html_dir = os.path.join(target_dir, "html ?�?�蹂�??)
        os.makedirs(html_dir, exist_ok=True)
        final_path = os.path.join(html_dir, f"?ъ��?��? ?댁��遺���� ?�臾� ?�?�蹂�??{file_date}.html")
        with open(final_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return final_path
            
    except Exception as e:
        print("HTML Template Error:", e)
        return None


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

# --- ?����???���� ?���몃━��� ---
class FileLock:
    def __init__(self, filepath, timeout=5):
        self.filepath = filepath
        self.lockfile = filepath + ".lock"
        self.timeout = timeout

    def __enter__(self):
        start = time.time()
        # ?대��媛� ?���쇰�??���� (Errno 2 諛⑹?)
        os.makedirs(os.path.dirname(self.lockfile), exist_ok=True)
        while True:
            try:
                # ?����???����?쇰�� ?���� ?�洹� 李⑤��
                fd = os.open(self.lockfile, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
                break
            except FileExistsError:
                if time.time() - start > self.timeout:
                    raise TimeoutError(f"?���� ?�湲� ?�湲??�媛� 珥�怨�: ?ㅻⅨ ?ъ��?��? ?ъ�� 以���� ???����?����.\n({self.filepath})")
                time.sleep(0.1)
            except OSError as e:
                raise e
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            os.remove(self.lockfile)
        except OSError:
            pass

def safe_write_json(filepath, data):
    with FileLock(filepath):
        tmp_path = filepath + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            os.replace(tmp_path, filepath)
        except Exception as e:
            if os.path.exists(tmp_path):
                try: os.remove(tmp_path)
                except: pass
            raise e

def safe_read_json(filepath, default=None):
    with FileLock(filepath):
        if not os.path.exists(filepath):
            return default
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

def safe_write_text(filepath, text):
    with FileLock(filepath):
        tmp_path = filepath + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(text)
            os.replace(tmp_path, filepath)
        except Exception as e:
            if os.path.exists(tmp_path):
                try: os.remove(tmp_path)
                except: pass
            raise e

def safe_read_text(filepath, default=""):
    with FileLock(filepath):
        if not os.path.exists(filepath):
            return default
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
# ------------------------------

# 1. 怨���� ?ㅼ�� (濡�而� ?����?몄�� ?대�� 寃쎈�� 諛?遺�?���� 由ъ��??
import sys
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
CONFIG_FILE = os.path.join(BASE_DIR, "backup", "config.json")
try:
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
except:
    pass

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"LOCAL_BASE_PATH": ""}

import threading

def is_path_accessible(path, timeout=10.0):
    if not path:
        return False
    result = [False]
    def check():
        try:
            result[0] = os.path.exists(path)
        except:
            pass
    t = threading.Thread(target=check, daemon=True)
    t.start()
    t.join(timeout)
    return result[0]

config = load_config()
LOCAL_BASE_PATH = config.get("LOCAL_BASE_PATH", "")

if LOCAL_BASE_PATH and not is_path_accessible(LOCAL_BASE_PATH):
    LOCAL_BASE_PATH = ""

LAST_USER_FILE = os.path.join(BASE_DIR, "last_user.txt")

if LOCAL_BASE_PATH:
    STAFF_MASTER_FILE = os.path.join(LOCAL_BASE_PATH, "master/staff_master.json")
    TASK_MASTER_FILE = os.path.join(LOCAL_BASE_PATH, "master/task_master.json")
else:
    STAFF_MASTER_FILE = ""
    TASK_MASTER_FILE = ""

def load_staff_list():
    default_staff = [
        "?댁???, "?��???, "諛����??, "諛����吏?, "諛����??,
        "?댁��??, "源�?����", "?댁��??, "諛��???
    ]
    if not STAFF_MASTER_FILE:
        return default_staff
        
    try:
        os.makedirs(os.path.dirname(STAFF_MASTER_FILE), exist_ok=True)
    except Exception:
        pass

        loaded = safe_read_json(STAFF_MASTER_FILE, default=None)
        if loaded is not None:
            return loaded
    except Exception as e:
        print(f"留����???���� 濡���� ?ㅽ��: {e}")
        
    try:
        safe_write_json(STAFF_MASTER_FILE, default_staff)
    except Exception as e:
        print(f"留����???���� ?���� ?ㅽ��: {e}")
    return default_staff

STAFF_LIST = load_staff_list()

def load_task_list():
    default_tasks = {
        "?댁��": [
            "?댁��遺����",
            "pathology ?����",
            "誘몃��?�由�"
        ],
        "?ъ��": [
            "?뱀��?����",
            "寃쎄낵湲곕��",
            "誘몃��?�由�"
        ],
        "李⑦�멸��??: [
            "李⑦�멸��??
        ],
        "紐⑤��?곕��": [
            "?몃��",
            "?�湲�",
            "?����"
        ],
        "肄����": [
            "吏�肄�??,
            "媛�肄����"
        ]
    }
    if not TASK_MASTER_FILE:
        return default_tasks
        
    try:
        os.makedirs(os.path.dirname(TASK_MASTER_FILE), exist_ok=True)
    except Exception:
        pass
        
    try:
        loaded = safe_read_json(TASK_MASTER_FILE, default=None)
        if loaded is not None:
            return loaded
    except Exception as e:
        print(f"?몃? ?�臾� 留����???���� 濡���� ?ㅽ��: {e}")
        
    try:
        safe_write_json(TASK_MASTER_FILE, default_tasks)
    except Exception as e:
        print(f"?몃? ?�臾� 留����???���� ?���� ?ㅽ��: {e}")
    return default_tasks

TASK_CATEGORIES = load_task_list()

class SettingsWindow(QDialog):
    def __init__(self, app_window):
        super().__init__(app_window)
        self.app = app_window
        self.setWindowTitle("?�寃�?ㅼ��")
        self.resize(500, 600)
        
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Tab 1: General
        self.tab_general = QWidget()
        self.setup_general_tab()
        self.tabs.addTab(self.tab_general, "湲곕낯 ?ㅼ��")
        
        # Tab 2: Staff
        self.tab_staff = QWidget()
        self.setup_staff_tab()
        self.tabs.addTab(self.tab_staff, "?대��??愿�由?)
        
        # Tab 3: Tasks
        self.tab_tasks = QWidget()
        self.setup_task_tab()
        self.tabs.addTab(self.tab_tasks, "?몃??�臾� 愿�由?)
        
        btn_frame = QFrame()
        btn_layout = QVBoxLayout(btn_frame)
        self.save_btn = QPushButton("?�??諛??リ린")
        self.save_btn.clicked.connect(self.save_settings)
        btn_layout.addWidget(self.save_btn)
        layout.addWidget(btn_frame)

    def setup_general_tab(self):
        layout = QVBoxLayout(self.tab_general)
        layout.addWidget(QLabel("?곗��???���� ?대�� ?�移�:"))
        
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit(LOCAL_BASE_PATH)
        self.path_edit.setReadOnly(True)
        path_layout.addWidget(self.path_edit)
        
        btn_browse = QPushButton("?대�� 蹂�寃?..")
        btn_browse.clicked.connect(self.browse_path)
        path_layout.addWidget(btn_browse)
        layout.addLayout(path_layout)
        
        btn_html = QPushButton("?�?�蹂�??HTML ?�??)
        btn_html.clicked.connect(self.app.export_to_html)
        layout.addWidget(btn_html)
        
        btn_excel = QPushButton("?��?濡?痍⑦��/?�??)
        btn_excel.clicked.connect(self.app.export_to_excel)
        layout.addWidget(btn_excel)
        layout.addStretch()

    def browse_path(self):
        from PySide6.QtWidgets import QFileDialog
        d = QFileDialog.getExistingDirectory(self, "?�臾�?쇱? ?�???대�� ?����", LOCAL_BASE_PATH)
        if d:
            self.path_edit.setText(d)

    def setup_staff_tab(self):
        layout = QVBoxLayout(self.tab_staff)
        self.staff_list = QListWidget()
        self.staff_list.addItems(STAFF_LIST)
        layout.addWidget(self.staff_list)
        
        ctrl_layout = QHBoxLayout()
        self.new_staff_edit = QLineEdit()
        ctrl_layout.addWidget(self.new_staff_edit)
        
        btn_add = QPushButton("異��?")
        btn_add.clicked.connect(self.add_staff)
        ctrl_layout.addWidget(btn_add)
        
        btn_del = QPushButton("?���� ??��")
        btn_del.clicked.connect(self.delete_staff)
        ctrl_layout.addWidget(btn_del)
        
        layout.addLayout(ctrl_layout)

    def add_staff(self):
        t = self.new_staff_edit.text().strip()
        if t:
            self.staff_list.addItem(t)
            self.new_staff_edit.clear()

    def delete_staff(self):
        for item in self.staff_list.selectedItems():
            self.staff_list.takeItem(self.staff_list.row(item))

    def setup_task_tab(self):
        layout = QVBoxLayout(self.tab_tasks)
        self.task_tree = QTreeWidget()
        self.task_tree.setHeaderLabels(["??ぉ紐?, "?����"])
        self.task_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        layout.addWidget(self.task_tree)
        
        for cat, tasks in TASK_CATEGORIES.items():
            cat_item = QTreeWidgetItem([cat, "移댄��怨�由�"])
            self.task_tree.addTopLevelItem(cat_item)
            cat_item.setExpanded(True)
            for t in tasks:
                t_item = QTreeWidgetItem([t, "?몃??�臾�"])
                cat_item.addChild(t_item)
                
        ctrl_layout = QHBoxLayout()
        self.new_task_edit = QLineEdit()
        ctrl_layout.addWidget(self.new_task_edit)
        layout.addLayout(ctrl_layout)
        
        btn_layout = QHBoxLayout()
        btn_add_cat = QPushButton("移댄��怨�由� 異��?")
        btn_add_cat.clicked.connect(self.add_category)
        btn_layout.addWidget(btn_add_cat)
        
        btn_add_task = QPushButton("?몃??�臾� 異��?")
        btn_add_task.clicked.connect(self.add_task)
        btn_layout.addWidget(btn_add_task)
        
        btn_del = QPushButton("?���� ??��")
        btn_del.clicked.connect(self.delete_task)
        btn_layout.addWidget(btn_del)
        
        layout.addLayout(btn_layout)

    def add_category(self):
        t = self.new_task_edit.text().strip()
        if t:
            cat = QTreeWidgetItem([t, "移댄��怨�由�"])
            self.task_tree.addTopLevelItem(cat)
            cat.setExpanded(True)
            self.new_task_edit.clear()

    def add_task(self):
        t = self.new_task_edit.text().strip()
        if not t: return
        items = self.task_tree.selectedItems()
        if not items:
            QMessageBox.warning(self, "寃쎄��", "癒쇱? 異��???移댄��怨�由щ�??����?댁＜?몄��.")
            return
        item = items[0]
        if item.text(1) == "?몃??�臾�":
            item = item.parent()
        t_item = QTreeWidgetItem([t, "?몃??�臾�"])
        item.addChild(t_item)
        self.new_task_edit.clear()

    def delete_task(self):
        items = self.task_tree.selectedItems()
        if items:
            item = items[0]
            parent = item.parent()
            if parent:
                parent.removeChild(item)
            else:
                idx = self.task_tree.indexOfTopLevelItem(item)
                self.task_tree.takeTopLevelItem(idx)

    def save_settings(self):
        global LOCAL_BASE_PATH, STAFF_MASTER_FILE, TASK_MASTER_FILE
        new_path = self.path_edit.text().strip()
        if new_path:
            LOCAL_BASE_PATH = new_path
            os.makedirs(LOCAL_BASE_PATH, exist_ok=True)
            STAFF_MASTER_FILE = os.path.join(LOCAL_BASE_PATH, "master", "staff_master.json")
            TASK_MASTER_FILE = os.path.join(LOCAL_BASE_PATH, "master", "task_master.json")
            try:
                os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
                config_data = safe_read_json(CONFIG_FILE, default={})
                config_data["LOCAL_BASE_PATH"] = new_path
                safe_write_json(CONFIG_FILE, config_data)
            except Exception as e:
                QMessageBox.critical(self, "?ㅻ��", f"寃쎈�� ?ㅼ�� ?�???ㅽ��: {e}")
                return
        
        new_staff = []
        for i in range(self.staff_list.count()):
            new_staff.append(self.staff_list.item(i).text())
        safe_write_json(STAFF_MASTER_FILE, new_staff)
        
        new_tasks = {}
        for i in range(self.task_tree.topLevelItemCount()):
            cat = self.task_tree.topLevelItem(i)
            cat_name = cat.text(0)
            sub_tasks = []
            for j in range(cat.childCount()):
                sub_tasks.append(cat.child(j).text(0))
            new_tasks[cat_name] = sub_tasks
        safe_write_json(TASK_MASTER_FILE, new_tasks)
        
        QMessageBox.information(self, "?�???�猷�", "?ㅼ��???�?λ��?����?����.\n?����???�瑜대�??�濡�洹몃��???ъ��?����?����.")
        self.accept()
        
        # ?����???? ?ъ��??
        from PySide6.QtCore import QProcess
        from PySide6.QtWidgets import QApplication
        import sys
        QProcess.startDetached(sys.executable, sys.argv[1:])
        QApplication.quit()


class WorkLogApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WORK log - ?ъ��?��? ?댁��遺���� ?�臾�?쇱? (v1.0)")
        win_w = config.get("WIN_WIDTH", 600)
        win_h = config.get("WIN_HEIGHT", 1020)
        self.resize(win_w, win_h)
        self.entries = {}
        
        # Window start centered (simple approach)
        self.startup_check()
        
    def closeEvent(self, event):
        try:
            config_data = safe_read_json(CONFIG_FILE, default={})
            config_data["WIN_WIDTH"] = self.width()
            config_data["WIN_HEIGHT"] = self.height()
            safe_write_json(CONFIG_FILE, config_data)
        except Exception as e:
            print(f"Failed to save window size: {e}")
        super().closeEvent(event)

    def startup_check(self):
        global STAFF_LIST, TASK_CATEGORIES
        if not LOCAL_BASE_PATH or not os.path.exists(LOCAL_BASE_PATH):
            if LOCAL_BASE_PATH:
                QMessageBox.critical(self, "?���� ?ㅻ��", f"?ㅼ��???대��?� ?곌껐?��? ?����?듬��??\n寃쎈��: {LOCAL_BASE_PATH}")
            dlg = SettingsWindow(self)
            dlg.exec()
            if not LOCAL_BASE_PATH or not os.path.exists(LOCAL_BASE_PATH):
                sys.exit(0)
            STAFF_LIST = load_staff_list()
            TASK_CATEGORIES = load_task_list()
            
        self.create_widgets()

    def create_widgets(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Header
        header_layout = QHBoxLayout()
        title_lbl = QLabel("?ъ��?��? ?댁��遺���� ?�臾�?쇱?")
        font = QFont("Arial", 16, QFont.Bold)
        title_lbl.setFont(font)
        header_layout.addWidget(title_lbl)
        
        btn_settings = QPushButton("?�寃�?ㅼ��")
        btn_settings.clicked.connect(self.open_settings)
        header_layout.addWidget(btn_settings, 0, Qt.AlignRight)
        main_layout.addLayout(header_layout)
        
        # Info Box
        info_group = QGroupBox("?쇱�� / ?ъ��???����")
        info_layout = QHBoxLayout(info_group)
        
        info_layout.addWidget(QLabel("?���� ?�吏�:"))
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.dateChanged.connect(self.load_data)
        info_layout.addWidget(self.date_edit)
        
        info_layout.addSpacing(20)
        
        info_layout.addWidget(QLabel("?대��???����:"))
        self.staff_combo = QComboBox()
        self.staff_combo.addItems(STAFF_LIST)
        
        last_user = "?댄��二?
        if os.path.exists(LAST_USER_FILE):
            try:
                with open(LAST_USER_FILE, "r", encoding="utf-8") as f:
                    u = f.read().strip()
                    if u in STAFF_LIST:
                        last_user = u
            except: pass
        if last_user in STAFF_LIST:
            self.staff_combo.setCurrentText(last_user)
            
        self.staff_combo.currentIndexChanged.connect(self.load_data)
        info_layout.addWidget(self.staff_combo)
        info_layout.addStretch()
        
        main_layout.addWidget(info_group)
        
        # Memo Box
        memo_group = QGroupBox()
        memo_layout = QVBoxLayout(memo_group)
        
        memo_header_layout = QHBoxLayout()
        memo_title = QLabel("怨듯�� 二쇱��?ы��")
        memo_header_layout.addWidget(memo_title)
        
        memo_header_layout.addStretch()
        btn_memo_load = QPushButton("遺����?ㅺ린")
        btn_memo_load.clicked.connect(lambda: self.load_memo(silent=False))
        btn_memo_save = QPushButton("?�?ν��湲?)
        btn_memo_save.clicked.connect(self.save_memo)
        memo_header_layout.addWidget(btn_memo_load)
        memo_header_layout.addWidget(btn_memo_save)
        memo_layout.addLayout(memo_header_layout)
        
        self.memo_text = QTextEdit()
        self.memo_text.setMaximumHeight(80)
        memo_layout.addWidget(self.memo_text)
        main_layout.addWidget(memo_group)
        
        # Tasks & Other Box
        tasks_group = QGroupBox("?몃? ?�臾� ?ㅼ�� (?쇨�� 嫄댁�� ?����)")
        tasks_layout = QHBoxLayout(tasks_group)
        
        # Left: Scroll area for tasks
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        self.entry_list = []
        self.cat_groups = {}
        self.cat_contents = {}
        for cat, fields in TASK_CATEGORIES.items():
            cat_group = QGroupBox(cat)
            cat_group.setCheckable(True)
            cat_group.setChecked(True)
            self.cat_groups[cat] = cat_group
            
            # 移댄��怨�由� ?�?댄??� 吏����寃? ?댁��?� 湲곕낯 ?고�몃�?
            title_font = QFont("Arial", 11, QFont.Bold)
            cat_group.setFont(title_font)
            
            group_layout = QVBoxLayout(cat_group)
            group_layout.setContentsMargins(0, 0, 0, 0)
            cat_content = QWidget()
            self.cat_contents[cat] = cat_content
            group_layout.addWidget(cat_content)
            cat_layout = QGridLayout(cat_content)
            
            cat_group.toggled.connect(lambda checked, w=cat_content, c=cat: self.toggle_category(c, checked, w))
            normal_font = QFont("留��? 怨����", 10)
            
            for idx, field in enumerate(fields):
                lbl = QLabel(field)
                lbl.setFont(normal_font)
                cat_layout.addWidget(lbl, idx, 0)
                
                le = QLineEdit("0")
                le.setFont(normal_font)
                le.setFixedWidth(80)
                le.setAlignment(Qt.AlignRight)
                
                from PySide6.QtGui import QIntValidator
                le.setValidator(QIntValidator(0, 99999))
                le.returnPressed.connect(lambda w=le: self.focus_next_entry(w))
                
                cat_layout.addWidget(le, idx, 1)
                
                unique_key = f"{cat}_{field}"
                self.entries[unique_key] = le
                self.entry_list.append(le)
                
            scroll_layout.addWidget(cat_group)
            
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        tasks_layout.addWidget(scroll, 1)
        
        # Right: Other progress
        other_layout = QVBoxLayout()
        other_layout.addWidget(QLabel("[洹몄�� ?�臾� 吏����?ы��]"))
        self.other_progress_text = QTextEdit()
        other_layout.addWidget(self.other_progress_text)
        tasks_layout.addLayout(other_layout, 1)
        
        main_layout.addWidget(tasks_group, 1)
        
        # Bottom Buttons
        btn_frame = QFrame()
        btn_layout = QHBoxLayout(btn_frame)
        
        btn_refresh = QPushButton("理���� ?곗��??遺����?ㅺ린")
        btn_refresh.setMinimumHeight(40)
        btn_refresh.clicked.connect(self.refresh_data)
        btn_layout.addWidget(btn_refresh)
        
        btn_save = QPushButton("???ㅼ�� ?�?ν��湲?)
        btn_save.setMinimumHeight(40)
        btn_save.clicked.connect(self.save_data)
        btn_layout.addWidget(btn_save)
        
        btn_preview = QPushButton("誘몃━蹂닿린")
        btn_preview.setMinimumHeight(40)
        btn_preview.clicked.connect(self.preview_html)
        btn_layout.addWidget(btn_preview)
        
        main_layout.addWidget(btn_frame)
        
        self.load_data()

    def open_settings(self):
        dlg = SettingsWindow(self)
        dlg.exec()
        
    def refresh_data(self):
        self.load_data()
        self.load_memo(silent=True)
        QMessageBox.information(self, "遺����?ㅺ린 ?�猷�", "?�踰�(?대��)???�?λ�� 理���� ?곗��?곕? ?깃났?���쇰�?遺����?����?����.")

    def save_data(self):
        user_name = self.staff_combo.currentText()
        if not user_name or user_name == "?����?����??:
            QMessageBox.warning(self, "寃쎄��", "?대��?��? ?����??二쇱��??")
            return

        date_input = self.date_edit.date().toString("yyyy-MM-dd")
        date_obj = self.date_edit.date().toPython()
        folder_month = date_obj.strftime("%Y-%m")
        file_date = date_obj.strftime("%Y%m%d")

        task_data = {}
        for unique_key, le in self.entries.items():
            val = le.text().strip()
            task_data[unique_key] = int(val) if val.isdigit() else 0

        target_dir = os.path.join(LOCAL_BASE_PATH, folder_month)
        os.makedirs(target_dir, exist_ok=True)

        file_name = f"{file_date}_{user_name}.json"
        file_path = os.path.join(target_dir, file_name)

        history = []
        if os.path.exists(file_path):
            try:
                old_data = safe_read_json(file_path)
                if old_data:
                    history = old_data.get("history", [])
                    old_state = {k: v for k, v in old_data.items() if k != "history"}
                    history.append(old_state)
            except: pass

        payload = {
            "date": date_input,
            "name": user_name,
            "tasks": task_data,
            "other_progress": self.other_progress_text.toPlainText().strip(),
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ip": get_local_ip(),
            "history": history
        }

        try:
            safe_write_json(file_path, payload)
            safe_write_text(LAST_USER_FILE, user_name)
            QMessageBox.information(self, "?�???깃났", f"{user_name}?���� {date_input} ?ㅼ��???�?λ��?����?����.")
        except Exception as e:
            QMessageBox.critical(self, "?�???ㅽ��", f"?ㅻ��媛� 諛����?����?����: {e}")

    def preview_html(self):
        self._generate_html(is_export=False)

    def export_to_html(self):
        self._generate_html(is_export=True)

    def _generate_html(self, is_export=False):
        date_input = self.date_edit.date().toString("yyyy-MM-dd")
        date_obj = self.date_edit.date().toPython()
        folder_month = date_obj.strftime("%Y-%m")
        file_date = date_obj.strftime("%Y%m%d")

        target_dir = os.path.join(LOCAL_BASE_PATH, folder_month)
        os.makedirs(target_dir, exist_ok=True)
        json_files = glob.glob(os.path.join(target_dir, "*.json"))

        all_rows = []
        for file_path in json_files:
            try:
                data = safe_read_json(file_path)
                if data:
                    row = {"?쇱��": data.get("date", ""), "?대��??: data.get("name", ""), "other_progress": data.get("other_progress", "")}
                    tasks = data.get("tasks", {})
                    for cat, fields in TASK_CATEGORIES.items():
                        for field in fields:
                            unique_key = f"{cat}_{field}"
                            row[unique_key] = tasks.get(unique_key, tasks.get(field, 0))
                    all_rows.append(row)
            except: pass

        user_name = self.staff_combo.currentText()
        if user_name and user_name != "?����?����??:
            task_data = {}
            for unique_key, le in self.entries.items():
                val = le.text().strip()
                task_data[unique_key] = int(val) if val.isdigit() else 0
            
            ui_row = {"?쇱��": date_input, "?대��??: user_name, "other_progress": self.other_progress_text.toPlainText().strip()}
            ui_row.update(task_data)
            
            replaced = False
            for i, r in enumerate(all_rows):
                if r.get("?쇱��") == date_input and r.get("?대��??) == user_name:
                    all_rows[i] = ui_row
                    replaced = True
                    break
            if not replaced:
                all_rows.append(ui_row)

        if not all_rows:
            QMessageBox.information(self, "?����", "?����???곗��?곌? ?����?����.")
            return

        df_all = pd.DataFrame(all_rows)
        all_unique_users = df_all["?대��??].unique().tolist()
        ordered_users = STAFF_LIST + [u for u in all_unique_users if u not in STAFF_LIST]

        df_daily = df_all[df_all["?쇱��"] == date_input]
        daily_dict = df_daily.set_index("?대��??).to_dict('index') if not df_daily.empty else {}

        df_monthly_base = df_all[df_all["?쇱��"].str.startswith(folder_month)].copy()
        cols = [c for c in df_monthly_base.columns if c not in ['?쇱��', '?대��??, 'other_progress']]
        df_monthly_base[cols] = df_monthly_base[cols].apply(pd.to_numeric, errors='coerce')
        monthly_dict = df_monthly_base.groupby("?대��??).sum(numeric_only=True).to_dict('index')

        memo_content = self.memo_text.toPlainText().strip()
        if not memo_content:
            memo_path = os.path.join(target_dir, f"{file_date}_memo.txt")
            if os.path.exists(memo_path):
                memo_content = safe_read_text(memo_path) or ""

        out_file = generate_html_report(date_input, target_dir, daily_dict, monthly_dict, memo_content, ordered_users, TASK_CATEGORIES, is_preview=not is_export, df_monthly_base=df_monthly_base)
        if out_file:
            webbrowser.open('file://' + os.path.realpath(out_file))
            if is_export:
                QMessageBox.information(self, "?�猷�", f"HTML 由ы��?멸? ?����?����?듬��??\n{out_file}")
        else:
            QMessageBox.critical(self, "?ㅻ��", "由ы��???����留??ㅽ��.")

    def export_to_excel(self):
        date_input = self.date_edit.date().toString("yyyy-MM-dd")
        date_obj = self.date_edit.date().toPython()
        folder_month = date_obj.strftime("%Y-%m")
        file_date = date_obj.strftime("%Y%m%d")

        target_dir = os.path.join(LOCAL_BASE_PATH, folder_month)
        json_files = glob.glob(os.path.join(target_dir, "*.json"))

        if not json_files:
            QMessageBox.information(self, "?����", f"{folder_month} ?���� ?�?λ�� ?곗��?곌? ?����?����.")
            return

        all_rows = []
        for file_path in json_files:
            try:
                data = safe_read_json(file_path)
                if data:
                    row = {"?쇱��": data.get("date", ""), "?대��??: data.get("name", ""), "other_progress": data.get("other_progress", "")}
                    tasks = data.get("tasks", {})
                    for cat, fields in TASK_CATEGORIES.items():
                        for field in fields:
                            unique_key = f"{cat}_{field}"
                            row[unique_key] = tasks.get(unique_key, tasks.get(field, 0))
                    all_rows.append(row)
            except: pass

        if not all_rows:
            QMessageBox.information(self, "?����", "?����???곗��?곌? ?����?����.")
            return

        df_all = pd.DataFrame(all_rows)
        all_unique_users = df_all["?대��??].unique().tolist()
        ordered_users = STAFF_LIST + [u for u in all_unique_users if u not in STAFF_LIST]

        df_daily = df_all[df_all["?쇱��"] == date_input].copy()
        if not df_daily.empty:
            df_daily.set_index("?대��??, inplace=True)
            df_daily = df_daily.reindex(ordered_users)
            df_daily.index.name = "?대��??
            df_daily.reset_index(inplace=True)
            df_daily["?쇱��"] = df_daily["?쇱��"].fillna(date_input)
            for col in df_daily.columns:
                if col in ["?쇱��", "?대��??, "other_progress"]:
                    df_daily[col] = df_daily[col].fillna("")
                else:
                    df_daily[col] = df_daily[col].fillna(0)
        else:
            df_daily = pd.DataFrame(columns=["?쇱��", "?대��??, "other_progress"] + [f"{c}_{f}" for c, fs in TASK_CATEGORIES.items() for f in fs])

        if "?쇱��" in df_all.columns:
            df_monthly_base = df_all.drop(columns=["?쇱��"])
        else:
            df_monthly_base = df_all
            
        cols = [c for c in df_monthly_base.columns if c not in ['?쇱��', '?대��??, 'other_progress']]
        df_monthly_base[cols] = df_monthly_base[cols].apply(pd.to_numeric, errors='coerce')
        
        df_monthly = df_monthly_base.groupby("?대��??).sum(numeric_only=True)
        df_monthly = df_monthly.reindex(ordered_users)
        df_monthly.index.name = "?대��??
        df_monthly.reset_index(inplace=True)
        for col in df_monthly.columns:
            if col in ["?대��??]:
                df_monthly[col] = df_monthly[col].fillna("")
            else:
                df_monthly[col] = df_monthly[col].fillna(0)

        daily_dict = df_daily.set_index("?대��??).to_dict('index') if not df_daily.empty else {}
        monthly_dict = df_monthly_base.groupby("?대��??).sum(numeric_only=True).to_dict('index')

        monthly_task_cols = [col for col in df_monthly.columns if col != "?대��??]
        m_total_row = {col: df_monthly[col].sum() for col in monthly_task_cols}
        m_total_row["?대��??] = "?�媛� 遺�??珥����"
        df_monthly_with_total = pd.concat([df_monthly, pd.DataFrame([m_total_row])], ignore_index=True)

        excel_name = f"?�臾�?쇱?_痍⑦��_{folder_month}.xlsx"
        excel_path = os.path.join(target_dir, excel_name)

        try:
            with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
                pd.DataFrame().to_excel(writer, sheet_name=date_input, header=False, index=False)
                df_monthly_with_total.to_excel(writer, sheet_name="?�媛� ?����", index=False)
                
                workbook = writer.book
                worksheet = writer.sheets[date_input]
                
                fmt_title = workbook.add_format({'bold': True, 'font_size': 18})
                fmt_subtitle = workbook.add_format({'bold': True, 'font_size': 12})
                fmt_header_gray = workbook.add_format({'bold': True, 'bg_color': '#D9D9D9', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
                fmt_header_diag = workbook.add_format({'bold': True, 'bg_color': '#D9D9D9', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'diag_type': 1, 'diag_border': 1})
                fmt_category = workbook.add_format({'bg_color': '#F2F2F2', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
                fmt_task = workbook.add_format({'bg_color': '#F2F2F2', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
                fmt_val = workbook.add_format({'border': 1, 'align': 'right', 'valign': 'vcenter', 'num_format': '#,##0'})
                fmt_val_zero = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
                fmt_memo = workbook.add_format({'border': 1, 'align': 'left', 'valign': 'top', 'text_wrap': True})
                
                weekdays = ["?����??, "?����??, "?����??, "紐⑹��??, "湲����??, "?����??, "?쇱��??]
                day_str = weekdays[date_obj.weekday()]
                date_str = f"??{date_obj.year}??{date_obj.month}??{date_obj.day}??({day_str})"
                
                worksheet.write(0, 0, "?�臾�?쇱?", fmt_title)
                worksheet.write(2, 0, date_str, fmt_subtitle)
                
                worksheet.set_column(0, 0, 10)
                worksheet.set_column(1, 1, 15)
                
                num_staff = len(ordered_users)
                max_col = 1 + num_staff * 2
                
                memo_content = ""
                memo_path = os.path.join(target_dir, f"{file_date}_memo.txt")
                if os.path.exists(memo_path):
                    try:
                        with open(memo_path, 'r', encoding='utf-8') as f:
                            memo_content = f.read().strip()
                    except: pass
                
                worksheet.merge_range(4, 0, 4, max_col, "二???????, fmt_header_gray)
                worksheet.merge_range(5, 0, 8, max_col, memo_content, fmt_memo)
                    
                start_row = 10
                worksheet.merge_range(start_row, 0, start_row, max_col, "媛�蹂� ?�臾� ?����", fmt_header_gray)
                
                hr1 = start_row + 1
                hr2 = start_row + 2
                worksheet.merge_range(hr1, 0, hr2, 1, "?대��??              \n               ?�臾대�?, fmt_header_diag)
                
                col = 2
                for staff in ordered_users:
                    worksheet.merge_range(hr1, col, hr1, col+1, staff, fmt_header_gray)
                    worksheet.write(hr2, col, "?쇨��", fmt_header_gray)
                    worksheet.write(hr2, col+1, "?�怨�", fmt_header_gray)
                    worksheet.set_column(col, col+1, 6)
                    col += 2
                    
                row = hr2 + 1
                for cat, tasks in TASK_CATEGORIES.items():
                    cat_start = row
                    for t in tasks:
                        worksheet.write(row, 1, t, fmt_task)
                        c = 2
                        unique_key = f"{cat}_{t}"
                        for staff in ordered_users:
                            val_d = daily_dict.get(staff, {}).get(unique_key, daily_dict.get(staff, {}).get(t, 0))
                            if pd.isna(val_d) or val_d == 0 or str(val_d).strip() == "":
                                worksheet.write(row, c, "-", fmt_val_zero)
                            else:
                                worksheet.write(row, c, float(val_d), fmt_val)
                                
                            val_m = monthly_dict.get(staff, {}).get(unique_key, monthly_dict.get(staff, {}).get(t, 0))
                            if pd.isna(val_m) or val_m == 0 or str(val_m).strip() == "":
                                worksheet.write(row, c+1, "-", fmt_val_zero)
                            else:
                                worksheet.write(row, c+1, float(val_m), fmt_val)
                            c += 2
                        row += 1
                        
                    if row > cat_start:
                        if row - 1 == cat_start:
                            worksheet.write(cat_start, 0, cat, fmt_category)
                        else:
                            worksheet.merge_range(cat_start, 0, row-1, 0, cat, fmt_category)
                
                worksheet.merge_range(row, 0, row+4, 1, "洹몄��\n?�臾� 吏����?ы��", fmt_category)
                c = 2
                for staff in ordered_users:
                    other_text = daily_dict.get(staff, {}).get("other_progress", "")
                    if pd.isna(other_text) or other_text == 0:
                        other_text = ""
                    worksheet.merge_range(row, c, row+4, c+1, str(other_text).strip(), fmt_memo)
                    c += 2
                
                worksheet_monthly = writer.sheets['?�媛� ?����']
                chart_monthly = workbook.add_chart({'type': 'column'})
                
                last_row = len(df_monthly_with_total)
                task_start_col = 1
                task_end_col = len(monthly_task_cols)
                
                chart_monthly.add_series({
                    'name': '??ぉ蹂??�媛� 遺�??珥??�臾�??,
                    'categories': ['?�媛� ?����', 0, task_start_col, 0, task_end_col],
                    'values':     ['?�媛� ?����', last_row, task_start_col, last_row, task_end_col],
                    'data_labels': {'value': True}
                })
                chart_monthly.set_title({'name': f'?�媛� ??ぉ蹂?遺�???ㅼ�� ({folder_month})'})
                chart_monthly.set_x_axis({'name': '?몃? ?�臾�'})
                chart_monthly.set_y_axis({'name': '珥??�臾� 嫄댁��'})
                
                worksheet_monthly.insert_chart(1, len(df_monthly_with_total.columns) + 1, chart_monthly)
                
            QMessageBox.information(self, "痍⑦�� ?깃났", f"珥?{len(json_files)}嫄댁�� ?����??泥�由�?����?듬��??\n\n?�??寃쎈��:\n{excel_path}")
            
            import subprocess
            if sys.platform == "win32":
                os.startfile(excel_path)
            elif sys.platform == "darwin":
                subprocess.Popen(['open', excel_path])
            else:
                subprocess.Popen(['xdg-open', excel_path])
        except Exception as e:
            # Fallback if xlsxwriter not available
            try:
                with pd.ExcelWriter(excel_path) as writer:
                    df_daily.to_excel(writer, sheet_name=date_input, index=False)
                    df_monthly_with_total.to_excel(writer, sheet_name="?�媛� ?����", index=False)
                QMessageBox.information(self, "痍⑦�� ?깃났 (湲곕낯)", f"珥?{len(json_files)}嫄댁�� ?����??泥�由�?����?듬��??\n\n?�??寃쎈��:\n{excel_path}")
                import subprocess
                if sys.platform == "win32":
                    os.startfile(excel_path)
                elif sys.platform == "darwin":
                    subprocess.Popen(['open', excel_path])
                else:
                    subprocess.Popen(['xdg-open', excel_path])
            except Exception as e2:
                QMessageBox.critical(self, "?ㅻ��", f"?��? ?�??以??ㅻ��媛� 諛����?����?����: {e}\n{e2}")

    def focus_next_entry(self, current_le):
        try:
            idx = self.entry_list.index(current_le)
            for i in range(idx + 1, len(self.entry_list)):
                if self.entry_list[i].isVisible():
                    self.entry_list[i].setFocus()
                    self.entry_list[i].selectAll()
                    return
            current_le.focusNextChild()
        except ValueError:
            current_le.focusNextChild()

    def toggle_category(self, cat, checked, widget):
        widget.setVisible(checked)
        try:
            config_data = safe_read_json(CONFIG_FILE, default={})
            collapsed = config_data.get("COLLAPSED_CATEGORIES", {})
            user = self.staff_combo.currentText()
            if user:
                user_collapsed = collapsed.get(user, [])
                if not checked and cat not in user_collapsed:
                    user_collapsed.append(cat)
                elif checked and cat in user_collapsed:
                    user_collapsed.remove(cat)
                collapsed[user] = user_collapsed
                config_data["COLLAPSED_CATEGORIES"] = collapsed
                safe_write_json(CONFIG_FILE, config_data)
        except Exception as e:
            print("Failed to save collapse state:", e)

    def load_data(self):
        date_input = self.date_edit.date().toString("yyyy-MM-dd")
        user_name = self.staff_combo.currentText()
        if not user_name or user_name == "?����?����??:
            return

        date_obj = self.date_edit.date().toPython()
        folder_month = date_obj.strftime("%Y-%m")
        file_date = date_obj.strftime("%Y%m%d")
        target_dir = os.path.join(LOCAL_BASE_PATH, folder_month)
        
        for le in self.entry_list:
            le.setText("0")
        self.other_progress_text.clear()
        
        file_path = os.path.join(target_dir, f"{file_date}_{user_name}.json")
        if os.path.exists(file_path):
            try:
                data = safe_read_json(file_path)
                if data:
                    tasks = data.get("tasks", {})
                    for cat, fields in TASK_CATEGORIES.items():
                        for field in fields:
                            unique_key = f"{cat}_{field}"
                            val = tasks.get(unique_key, tasks.get(field, 0))
                            if unique_key in self.entries:
                                self.entries[unique_key].setText(str(val))
                    other = data.get("other_progress", "")
                    if other:
                        self.other_progress_text.setPlainText(other)
            except: pass

        try:
            config_data = safe_read_json(CONFIG_FILE, default={})
            collapsed = config_data.get("COLLAPSED_CATEGORIES", {})
            user_name = self.staff_combo.currentText()
            user_collapsed = collapsed.get(user_name, [])
            for c_name, group in getattr(self, 'cat_groups', {}).items():
                is_checked = c_name not in user_collapsed
                group.blockSignals(True)
                group.setChecked(is_checked)
                if c_name in getattr(self, 'cat_contents', {}):
                    self.cat_contents[c_name].setVisible(is_checked)
                group.blockSignals(False)
        except Exception as e:
            print("Failed to load collapse state:", e)

        self.load_memo(silent=True)

    def load_memo(self, silent=False):
        date_obj = self.date_edit.date().toPython()
        folder_month = date_obj.strftime("%Y-%m")
        file_date = date_obj.strftime("%Y%m%d")
        target_dir = os.path.join(LOCAL_BASE_PATH, folder_month)
        memo_path = os.path.join(target_dir, f"{file_date}_memo.txt")
        
        self.memo_text.clear()
        if os.path.exists(memo_path):
            try:
                memo = safe_read_text(memo_path)
                if memo:
                    self.memo_text.setPlainText(memo.strip())
                if not silent: QMessageBox.information(self, "遺����?ㅺ린", "?깃났?���쇰�?遺����?����?����.")
            except: pass

    def save_memo(self):
        date_obj = self.date_edit.date().toPython()
        folder_month = date_obj.strftime("%Y-%m")
        file_date = date_obj.strftime("%Y%m%d")
        target_dir = os.path.join(LOCAL_BASE_PATH, folder_month)
        os.makedirs(target_dir, exist_ok=True)
        memo_path = os.path.join(target_dir, f"{file_date}_memo.txt")
        
        try:
            safe_write_text(memo_path, self.memo_text.toPlainText().strip())
            QMessageBox.information(self, "?�???깃났", "?깃났?���쇰�??�?λ��?����?����.")
        except Exception as e:
            QMessageBox.critical(self, "?ㅻ��", str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    font = QFont("留��? 怨����", 10)
    app.setFont(font)
    
    window = WorkLogApp()
    window.show()
    sys.exit(app.exec())
