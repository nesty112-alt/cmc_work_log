import os
import json
import glob
import time
from datetime import datetime
import socket
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd


try:
    from tkcalendar import DateEntry
    HAS_TKCALENDAR = True
except ImportError:
    HAS_TKCALENDAR = False

# --- HTML Export Code ---
import webbrowser
import urllib.request
import urllib.parse
import base64

QUICKCHART_OFFLINE = False

def get_quickchart_b64(chart_config):
    global QUICKCHART_OFFLINE
    if QUICKCHART_OFFLINE:
        return ""
        
    url = "https://quickchart.io/chart"
    payload = {
        "backgroundColor": "white",
        "width": 700,
        "height": 400,
        "format": "png",
        "version": "3",
        "chart": chart_config
    }
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=1.5) as response:
            image_data = response.read()
            b64 = base64.b64encode(image_data).decode('utf-8')
            return f"data:image/png;base64,{b64}"
    except Exception as e:
        print("QuickChart fallback error:", e)
        QUICKCHART_OFFLINE = True
        return ""

# 업무 종류별 컬러 팔레트 (차트 렌더링용)
COLOR_PALETTE = [
    '#9B81DD', # 연보라
    '#4EBC9D', # 청록
    '#3984C6', # 파랑
    '#F2A154', # 주황
    '#E76F51', # 빨강
    '#2A9D8F', # 진녹색
    '#E9C46A', # 노랑
    '#6D6875', # 회색
    '#B5838D', # 탁한분홍
    '#E5989B', # 핑크
    '#FFB4A2', # 살구
    '#84A59D', # 에메랄드
    '#F6BD60', # 샌드
    '#F28482', # 로즈
]

def generate_html_report(date_input, target_dir, daily_dict, monthly_dict, memo_content, staff_list, task_categories, is_preview=False):
    try:
        date_obj = datetime.strptime(date_input, "%Y-%m-%d")
        weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
        day_str = weekdays[date_obj.weekday()]
        report_date_str = f"{date_obj.year}년 {date_obj.month}월 {date_obj.day}일 ({day_str})"
        file_date = date_obj.strftime("%Y%m%d")
    except:
        report_date_str = date_input
        file_date = date_input.replace("-", "")

    # 모든 세부 업무 리스트 추출 및 컬러 매핑
    all_tasks = []
    task_colors = {}
    color_idx = 0
    for cat, tasks in task_categories.items():
        for t in tasks:
            unique_key = f"{cat}_{t}"
            all_tasks.append((unique_key, t, cat))
            task_colors[unique_key] = COLOR_PALETTE[color_idx % len(COLOR_PALETTE)]
            color_idx += 1

    # ------------------ Chart.js 데이터 구성 ------------------
    # 일계 차트 데이터
    daily_datasets = []
    for unique_key, t, cat in all_tasks:
        data_arr = []
        for staff in staff_list:
            # 신규 방식(고유 키)을 먼저 찾고, 없으면 구버전(단순 이름)으로 찾음
            val = daily_dict.get(staff, {}).get(unique_key, daily_dict.get(staff, {}).get(t, 0))
            data_arr.append(val if val else 0)
        
        # 값이 하나라도 있는지 확인
        if any(data_arr):
            daily_datasets.append({
                "label": f"[{cat}] {t}",
                "data": data_arr,
                "backgroundColor": task_colors[unique_key]
            })

    # 누계 차트 데이터
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

    # ------------------ 업무별 차트 데이터 (신규) ------------------
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

    task_daily_datasets = [{"label": "일일 합계", "data": task_daily_totals, "backgroundColor": task_bar_colors}]
    task_monthly_datasets = [{"label": "누적 합계", "data": task_monthly_totals, "backgroundColor": task_bar_colors}]

    # ------------------ QuickChart 대체 이미지 생성 ------------------
    # JS 실행이 차단된 모바일 뷰어를 위한 정적 Base64 이미지
    qc_daily_config = {
        "type": "bar",
        "data": { "labels": staff_list, "datasets": daily_datasets },
        "options": {
            "plugins": {
                "legend": { "display": False },
                "datalabels": { "color": "white", "font": { "weight": "bold", "size": 11 } }
            },
            "scales": {
                "x": { "stacked": True },
                "y": { "stacked": True }
            }
        }
    }
    daily_b64 = get_quickchart_b64(qc_daily_config)

    qc_monthly_config = {
        "type": "bar",
        "data": { "labels": staff_list, "datasets": monthly_datasets },
        "options": {
            "plugins": {
                "legend": { "display": False },
                "datalabels": { "color": "white", "font": { "weight": "bold", "size": 11 } }
            },
            "scales": {
                "x": { "stacked": True },
                "y": { "stacked": True }
            }
        }
    }
    monthly_b64 = get_quickchart_b64(qc_monthly_config)

    qc_task_daily_config = {
        "type": "bar",
        "data": { "labels": task_labels, "datasets": task_daily_datasets },
        "options": {
            "plugins": {
                "legend": { "display": False },
                "datalabels": { "color": "#4b5563", "anchor": "end", "align": "top", "font": { "weight": "bold", "size": 11 } }
            },
            "scales": { "y": { "beginAtZero": True } },
            "layout": { "padding": { "top": 20 } }
        }
    }
    task_daily_b64 = get_quickchart_b64(qc_task_daily_config)

    qc_task_monthly_config = {
        "type": "bar",
        "data": { "labels": task_labels, "datasets": task_monthly_datasets },
        "options": {
            "plugins": {
                "legend": { "display": False },
                "datalabels": { "color": "#4b5563", "anchor": "end", "align": "top", "font": { "weight": "bold", "size": 11 } }
            },
            "scales": { "y": { "beginAtZero": True } },
            "layout": { "padding": { "top": 20 } }
        }
    }
    task_monthly_b64 = get_quickchart_b64(qc_task_monthly_config)

    # ------------------ 통합 범례(Legend) 생성 ------------------
    custom_legend_html = '<div class="custom-legend">'
    for unique_key, t, cat in all_tasks:
        color = task_colors[unique_key]
        custom_legend_html += f'<div class="legend-item"><span class="color-box" style="background-color: {color};"></span> [{cat}] {t}</div>'
    custom_legend_html += '</div>'

    # ------------------ HTML 테이블 렌더링 ------------------
    table_html = """
    <table class="report-table">
        <thead>
            <tr>
                <th rowspan="2">업무분류</th>
                <th rowspan="2">업무명</th>
    """
    for staff in staff_list:
        table_html += f'<th colspan="2">{staff}</th>'
    table_html += "</tr><tr>"
    for _ in staff_list:
        table_html += "<th>일계</th><th>누계</th>"
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

    # ------------------ 그외 업무 진행사항 렌더링 ------------------
    other_progress_html = ""
    for staff in staff_list:
        other_text = str(daily_dict.get(staff, {}).get("other_progress", "")).strip()
        if not other_text or other_text == "0":
            other_text = ""
        else:
            other_text = other_text.replace("\n", "<br>")
            
        other_progress_html += f"""
        <div class="memo-card">
            <div class="memo-card-title">{staff}</div>
            <div class="memo-card-content">{other_text}</div>
        </div>
        """

    # 메모 줄바꿈 및 리스트화
    memo_lines = [line.strip() for line in memo_content.split('\n') if line.strip()]
    memo_html = ""
    for line in memo_lines:
        memo_html += f"<li>{line}</li>"
    if not memo_html:
        memo_html = "<li>입력된 주요사항이 없습니다.</li>"

    # ------------------ 오프라인 차트 렌더링용 로컬 JS 로드 ------------------
    def get_resource_path(rel_path):
        import sys, os
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, rel_path)
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), rel_path)

    chart_js = ""
    datalabels_js = ""
    try:
        with open(get_resource_path("static/chart.min.js"), "r", encoding="utf-8") as f:
            chart_js = f.read()
        with open(get_resource_path("static/chartjs-plugin-datalabels.min.js"), "r", encoding="utf-8") as f:
            datalabels_js = f.read()
    except Exception as e:
        print("로컬 JS 라이브러리 로드 실패:", e)

    # ------------------ 전체 HTML 템플릿 ------------------
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>업무대시보드 - {date_input}</title>
    <!-- Pretendard 폰트 -->
    <link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.8/dist/web/static/pretendard.css" />
    <!-- Chart.js (오프라인 지원용 로컬 삽입) -->
    <script>{chart_js}</script>
    <script>{datalabels_js}</script>
    <style>
        :root {{
            --primary-color: #3B82F6;
            --border-color: #E5E7EB;
            --text-main: #1F2937;
            --text-muted: #6B7280;
            --bg-gray: #F9FAFB;
        }}
        body {{
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
            background-color: #f3f4f6;
            color: var(--text-main);
            margin: 0;
            padding: 40px 20px;
        }}
        .dashboard-container {{
            max-width: 1200px;
            width: 100%;
            box-sizing: border-box;
            margin: 0 auto;
            background-color: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            padding: 40px;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            border-bottom: 2px solid var(--primary-color);
            padding-bottom: 15px;
            margin-bottom: 25px;
        }}
        .title-area h1 {{
            margin: 0;
            font-size: 24px;
            color: #1a365d;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .meta-area {{
            text-align: right;
            font-size: 14px;
            color: #4b5563;
            line-height: 1.5;
        }}
        .meta-area span {{
            color: #9ca3af;
        }}
        
        /* 안내 박스 (주요사항) */
        .notice-box {{
            background-color: #F8FAF2;
            border: 1px solid #D1E5CF;
            border-radius: 8px;
            padding: 20px 25px;
            margin-bottom: 30px;
        }}
        .notice-box ul {{
            margin: 0;
            padding-left: 20px;
            color: #374151;
            line-height: 1.6;
        }}
        .notice-box li::marker {{
            color: #10B981;
        }}
        
        /* 섹션 타이틀 */
        .section-title {{
            font-size: 18px;
            font-weight: 700;
            margin: 40px 0 20px 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .section-title::before {{
            content: '';
            display: block;
            width: 4px;
            height: 20px;
            background-color: #60a5fa;
            border-radius: 2px;
        }}

        /* 차트 영역 */
        .chart-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 40px;
        }}
        .chart-card {{
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 20px;
            background: white;
            position: relative;
            min-width: 0; /* Safari Grid Canvas fix */
        }}
        .chart-title {{
            display: flex;
            justify-content: space-between;
            font-size: 15px;
            font-weight: 600;
            color: #4b5563;
            margin-bottom: 20px;
        }}
        .chart-legend-info {{
            font-size: 12px;
            font-weight: normal;
            color: #6B7280;
        }}
        .chart-container-inner {{
            position: relative;
            height: 400px;
            width: 100%;
        }}

        /* 테이블 영역 */
        .table-container {{
            overflow-x: auto;
            margin-bottom: 40px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
        }}
        .report-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            text-align: center;
        }}
        .report-table th, .report-table td {{
            border: 1px solid var(--border-color);
            padding: 10px 8px;
        }}
        .report-table th {{
            background-color: var(--bg-gray);
            color: #374151;
            font-weight: 600;
        }}
        .report-table .cat-cell {{
            font-weight: 600;
            color: #4b5563;
        }}
        .report-table .num-cell {{
            text-align: right;
            padding-right: 12px;
        }}

        /* 메모 그리드 영역 */
        .memo-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
        }}
        .memo-card {{
            border: 1px solid var(--border-color);
            border-radius: 8px;
            background-color: white;
            display: flex;
            flex-direction: column;
            min-height: 120px;
        }}
        .memo-card-title {{
            background-color: var(--bg-gray);
            padding: 10px 15px;
            font-weight: 600;
            font-size: 14px;
            color: #1e3a8a;
            border-bottom: 1px solid var(--border-color);
            border-radius: 8px 8px 0 0;
        }}
        .memo-card-content {{
            padding: 15px;
            font-size: 13px;
            color: #4b5563;
            flex-grow: 1;
            line-height: 1.5;
        }}
        
        /* 커스텀 범례 영역 */
        .custom-legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-top: 15px;
            margin-bottom: 20px;
            justify-content: center;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            font-size: 13px;
            color: #4b5563;
        }}
        .color-box {{
            width: 12px;
            height: 12px;
            border-radius: 4px;
            margin-right: 6px;
            display: inline-block;
        }}
        
        /* 모바일 대응 (반응형) */
        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}
            .dashboard-container {{
                padding: 15px;
            }}
            .header {{
                flex-direction: column;
                align-items: flex-start;
                gap: 10px;
            }}
            .meta-area {{
                text-align: left;
            }}
            .chart-grid {{
                grid-template-columns: 1fr;
            }}
            .memo-grid {{
                grid-template-columns: 1fr;
            }}
            .chart-container-inner {{
                height: 350px;
            }}
        }}
    </style>
</head>
<body>

<div class="dashboard-container">
    <!-- Header -->
    <div class="header">
        <div class="title-area">
            <h1>📋 재원점검 · 퇴원분석 통합 업무대시보드</h1>
        </div>
        <div class="meta-area">
            <span>보고일자:</span> {report_date_str}<br>
            <span>작성부서:</span> 의무기록팀
        </div>
    </div>

    <!-- 공통 주요사항 -->
    <div class="notice-box">
        <ul>
            {memo_html}
        </ul>
    </div>

    <!-- 담당자별 차트 영역 -->
    <div class="section-title">담당자별 실적 분석 (일계 vs 누계 비교)</div>
    <div class="chart-grid">
        <div class="chart-card">
            <div class="chart-title">
                <div>📅 담당자별 금일 업무 현황 (일계)</div>
            </div>
            <div class="chart-container-inner">
                {f'<img id="dailyChartFallback" src="{daily_b64}" style="width:100%; max-width:700px; display:block; margin:0 auto;" alt="금일 업무 현황 차트">' if daily_b64 else ''}
                <canvas id="dailyChart" style="display:none;"></canvas>
            </div>
        </div>
        <div class="chart-card">
            <div class="chart-title">
                <div>📈 담당자별 누적 작업 건수</div>
            </div>
            <div class="chart-container-inner">
                {f'<img id="monthlyChartFallback" src="{monthly_b64}" style="width:100%; max-width:700px; display:block; margin:0 auto;" alt="누적 작업 건수 차트">' if monthly_b64 else ''}
                <canvas id="monthlyChart" style="display:none;"></canvas>
            </div>
        </div>
    </div>
    {custom_legend_html}

    <!-- 업무별 차트 영역 -->
    <div class="section-title">업무별 실적 분석 (일계 vs 누계 합계)</div>
    <div class="chart-grid">
        <div class="chart-card">
            <div class="chart-title">
                <div>📅 업무별 금일 업무 합계 (일계)</div>
            </div>
            <div class="chart-container-inner">
                {f'<img id="taskDailyChartFallback" src="{task_daily_b64}" style="width:100%; max-width:700px; display:block; margin:0 auto;" alt="업무별 금일 업무 합계 차트">' if task_daily_b64 else ''}
                <canvas id="taskDailyChart" style="display:none;"></canvas>
            </div>
        </div>
        <div class="chart-card">
            <div class="chart-title">
                <div>📈 업무별 누적 작업 합계</div>
            </div>
            <div class="chart-container-inner">
                {f'<img id="taskMonthlyChartFallback" src="{task_monthly_b64}" style="width:100%; max-width:700px; display:block; margin:0 auto;" alt="업무별 누적 작업 합계 차트">' if task_monthly_b64 else ''}
                <canvas id="taskMonthlyChart" style="display:none;"></canvas>
            </div>
        </div>
    </div>

    <!-- 테이블 영역 -->
    <div class="section-title">개별 업무 상세 실적 현황 (일계/누계 통합형)</div>
    <div class="table-container">
        {table_html}
    </div>

    <!-- 그외 업무 진행사항 -->
    <div class="section-title">담당자별 그외 업무 진행사항</div>
    <div class="memo-grid">
        {other_progress_html}
    </div>
</div>

<script>
    if (typeof Chart !== 'undefined') {{
        const dfb = document.getElementById('dailyChartFallback');
        if (dfb) dfb.style.display = 'none';
        document.getElementById('dailyChart').style.display = 'block';

        const mfb = document.getElementById('monthlyChartFallback');
        if (mfb) mfb.style.display = 'none';
        document.getElementById('monthlyChart').style.display = 'block';

        const tdfb = document.getElementById('taskDailyChartFallback');
        if (tdfb) tdfb.style.display = 'none';
        document.getElementById('taskDailyChart').style.display = 'block';

        const tmfb = document.getElementById('taskMonthlyChartFallback');
        if (tmfb) tmfb.style.display = 'none';
        document.getElementById('taskMonthlyChart').style.display = 'block';

        Chart.register(ChartDataLabels);

        const staffList = {json.dumps(staff_list, ensure_ascii=False)};
        const taskLabels = {json.dumps(task_labels, ensure_ascii=False)};
        
        // 일계 차트 (누적 막대)
        const ctxDaily = document.getElementById('dailyChart').getContext('2d');
    new Chart(ctxDaily, {{
        type: 'bar',
        data: {{
            labels: staffList,
            datasets: {json.dumps(daily_datasets, ensure_ascii=False)}
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ display: false }},
                datalabels: {{
                    color: 'white',
                    font: {{ weight: 'bold', size: 11 }},
                    formatter: function(value, context) {{
                        if (!value || value === 0) return '';
                        return value + '건';
                    }}
                }}
            }},
            scales: {{
                x: {{ stacked: true, grid: {{ display: false }} }},
                y: {{ stacked: true }}
            }}
        }}
    }});

    // 누계 차트 (누적 막대)
    const ctxMonthly = document.getElementById('monthlyChart').getContext('2d');
    new Chart(ctxMonthly, {{
        type: 'bar',
        data: {{
            labels: staffList,
            datasets: {json.dumps(monthly_datasets, ensure_ascii=False)}
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ display: false }},
                datalabels: {{
                    color: 'white',
                    font: {{ weight: 'bold', size: 11 }},
                    formatter: function(value, context) {{
                        if (!value || value === 0) return '';
                        return value.toLocaleString() + '건';
                    }}
                }}
            }},
            scales: {{
                x: {{ stacked: true, grid: {{ display: false }} }},
                y: {{ stacked: true }}
            }}
        }}
    }});

    // 업무별 일계 차트
    const ctxTaskDaily = document.getElementById('taskDailyChart').getContext('2d');
    new Chart(ctxTaskDaily, {{
        type: 'bar',
        data: {{
            labels: taskLabels,
            datasets: {json.dumps(task_daily_datasets, ensure_ascii=False)}
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ display: false }},
                datalabels: {{
                    color: '#4b5563',
                    anchor: 'end',
                    align: 'top',
                    font: {{ weight: 'bold', size: 11 }},
                    formatter: function(value, context) {{
                        if (!value || value === 0) return '';
                        return value + '건';
                    }}
                }}
            }},
            scales: {{
                x: {{ grid: {{ display: false }} }},
                y: {{ beginAtZero: true }}
            }},
            layout: {{
                padding: {{ top: 20 }}
            }}
        }}
    }});

    // 업무별 누계 차트
    const ctxTaskMonthly = document.getElementById('taskMonthlyChart').getContext('2d');
    new Chart(ctxTaskMonthly, {{
        type: 'bar',
        data: {{
            labels: taskLabels,
            datasets: {json.dumps(task_monthly_datasets, ensure_ascii=False)}
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ display: false }},
                datalabels: {{
                    color: '#4b5563',
                    anchor: 'end',
                    align: 'top',
                    font: {{ weight: 'bold', size: 11 }},
                    formatter: function(value, context) {{
                        if (!value || value === 0) return '';
                        return value.toLocaleString() + '건';
                    }}
                }}
            }},
            scales: {{
                x: {{ grid: {{ display: false }} }},
                y: {{ beginAtZero: true }}
            }},
            layout: {{
                padding: {{ top: 20 }}
            }}
        }}
    }});
    }}
</script>
</body>
</html>
"""

    prefix = "미리보기_" if is_preview else "대시보드_"
    out_file = os.path.join(target_dir, f"{prefix}{file_date}.html")
    try:
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        import sys
        if sys.platform == "win32":
            os.startfile(os.path.abspath(out_file))
        else:
            import urllib.request
            uri = "file://" + urllib.request.pathname2url(os.path.abspath(out_file))
            webbrowser.open(uri)
        return out_file, None
    except Exception as e:
        return None, str(e)

# --- End HTML Export Code ---


# --- 네트워크 유틸리티 ---
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

# --- 동시성 제어 유틸리티 ---
class FileLock:
    def __init__(self, filepath, timeout=5):
        self.filepath = filepath
        self.lockfile = filepath + ".lock"
        self.timeout = timeout

    def __enter__(self):
        start = time.time()
        # 폴더가 없으면 생성 (Errno 2 방지)
        os.makedirs(os.path.dirname(self.lockfile), exist_ok=True)
        while True:
            try:
                # 원자적 생성으로 동시 접근 차단
                fd = os.open(self.lockfile, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
                break
            except FileExistsError:
                if time.time() - start > self.timeout:
                    raise TimeoutError(f"파일 잠금 대기 시간 초과: 다른 사용자가 사용 중일 수 있습니다.\n({self.filepath})")
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

# 1. 고정 설정 (로컬 테스트용 폴더 경로 및 부서원 리스트)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "backup/config.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"LOCAL_BASE_PATH": ""}

config = load_config()
LOCAL_BASE_PATH = config.get("LOCAL_BASE_PATH", "")

LAST_USER_FILE = os.path.join(BASE_DIR, "last_user.txt")

if LOCAL_BASE_PATH:
    STAFF_MASTER_FILE = os.path.join(LOCAL_BASE_PATH, "master/staff_master.json")
    TASK_MASTER_FILE = os.path.join(LOCAL_BASE_PATH, "master/task_master.json")
else:
    STAFF_MASTER_FILE = ""
    TASK_MASTER_FILE = ""

def load_staff_list():
    default_staff = [
        "이지연", "신준호", "박선우", "박유진", "박연정",
        "이재희", "김정현", "이윤혜", "박민영"
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
        print(f"마스터 파일 로드 실패: {e}")
        
    try:
        safe_write_json(STAFF_MASTER_FILE, default_staff)
    except Exception as e:
        print(f"마스터 파일 생성 실패: {e}")
    return default_staff

STAFF_LIST = load_staff_list()


def load_task_list():
    default_tasks = {
        "퇴원": [
            "퇴원분석",
            "pathology 확인",
            "미비정리"
        ],
        "재원": [
            "특수서식",
            "경과기록",
            "미비정리"
        ],
        "차트검수": [
            "차트검수"
        ],
        "모니터링": [
            "외래",
            "응급",
            "입원"
        ],
        "코딩": [
            "진코딩",
            "가코딩"
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
        print(f"세부 업무 마스터 파일 로드 실패: {e}")
        
    try:
        safe_write_json(TASK_MASTER_FILE, default_tasks)
    except Exception as e:
        print(f"세부 업무 마스터 파일 생성 실패: {e}")
    return default_tasks

TASK_CATEGORIES = load_task_list()


class WorkLogApp:
    def __init__(self, root):
        self.root = root
        self.root.title("재원점검 퇴원분석 업무일지")
        self.root.geometry("1000x950")

        if not LOCAL_BASE_PATH or not os.path.exists(LOCAL_BASE_PATH):
            self.root.withdraw()
            if not LOCAL_BASE_PATH:
                messagebox.showwarning("필수 설정 안내", "최초 실행 시 데이터 적재 폴더(공유 폴더) 설정이 필요합니다.\n설정을 완료해야 프로그램을 사용할 수 있습니다.")
            else:
                messagebox.showerror("접속 오류", f"설정된 폴더와 연결되지 않았습니다.\n접속을 확인해주세요.\n\n경로: {LOCAL_BASE_PATH}")
                
            self.settings_window = SettingsWindow(self)
            self.root.wait_window(self.settings_window.top)
            
            if not LOCAL_BASE_PATH or not os.path.exists(LOCAL_BASE_PATH):
                self.root.destroy()
                return
                
            global STAFF_LIST, TASK_CATEGORIES
            STAFF_LIST = load_staff_list()
            TASK_CATEGORIES = load_task_list()
            self.root.deiconify()

        self.entries = {}
        self.create_widgets()
        
        # macOS 복사/붙여넣기 단축키 지원 (Command+C, Command+V 등)
        self.root.bind_class("Text", "<Command-c>", lambda event: event.widget.event_generate("<<Copy>>"))
        self.root.bind_class("Text", "<Command-v>", lambda event: event.widget.event_generate("<<Paste>>"))
        self.root.bind_class("Text", "<Command-x>", lambda event: event.widget.event_generate("<<Cut>>"))
        self.root.bind_class("Text", "<Command-a>", lambda event: event.widget.tag_add("sel", "1.0", "end"))
        
        self.root.bind_class("Entry", "<Command-c>", lambda event: event.widget.event_generate("<<Copy>>"))
        self.root.bind_class("Entry", "<Command-v>", lambda event: event.widget.event_generate("<<Paste>>"))
        self.root.bind_class("Entry", "<Command-x>", lambda event: event.widget.event_generate("<<Cut>>"))
        self.root.bind_class("Entry", "<Command-a>", lambda event: event.widget.selection_range(0, "end"))

        # 우클릭 메뉴 설정
        self.setup_context_menu()

    def setup_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="복사 (Copy)", command=self.copy_text)
        self.context_menu.add_command(label="붙여넣기 (Paste)", command=self.paste_text)
        self.context_menu.add_command(label="잘라내기 (Cut)", command=self.cut_text)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="전체 선택 (Select All)", command=self.select_all_text)

        self.root.bind_class("Text", "<Button-3>", self.show_context_menu)
        self.root.bind_class("Entry", "<Button-3>", self.show_context_menu)
        # Mac 트랙패드 보조 클릭용
        self.root.bind_class("Text", "<Button-2>", self.show_context_menu)
        self.root.bind_class("Entry", "<Button-2>", self.show_context_menu)

    def show_context_menu(self, event):
        event.widget.focus_set()
        self.current_widget = event.widget
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def copy_text(self):
        if hasattr(self, 'current_widget') and self.current_widget:
            try:
                self.current_widget.event_generate("<<Copy>>")
            except tk.TclError:
                pass

    def paste_text(self):
        if hasattr(self, 'current_widget') and self.current_widget:
            try:
                self.current_widget.event_generate("<<Paste>>")
            except tk.TclError:
                pass

    def cut_text(self):
        if hasattr(self, 'current_widget') and self.current_widget:
            try:
                self.current_widget.event_generate("<<Cut>>")
            except tk.TclError:
                pass

    def select_all_text(self):
        if hasattr(self, 'current_widget') and self.current_widget:
            if isinstance(self.current_widget, tk.Text):
                self.current_widget.tag_add("sel", "1.0", "end")
            else:
                self.current_widget.selection_range(0, "end")

    def validate_number(self, value_if_allowed):
        if value_if_allowed == "":
            return True
        try:
            int(value_if_allowed)
            return True
        except ValueError:
            return False

    def create_widgets(self):
        # 상단 타이틀
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill="x", pady=10)
        title_label = tk.Label(top_frame, text="재원점검 퇴원분석 업무일지", font=("Arial", 16, "bold"))
        title_label.pack(side="left", padx=20)

        settings_btn = tk.Button(top_frame, text="환경설정", command=self.open_settings)
        settings_btn.pack(side="right", padx=20)

        # ------------------ 기본 정보 입력 구역 ------------------
        info_frame = tk.LabelFrame(self.root, text="일자 / 사용자 선택", padx=10, pady=10)
        info_frame.pack(fill="x", padx=20, pady=5)

        inner_frame = tk.Frame(info_frame)
        inner_frame.pack(fill="x")

        # 날짜 설정 (기본값: 오늘)
        lbl_text = "작업 날짜:" if HAS_TKCALENDAR else "작업 날짜:"
        tk.Label(inner_frame, text=lbl_text).pack(side="left", padx=(0, 5))
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        
        if HAS_TKCALENDAR:
            self.date_entry = DateEntry(inner_frame, textvariable=self.date_var, date_pattern='yyyy-mm-dd', 
                                        width=13, background='darkblue', foreground='white', borderwidth=2)
            self.date_entry.pack(side="left", padx=(0, 20))
        else:
            self.date_entry = tk.Entry(inner_frame, textvariable=self.date_var, width=15)
            self.date_entry.pack(side="left", padx=(0, 5))
            tk.Label(inner_frame, text=" (형식: YYYY-MM-DD)").pack(side="left")
            
            # tkcalendar 미설치 안내 라벨
            tk.Label(inner_frame, text="*달력을 쓰려면 pip install tkcalendar 필요", fg="gray", font=("Arial", 9)).pack(side="left", padx=(5, 20))

        # 담당자 선택 드롭다운
        tk.Label(inner_frame, text="담당자 선택:").pack(side="left", padx=(0, 5))
        self.staff_combo = ttk.Combobox(inner_frame, values=STAFF_LIST, state="readonly", width=13)
        self.staff_combo.pack(side="left")
        
        last_user = "선택하세요"
        if os.path.exists(LAST_USER_FILE):
            try:
                with open(LAST_USER_FILE, "r", encoding="utf-8") as f:
                    saved_user = f.read().strip()
                    if saved_user in STAFF_LIST:
                        last_user = saved_user
            except:
                pass
        self.staff_combo.set(last_user)

        # ------------------ 메모 입력 구역 (공통 주요사항) ------------------
        memo_frame = tk.LabelFrame(self.root, padx=10, pady=5)
        memo_frame.pack(fill="x", padx=20, pady=5)
        
        memo_header = tk.Frame(memo_frame, width=930, height=25)
        memo_header.pack_propagate(False)
        tk.Label(memo_header, text="공통 주요사항 (해당 일자 부서 전체 공유)").pack(side="left")
        
        sep = ttk.Separator(memo_header, orient="horizontal")
        sep.pack(side="left", fill="x", expand=True, padx=5)

        tk.Button(memo_header, text="저장하기", command=self.save_memo, font=("Arial", 9)).pack(side="right", padx=2)
        tk.Button(memo_header, text="불러오기", command=self.load_memo, font=("Arial", 9)).pack(side="right", padx=2)
        memo_frame.config(labelwidget=memo_header)

        self.memo_text = tk.Text(memo_frame, height=3, width=50)
        self.memo_text.pack(fill="both", expand=True)

        # ------------------ 업무 실적 입력 구역 ------------------
        fields_frame = tk.LabelFrame(self.root, text="세부 업무 실적 (일계 건수 입력)", padx=10, pady=10)
        fields_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # 좌측: 세부업무 리스트 (스크롤 지원)
        tasks_container = tk.Frame(fields_frame)
        tasks_container.pack(side="left", fill="both", expand=True)

        # 스크롤 가능한 영역 만들기
        canvas = tk.Canvas(tasks_container, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(tasks_container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 실적 입력 필드 배치 (카테고리별로 렌더링)
        vcmd = (self.root.register(self.validate_number), '%P')
        current_row = 0
        self.entry_list = []

        for category, fields in TASK_CATEGORIES.items():
            # 카테고리 묶음 박스 (테두리 없음, 밝은 배경색)
            cat_box = tk.Frame(self.scrollable_frame, bg="#F5F7FA", bd=0, padx=10, pady=10)
            cat_box.grid(row=current_row, column=0, padx=10, pady=5, sticky="we")
            current_row += 1

            # 카테고리 헤더 (좌측 배치)
            cat_lbl = tk.Label(cat_box, text=f"[{category}]", font=("Arial", 13, "bold"), fg="#222222", bg="#F5F7FA", width=12, anchor="nw")
            cat_lbl.grid(row=0, column=0, rowspan=max(1, len(fields)), padx=(5, 10), pady=2, sticky="nw")

            # 세로선 (구분선) 추가
            separator = tk.Frame(cat_box, width=1, bg="#D0D0D0")
            separator.grid(row=0, column=1, rowspan=max(1, len(fields)), sticky="ns", padx=(0, 15), pady=2)

            for idx, field in enumerate(fields):
                lbl = tk.Label(cat_box, text=field, width=18, anchor="w", bg="#F5F7FA")
                lbl.grid(row=idx, column=2, padx=(0, 10), pady=2, sticky="w")

                entry = tk.Entry(cat_box, width=12, justify="right", validate="key", validatecommand=vcmd)
                entry.insert(0, "0")  # 기본값 0
                entry.grid(row=idx, column=3, padx=5, pady=2)
                
                unique_key = f"{category}_{field}"
                self.entries[unique_key] = entry
                self.entry_list.append(entry)

        # 엔터 키 입력 시 다음 필드로 이동 및 텍스트 전체 선택
        def focus_next_entry(event, index):
            if index + 1 < len(self.entry_list):
                next_entry = self.entry_list[index + 1]
                next_entry.focus_set()
                next_entry.select_range(0, tk.END)
                next_entry.icursor(tk.END)
            return "break"

        for i, entry in enumerate(self.entry_list):
            entry.bind("<Return>", lambda e, idx=i: focus_next_entry(e, idx))

        # 우측: 그외 업무 진행사항
        other_frame = tk.Frame(fields_frame)
        other_frame.pack(side="right", fill="both", expand=True, padx=(15, 0))

        other_lbl = tk.Label(other_frame, text="[그외 업무 진행사항]", font=("Arial", 11, "bold"), fg="#333333")
        other_lbl.pack(anchor="nw", pady=(0, 5))

        self.other_progress_text = tk.Text(other_frame, width=30)
        self.other_progress_text.pack(fill="both", expand=True)

        # 이벤트 바인딩 (자동 불러오기)
        self.staff_combo.bind("<<ComboboxSelected>>", self.load_data)
        if HAS_TKCALENDAR:
            self.date_entry.bind("<<DateEntrySelected>>", self.load_data)
        self.date_entry.bind("<FocusOut>", self.load_data)
        self.date_entry.bind("<Return>", self.load_data)
        
        # 앱 시작 시 오늘 날짜 공통 메모 로드
        self.load_data()

        # ------------------ 하단 버튼 구역 ------------------
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", padx=20, pady=15)

        # 불러오기 버튼
        refresh_btn = tk.Button(btn_frame, text="최신 데이터 불러오기", font=("Arial", 11),
                                width=22, command=self.refresh_data)
        refresh_btn.pack(side="left", padx=5, expand=True)

        # 저장 버튼 (개별 PC용)
        save_btn = tk.Button(btn_frame, text="내 실적 저장하기", font=("Arial", 11),
                             width=22, command=self.save_data)
        save_btn.pack(side="left", padx=5, expand=True)

        # 미리보기 버튼
        preview_btn = tk.Button(btn_frame, text="미리보기", font=("Arial", 11),
                                width=22, command=self.preview_html)
        preview_btn.pack(side="left", padx=5, expand=True)



    def refresh_data(self):
        self.load_data()
        self.load_memo(silent=True)
        messagebox.showinfo("불러오기 완료", "서버(폴더)에 저장된 최신 데이터를 성공적으로 불러왔습니다.\n(공통 주요사항 및 본인 실적 갱신)")

    def save_data(self):
        user_name = self.staff_combo.get()
        if user_name == "선택하세요":
            messagebox.showwarning("경고", "담당자를 선택해 주세요.")
            return

        date_input = self.date_var.get().strip()
        try:
            # 날짜 형식 검증 및 변환
            date_obj = datetime.strptime(date_input, "%Y-%m-%d")
            folder_month = date_obj.strftime("%Y-%m")  # YYYY-MM
            file_date = date_obj.strftime("%Y%m%d")  # YYYYMMDD
        except ValueError:
            messagebox.showerror("오류", "날짜 형식이 올바르지 않습니다. (YYYY-MM-DD)")
            return

        # 현재 UI 데이터 읽기
        task_data = {}
        for category, fields in TASK_CATEGORIES.items():
            for field in fields:
                unique_key = f"{category}_{field}"
                if unique_key in self.entries:
                    val = self.entries[unique_key].get().strip()
                    task_data[unique_key] = int(val) if val.isdigit() else 0

        # 로컬 경로 생성 (월별로 폴더 분할 관리)
        target_dir = os.path.join(LOCAL_BASE_PATH, folder_month)
        try:
            os.makedirs(target_dir, exist_ok=True)
        except Exception as e:
            messagebox.showerror("경로 오류", f"로컬 폴더를 생성하거나 접근할 수 없습니다.\n{e}")
            return

        # 파일명 정의 (예: 20260702_김성진.json)
        file_name = f"{file_date}_{user_name}.json"
        file_path = os.path.join(target_dir, file_name)

        # 기존 데이터가 있다면 히스토리에 추가하기 위해 읽어옴
        history = []
        if os.path.exists(file_path):
            try:
                old_data = safe_read_json(file_path)
                if old_data:
                    history = old_data.get("history", [])
                    # 이전 상태 기록 (history 자기 자신은 제외)
                    old_state = {k: v for k, v in old_data.items() if k != "history"}
                    history.append(old_state)
            except:
                pass

        # 데이터 저장 구조 정의 (히스토리 포함)
        payload = {
            "date": date_input,
            "name": user_name,
            "tasks": task_data,
            "other_progress": self.other_progress_text.get("1.0", tk.END).strip(),
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ip": get_local_ip(),
            "history": history
        }

        try:
            safe_write_json(file_path, payload)
                
            # 마지막 사용 담당자 기억
            try:
                safe_write_text(LAST_USER_FILE, user_name)
            except:
                pass
                
            messagebox.showinfo("저장 성공", f"{user_name}님의 {date_input} 실적이 저장되었습니다.\n\n저장 위치:\n{file_path}")
        except Exception as e:
            messagebox.showerror("저장 실패", f"파일 저장 중 오류가 발생했습니다: {e}")

    def preview_html(self):
        try:
            import importlib
        except Exception:
            pass

        date_input = self.date_var.get().strip()
        try:
            date_obj = datetime.strptime(date_input, "%Y-%m-%d")
            folder_month = date_obj.strftime("%Y-%m")
            file_date = date_obj.strftime("%Y%m%d")
        except ValueError:
            messagebox.showerror("오류", "날짜 형식이 올바르지 않습니다. (YYYY-MM-DD)")
            return

        target_dir = os.path.join(LOCAL_BASE_PATH, folder_month)
        os.makedirs(target_dir, exist_ok=True)
        
        file_pattern = os.path.join(target_dir, "*.json")
        json_files = glob.glob(file_pattern)

        all_rows = []
        for file_path in json_files:
            try:
                data = safe_read_json(file_path)
                if data:
                    row = {"일자": data.get("date", ""), "담당자": data.get("name", ""), "other_progress": data.get("other_progress", "")}
                    tasks = data.get("tasks", {})
                    migrated_tasks = {}
                    for category, fields in TASK_CATEGORIES.items():
                        for field in fields:
                            unique_key = f"{category}_{field}"
                            migrated_tasks[unique_key] = tasks.get(unique_key, tasks.get(field, 0))
                    row.update(migrated_tasks)
                    all_rows.append(row)
            except Exception as e:
                pass

        # 현재 UI 데이터 읽기 (저장하지 않음)
        user_name = self.staff_combo.get()
        if user_name != "선택하세요":
            task_data = {}
            for category, fields in TASK_CATEGORIES.items():
                for field in fields:
                    unique_key = f"{category}_{field}"
                    if unique_key in self.entries:
                        val = self.entries[unique_key].get().strip()
                        task_data[unique_key] = int(val) if val.isdigit() else 0
            
            ui_row = {"일자": date_input, "담당자": user_name, "other_progress": self.other_progress_text.get("1.0", tk.END).strip()}
            ui_row.update(task_data)
            
            # 덮어쓰기 로직: 일자와 담당자가 동일한 행이 있다면 업데이트, 아니면 추가
            replaced = False
            for i, r in enumerate(all_rows):
                if r.get("일자") == date_input and r.get("담당자") == user_name:
                    all_rows[i] = ui_row
                    replaced = True
                    break
            if not replaced:
                all_rows.append(ui_row)

        if not all_rows:
            messagebox.showinfo("안내", "유효한 데이터가 없습니다.")
            return

        df_all = pd.DataFrame(all_rows)

        # 라이브 마스터 리스트와 실제 데이터 사용자 통합 및 정렬
        current_staff_master = load_staff_list()
        all_unique_users = df_all["담당자"].unique().tolist()
        ordered_users = current_staff_master + [u for u in all_unique_users if u not in current_staff_master]

        # 1. 데일리 취합 요약 (선택한 날짜 기준)
        df_daily = df_all[df_all["일자"] == date_input].copy()
        df_daily.set_index("담당자", inplace=True)
        df_daily = df_daily.reindex(ordered_users)
        df_daily.index.name = "담당자"
        df_daily.reset_index(inplace=True)
        for col in df_daily.columns:
            if col in ["일자", "담당자", "other_progress"]:
                df_daily[col] = df_daily[col].fillna("")
            else:
                df_daily[col] = df_daily[col].fillna(0)

        # 2. 월간 취합 요약 (해당 월 전체)
        if "일자" in df_all.columns:
            df_monthly_base = df_all.drop(columns=["일자"])
        else:
            df_monthly_base = df_all
            
        # 3. HTML 생성용 딕셔너리 준비
        daily_dict = df_daily.set_index("담당자").to_dict('index')
        monthly_dict = df_monthly_base.groupby("담당자").sum(numeric_only=True).to_dict('index')

        # 4. 공통 메모 로드 (현재 UI에 적힌 메모 우선 적용)
        memo_content = self.memo_text.get("1.0", tk.END).strip()
        if not memo_content:
            memo_path = os.path.join(target_dir, f"{file_date}_memo.txt")
            if os.path.exists(memo_path):
                try:
                    with open(memo_path, 'r', encoding='utf-8') as f:
                        memo_content = f.read()
                except:
                    pass

        html_target_dir = os.path.join(LOCAL_BASE_PATH, "html report", folder_month, date_input)
        os.makedirs(html_target_dir, exist_ok=True)
        
        self.root.config(cursor="watch")
        self.root.update_idletasks()
        
        def run_report():
            try:
                out_file, err = generate_html_report(date_input, html_target_dir, daily_dict, monthly_dict, memo_content, ordered_users, TASK_CATEGORIES, is_preview=True)
                self.root.after(0, finish_report, out_file, err)
            except Exception as e:
                self.root.after(0, finish_report, None, str(e))
                
        def finish_report(out_file, err):
            self.root.config(cursor="")
            if err:
                messagebox.showerror("미리보기 실패", f"미리보기 생성 중 오류가 발생했습니다: {err}")
                
        import threading
        threading.Thread(target=run_report, daemon=True).start()

    def load_data(self, event=None):
        date_input = self.date_var.get().strip()
        user_name = self.staff_combo.get()
        
        try:
            date_obj = datetime.strptime(date_input, "%Y-%m-%d")
            folder_month = date_obj.strftime("%Y-%m")
            file_date = date_obj.strftime("%Y%m%d")
        except ValueError:
            return
            
        target_dir = os.path.join(LOCAL_BASE_PATH, folder_month)
        
        # 공통 메모 로드 (silent 모드로)
        self.load_memo(silent=True)
                
        # 담당자별 데이터 로드
        if user_name != "선택하세요":
            # 폼 초기화
            for entry in self.entries.values():
                entry.delete(0, tk.END)
                entry.insert(0, "0")
            self.other_progress_text.delete("1.0", tk.END)
            
            file_path = os.path.join(target_dir, f"{file_date}_{user_name}.json")
            if os.path.exists(file_path):
                try:
                    data = safe_read_json(file_path)
                    if data:
                        tasks = data.get("tasks", {})
                        for category, fields in TASK_CATEGORIES.items():
                            for field in fields:
                                unique_key = f"{category}_{field}"
                                val = tasks.get(unique_key, tasks.get(field, 0))
                                if unique_key in self.entries:
                                    self.entries[unique_key].delete(0, tk.END)
                                    self.entries[unique_key].insert(0, str(val))
                        other_progress = data.get("other_progress", "")
                        if other_progress:
                            self.other_progress_text.insert("1.0", other_progress)
                except:
                    pass

    def load_memo(self, silent=False):
        date_input = self.date_var.get().strip()
        try:
            date_obj = datetime.strptime(date_input, "%Y-%m-%d")
            folder_month = date_obj.strftime("%Y-%m")
            file_date = date_obj.strftime("%Y%m%d")
        except ValueError:
            if not silent: messagebox.showerror("오류", "날짜 형식이 올바르지 않습니다.")
            return

        target_dir = os.path.join(LOCAL_BASE_PATH, folder_month)
        memo_path = os.path.join(target_dir, f"{file_date}_memo.txt")
        
        self.memo_text.delete("1.0", tk.END)
        if os.path.exists(memo_path):
            try:
                memo_content = safe_read_text(memo_path)
                if memo_content:
                    self.memo_text.insert("1.0", memo_content.strip())
                if not silent: messagebox.showinfo("불러오기 완료", "공통 주요사항을 성공적으로 불러왔습니다.")
            except Exception as e:
                if not silent: messagebox.showerror("오류", f"메모 불러오기 실패: {e}")
        else:
            if not silent: messagebox.showinfo("안내", "해당 날짜에 저장된 공통 주요사항이 없습니다.")

    def save_memo(self):
        date_input = self.date_var.get().strip()
        try:
            date_obj = datetime.strptime(date_input, "%Y-%m-%d")
            folder_month = date_obj.strftime("%Y-%m")
            file_date = date_obj.strftime("%Y%m%d")
        except ValueError:
            messagebox.showerror("오류", "날짜 형식이 올바르지 않습니다.")
            return

        target_dir = os.path.join(LOCAL_BASE_PATH, folder_month)
        os.makedirs(target_dir, exist_ok=True)
        
        memo_path = os.path.join(target_dir, f"{file_date}_memo.txt")
        try:
            safe_write_text(memo_path, self.memo_text.get("1.0", tk.END).strip())
            messagebox.showinfo("저장 성공", "공통 주요사항이 성공적으로 저장되었습니다.")
        except Exception as e:
            messagebox.showerror("저장 실패", f"메모 저장 중 오류가 발생했습니다: {e}")

    def merge_to_excel(self):
        date_input = self.date_var.get().strip()
        try:
            date_obj = datetime.strptime(date_input, "%Y-%m-%d")
            folder_month = date_obj.strftime("%Y-%m")
            file_date = date_obj.strftime("%Y%m%d")
        except ValueError:
            messagebox.showerror("오류", "날짜 형식이 올바르지 않습니다. (YYYY-MM-DD)")
            return

        target_dir = os.path.join(LOCAL_BASE_PATH, folder_month)
        # 월 전체 데이터 로드
        file_pattern = os.path.join(target_dir, "*.json")
        json_files = glob.glob(file_pattern)

        if not json_files:
            messagebox.showinfo("안내", f"{folder_month} 월에 저장된 데이터가 없습니다.")
            return

        all_rows = []
        for file_path in json_files:
            try:
                data = safe_read_json(file_path)
                if data:
                    row = {"일자": data.get("date", ""), "담당자": data.get("name", ""), "other_progress": data.get("other_progress", "")}
                    tasks = data.get("tasks", {})
                    migrated_tasks = {}
                    for category, fields in TASK_CATEGORIES.items():
                        for field in fields:
                            unique_key = f"{category}_{field}"
                            migrated_tasks[unique_key] = tasks.get(unique_key, tasks.get(field, 0))
                    row.update(migrated_tasks)
                    all_rows.append(row)
            except Exception as e:
                print(f"파일 로드 실패 ({file_path}): {e}")

        if not all_rows:
            messagebox.showinfo("안내", "유효한 데이터가 없습니다.")
            return

        # Pandas 변환
        df_all = pd.DataFrame(all_rows)

        # 라이브 마스터 리스트와 실제 데이터 사용자 통합 및 정렬
        current_staff_master = load_staff_list()
        all_unique_users = df_all["담당자"].unique().tolist()
        ordered_users = current_staff_master + [u for u in all_unique_users if u not in current_staff_master]

        # 1. 데일리 취합 요약 (선택한 날짜 기준)
        df_daily = df_all[df_all["일자"] == date_input].copy()
        df_daily.set_index("담당자", inplace=True)
        df_daily = df_daily.reindex(ordered_users)
        df_daily.index.name = "담당자"
        df_daily.reset_index(inplace=True)
        df_daily["일자"] = df_daily["일자"].fillna(date_input)
        for col in df_daily.columns:
            if col in ["일자", "담당자", "other_progress"]:
                df_daily[col] = df_daily[col].fillna("")
            else:
                df_daily[col] = df_daily[col].fillna(0)

        # 2. 월간 취합 요약 (해당 월 전체 담당자별 합계)
        if "일자" in df_all.columns:
            df_monthly_base = df_all.drop(columns=["일자"])
        else:
            df_monthly_base = df_all
            
        df_monthly = df_monthly_base.groupby("담당자").sum(numeric_only=True)
        df_monthly = df_monthly.reindex(ordered_users)
        df_monthly.index.name = "담당자"
        df_monthly.reset_index(inplace=True)
        for col in df_monthly.columns:
            if col in ["담당자"]:
                df_monthly[col] = df_monthly[col].fillna("")
            else:
                df_monthly[col] = df_monthly[col].fillna(0)

        # 3. Summary 탭용 딕셔너리 준비
        daily_dict = df_daily.set_index("담당자").to_dict('index')
        monthly_dict = df_monthly_base.groupby("담당자").sum(numeric_only=True).to_dict('index')

        # 월간 요약에도 부서 총합 추가
        monthly_task_cols = [col for col in df_monthly.columns if col != "담당자"]
        m_total_row = {col: df_monthly[col].sum() for col in monthly_task_cols}
        m_total_row["담당자"] = "월간 부서 총합"
        df_monthly_with_total = pd.concat([df_monthly, pd.DataFrame([m_total_row])], ignore_index=True)

        # Excel 저장 경로 설정 (로컬 내부에 바로 생성)
        excel_name = f"업무일지_취합_{folder_month}.xlsx"
        excel_path = os.path.join(target_dir, excel_name)

        try:
            with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
                # Summary 탭을 해당 날짜로 생성하여 첫 번째 탭으로 만듦
                pd.DataFrame().to_excel(writer, sheet_name=date_input, header=False, index=False)
                df_monthly_with_total.to_excel(writer, sheet_name="월간 요약", index=False)
                
                workbook = writer.book
                worksheet = writer.sheets[date_input]
                
                # ==========================
                # 커스텀 Summary 시트 작성
                # ==========================
                fmt_title = workbook.add_format({'bold': True, 'font_size': 18})
                fmt_subtitle = workbook.add_format({'bold': True, 'font_size': 12})
                fmt_header_gray = workbook.add_format({'bold': True, 'bg_color': '#D9D9D9', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
                fmt_header_diag = workbook.add_format({'bold': True, 'bg_color': '#D9D9D9', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'diag_type': 1, 'diag_border': 1})
                fmt_cell = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
                fmt_category = workbook.add_format({'bg_color': '#F2F2F2', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
                fmt_task = workbook.add_format({'bg_color': '#F2F2F2', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
                fmt_val = workbook.add_format({'border': 1, 'align': 'right', 'valign': 'vcenter', 'num_format': '#,##0'})
                fmt_val_zero = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
                
                # 요일 계산
                weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
                day_str = weekdays[date_obj.weekday()]
                date_str = f"■ {date_obj.year}년 {date_obj.month}월 {date_obj.day}일 ({day_str})"
                
                worksheet.write(0, 0, "재원점검·퇴원분석 업무일지", fmt_title)
                worksheet.write(2, 0, date_str, fmt_subtitle)
                
                worksheet.set_column(0, 0, 10)
                worksheet.set_column(1, 1, 15)
                
                num_staff = len(STAFF_LIST)
                max_col = 1 + num_staff * 2
                
                # 주 요 사 항
                fmt_memo = workbook.add_format({'border': 1, 'align': 'left', 'valign': 'top', 'text_wrap': True})
                memo_content = ""
                memo_path = os.path.join(target_dir, f"{file_date}_memo.txt")
                if os.path.exists(memo_path):
                    try:
                        with open(memo_path, 'r', encoding='utf-8') as f:
                            memo_content = f.read().strip()
                    except:
                        pass
                worksheet.merge_range(4, 0, 4, max_col, "주 요 사 항", fmt_header_gray)
                worksheet.merge_range(5, 0, 8, max_col, memo_content, fmt_memo)
                    
                # 개별 업무 현황
                start_row = 10
                worksheet.merge_range(start_row, 0, start_row, max_col, "개별 업무 현황", fmt_header_gray)
                
                # 헤더 그리기
                hr1 = start_row + 1
                hr2 = start_row + 2
                worksheet.merge_range(hr1, 0, hr2, 1, "담당자               \n               업무명", fmt_header_diag)
                
                col = 2
                for staff in ordered_users:
                    worksheet.merge_range(hr1, col, hr1, col+1, staff, fmt_header_gray)
                    worksheet.write(hr2, col, "일계", fmt_header_gray)
                    worksheet.write(hr2, col+1, "누계", fmt_header_gray)
                    worksheet.set_column(col, col+1, 6)
                    col += 2
                    
                # 데이터 영역
                row = hr2 + 1
                for cat, tasks in TASK_CATEGORIES.items():
                    cat_start = row
                    for t in tasks:
                        worksheet.write(row, 1, t, fmt_task)
                        c = 2
                        for staff in ordered_users:
                            val_d = daily_dict.get(staff, {}).get(t, 0)
                            if pd.isna(val_d) or val_d == 0 or str(val_d).strip() == "":
                                worksheet.write(row, c, "-", fmt_val_zero)
                            else:
                                worksheet.write(row, c, float(val_d), fmt_val)
                                
                            val_m = monthly_dict.get(staff, {}).get(t, 0)
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
                
                # 그외 업무 진행사항
                worksheet.merge_range(row, 0, row+4, 1, "그외\n업무 진행사항", fmt_category)
                c = 2
                for staff in ordered_users:
                    other_text = daily_dict.get(staff, {}).get("other_progress", "")
                    if pd.isna(other_text) or other_text == 0:
                        other_text = ""
                    worksheet.merge_range(row, c, row+4, c+1, str(other_text).strip(), fmt_memo)
                    c += 2
                
                # --- 월간 요약 탭 그래프 ---
                worksheet_monthly = writer.sheets['월간 요약']
                chart_monthly = workbook.add_chart({'type': 'column'})
                
                last_row = len(df_monthly_with_total)
                task_start_col = 1
                task_end_col = len(monthly_task_cols)
                
                chart_monthly.add_series({
                    'name': '항목별 월간 부서 총 업무량',
                    'categories': ['월간 요약', 0, task_start_col, 0, task_end_col],
                    'values':     ['월간 요약', last_row, task_start_col, last_row, task_end_col],
                    'data_labels': {'value': True}
                })
                chart_monthly.set_title({'name': f'월간 항목별 부서 실적 ({folder_month})'})
                chart_monthly.set_x_axis({'name': '세부 업무'})
                chart_monthly.set_y_axis({'name': '총 업무 건수'})
                
                worksheet_monthly.insert_chart(1, len(df_monthly_with_total.columns) + 1, chart_monthly)
                
            messagebox.showinfo("취합 성공", f"총 {len(json_files)}건의 파일이 처리되었습니다.\n(Summary 폼 생성 완료)\n\n저장 경로:\n{excel_path}")
            # 저장 후 자동 실행 (크로스 플랫폼)
            try:
                import sys, subprocess
                if sys.platform == "win32":
                    os.startfile(excel_path)
                elif sys.platform == "darwin":
                    subprocess.Popen(['open', excel_path])
                else:
                    subprocess.Popen(['xdg-open', excel_path])
            except Exception:
                pass
        except ModuleNotFoundError:
            # xlsxwriter가 없을 경우를 대비하여 엔진 지정 없이 저장
            messagebox.showwarning("라이브러리 경고", "xlsxwriter 모듈이 설치되어 있지 않아 그래프 생성을 생략합니다.\n명령어 'pip install xlsxwriter'를 입력하시면 그래프 기능이 활성화됩니다.")
            try:
                with pd.ExcelWriter(excel_path) as writer:
                    df_daily.to_excel(writer, sheet_name=date_input, index=False)
                    df_monthly_with_total.to_excel(writer, sheet_name="월간 요약", index=False)
                messagebox.showinfo("취합 성공", f"총 {len(json_files)}건의 파일이 처리되었습니다.\n\n저장 경로:\n{excel_path}")
                try:
                    import sys, subprocess
                    if sys.platform == "win32":
                        os.startfile(excel_path)
                    elif sys.platform == "darwin":
                        subprocess.Popen(['open', excel_path])
                    else:
                        subprocess.Popen(['xdg-open', excel_path])
                except Exception:
                    pass
            except Exception as e2:
                messagebox.showerror("엑셀 변환 실패", f"엑셀 저장 중 오류가 발생했습니다: {e2}")
        except Exception as e:
            messagebox.showerror("엑셀 변환 실패", f"엑셀 저장 중 오류가 발생했습니다: {e}")

    def export_to_html(self):
            
        date_input = self.date_var.get().strip()
        try:
            date_obj = datetime.strptime(date_input, "%Y-%m-%d")
            folder_month = date_obj.strftime("%Y-%m")
            file_date = date_obj.strftime("%Y%m%d")
        except ValueError:
            messagebox.showerror("오류", "날짜 형식이 올바르지 않습니다. (YYYY-MM-DD)")
            return

        target_dir = os.path.join(LOCAL_BASE_PATH, folder_month)
        file_pattern = os.path.join(target_dir, "*.json")
        json_files = glob.glob(file_pattern)

        if not json_files:
            messagebox.showinfo("안내", f"{folder_month} 월에 저장된 데이터가 없습니다.")
            return

        all_rows = []
        for file_path in json_files:
            try:
                data = safe_read_json(file_path)
                if data:
                    row = {"일자": data.get("date", ""), "담당자": data.get("name", ""), "other_progress": data.get("other_progress", "")}
                    row.update(data.get("tasks", {}))
                    all_rows.append(row)
            except Exception as e:
                print(f"파일 로드 실패 ({file_path}): {e}")

        if not all_rows:
            messagebox.showinfo("안내", "유효한 데이터가 없습니다.")
            return

        df_all = pd.DataFrame(all_rows)

        # 라이브 마스터 리스트와 실제 데이터 사용자 통합 및 정렬
        current_staff_master = load_staff_list()
        all_unique_users = df_all["담당자"].unique().tolist()
        ordered_users = current_staff_master + [u for u in all_unique_users if u not in current_staff_master]

        # 1. 데일리 취합 요약 (선택한 날짜 기준)
        df_daily = df_all[df_all["일자"] == date_input].copy()
        df_daily.set_index("담당자", inplace=True)
        df_daily = df_daily.reindex(ordered_users)
        df_daily.index.name = "담당자"
        df_daily.reset_index(inplace=True)
        for col in df_daily.columns:
            if col in ["일자", "담당자", "other_progress"]:
                df_daily[col] = df_daily[col].fillna("")
            else:
                df_daily[col] = df_daily[col].fillna(0)

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
                content = safe_read_text(memo_path)
                if content:
                    memo_content = content
            except:
                pass

        html_target_dir = os.path.join(LOCAL_BASE_PATH, "html report", folder_month, date_input)
        os.makedirs(html_target_dir, exist_ok=True)
        
        self.root.config(cursor="watch")
        self.root.update_idletasks()
        
        def run_report():
            try:
                out_file, err = generate_html_report(date_input, html_target_dir, daily_dict, monthly_dict, memo_content, ordered_users, TASK_CATEGORIES)
                self.root.after(0, finish_report, out_file, err)
            except Exception as e:
                self.root.after(0, finish_report, None, str(e))
                
        def finish_report(out_file, err):
            self.root.config(cursor="")
            if out_file:
                messagebox.showinfo("취합 성공", f"HTML 대시보드 리포트 생성이 완료되었습니다.\n\n저장 경로:\n{out_file}")
            else:
                messagebox.showerror("HTML 변환 실패", f"HTML 리포트 생성 중 오류가 발생했습니다: {err}")

        import threading
        threading.Thread(target=run_report, daemon=True).start()

    def open_settings(self):
        SettingsWindow(self)

class SettingsWindow:
    def __init__(self, app):
        self.app = app
        self.top = tk.Toplevel(app.root)
        self.top.title("환경설정")
        
        # 메인창 기준 중앙 정렬 계산
        app.root.update_idletasks()
        main_x = app.root.winfo_x()
        main_y = app.root.winfo_y()
        main_w = app.root.winfo_width()
        main_h = app.root.winfo_height()
        
        w, h = 500, 600
        x = main_x + (main_w // 2) - (w // 2)
        y = main_y + (main_h // 2) - (h // 2)
        self.top.geometry(f"{w}x{h}+{x}+{y}")

        self.notebook = ttk.Notebook(self.top)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab 1: General Settings (Path)
        self.general_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.general_frame, text="기본 설정")
        self.setup_general_tab()

        # Tab 2: Staff
        self.staff_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.staff_frame, text="담당자 관리")
        self.setup_staff_tab()

        # Tab 3: Tasks
        self.task_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.task_frame, text="세부업무 관리")
        self.setup_task_tab()

        # Bottom Buttons
        btn_frame = tk.Frame(self.top)
        btn_frame.pack(fill="x", pady=10)
        save_btn = tk.Button(btn_frame, text="저장 및 닫기", font=("Arial", 11), command=self.save_settings)
        save_btn.pack(pady=5)

    def setup_general_tab(self):
        tk.Label(self.general_frame, text="데이터 적재 폴더 위치:", font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(20, 5))
        path_frame = tk.Frame(self.general_frame)
        path_frame.pack(fill="x", padx=10)
        self.path_var = tk.StringVar(value=LOCAL_BASE_PATH)
        tk.Entry(path_frame, textvariable=self.path_var, state="readonly").pack(side="left", fill="x", expand=True)
        tk.Button(path_frame, text="폴더 변경...", command=self.browse_path).pack(side="right", padx=(5, 0))

        # 리포트 저장 버튼들
        report_frame = tk.Frame(self.general_frame)
        report_frame.pack(fill="x", padx=10, pady=(20, 5))
        html_btn = tk.Button(report_frame, text="대시보드 HTML 저장", font=("Arial", 11),
                             command=self.app.export_to_html)
        html_btn.pack(side="left", padx=(0, 5))
        merge_btn = tk.Button(report_frame, text="대시보드 Excel 저장", font=("Arial", 11),
                              command=self.app.merge_to_excel)
        merge_btn.pack(side="left")

    def browse_path(self):
        from tkinter import filedialog
        new_path = filedialog.askdirectory(parent=self.top, initialdir=LOCAL_BASE_PATH, title="업무일지 저장 폴더 선택")
        if new_path:
            self.path_var.set(new_path)

    def setup_staff_tab(self):
        # Listbox
        self.staff_listbox = tk.Listbox(self.staff_frame, height=15)
        self.staff_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        for staff in STAFF_LIST:
            self.staff_listbox.insert(tk.END, staff)

        # Control Frame
        ctrl_frame = tk.Frame(self.staff_frame)
        ctrl_frame.pack(fill="x", padx=10, pady=5)
        
        self.new_staff_var = tk.StringVar()
        tk.Entry(ctrl_frame, textvariable=self.new_staff_var).pack(side="left", expand=True, fill="x", padx=5)
        tk.Button(ctrl_frame, text="추가", command=self.add_staff).pack(side="left", padx=5)
        tk.Button(ctrl_frame, text="선택 삭제", command=self.delete_staff).pack(side="right", padx=5)

    def add_staff(self):
        name = self.new_staff_var.get().strip()
        if name:
            self.staff_listbox.insert(tk.END, name)
            self.new_staff_var.set("")

    def delete_staff(self):
        sel = self.staff_listbox.curselection()
        if sel:
            self.staff_listbox.delete(sel[0])

    def setup_task_tab(self):
        self.task_tree = ttk.Treeview(self.task_frame, columns=("Type",), show="tree headings", height=15)
        self.task_tree.heading("#0", text="항목명")
        self.task_tree.heading("Type", text="유형")
        self.task_tree.column("#0", width=250)
        self.task_tree.column("Type", width=100)
        self.task_tree.pack(fill="both", expand=True, padx=10, pady=10)

        for cat, tasks in TASK_CATEGORIES.items():
            cat_id = self.task_tree.insert("", tk.END, text=cat, values=("카테고리",), open=True)
            for t in tasks:
                self.task_tree.insert(cat_id, tk.END, text=t, values=("세부업무",))

        ctrl_frame = tk.Frame(self.task_frame)
        ctrl_frame.pack(fill="x", padx=10, pady=5)
        
        self.new_task_var = tk.StringVar()
        tk.Entry(ctrl_frame, textvariable=self.new_task_var).pack(side="left", expand=True, fill="x", padx=5)
        
        btn_frame2 = tk.Frame(self.task_frame)
        btn_frame2.pack(fill="x", padx=10, pady=5)

        tk.Button(btn_frame2, text="카테고리 추가", command=self.add_category).pack(side="left", padx=5)
        tk.Button(btn_frame2, text="세부업무 추가", command=self.add_task).pack(side="left", padx=5)
        tk.Button(btn_frame2, text="선택 삭제", command=self.delete_task).pack(side="right", padx=5)

    def add_category(self):
        cat = self.new_task_var.get().strip()
        if cat:
            self.task_tree.insert("", tk.END, text=cat, values=("카테고리",), open=True)
            self.new_task_var.set("")

    def add_task(self):
        task = self.new_task_var.get().strip()
        if not task: return
        sel = self.task_tree.selection()
        if not sel:
            messagebox.showwarning("경고", "먼저 추가할 카테고리를 선택해주세요.")
            return
        item = sel[0]
        # Make sure it's a category
        if self.task_tree.item(item, "values")[0] == "세부업무":
            item = self.task_tree.parent(item)
            
        self.task_tree.insert(item, tk.END, text=task, values=("세부업무",))
        self.new_task_var.set("")

    def delete_task(self):
        sel = self.task_tree.selection()
        if sel:
            self.task_tree.delete(sel[0])

    def save_settings(self):
        # Save Path
        global LOCAL_BASE_PATH, STAFF_MASTER_FILE, TASK_MASTER_FILE
        new_path = self.path_var.get().strip()
        if new_path:
            LOCAL_BASE_PATH = new_path
            os.makedirs(LOCAL_BASE_PATH, exist_ok=True)
            STAFF_MASTER_FILE = os.path.join(LOCAL_BASE_PATH, "master/staff_master.json")
            TASK_MASTER_FILE = os.path.join(LOCAL_BASE_PATH, "master/task_master.json")
            try:
                os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
                config_data = safe_read_json(CONFIG_FILE, default={})
                config_data["LOCAL_BASE_PATH"] = new_path
                safe_write_json(CONFIG_FILE, config_data)
            except Exception as e:
                messagebox.showerror("오류", f"경로 설정 저장 실패: {e}")
                return
        else:
            messagebox.showerror("오류", "데이터 적재 폴더 경로를 지정해주세요.")
            return

        # Save Staff
        new_staff = list(self.staff_listbox.get(0, tk.END))
        try:
            safe_write_json(STAFF_MASTER_FILE, new_staff)
        except Exception as e:
            messagebox.showerror("오류", f"담당자 저장 실패: {e}")
            return

        # Save Tasks
        new_tasks = {}
        for child in self.task_tree.get_children(""):
            cat_name = self.task_tree.item(child, "text")
            sub_tasks = []
            for sub in self.task_tree.get_children(child):
                sub_tasks.append(self.task_tree.item(sub, "text"))
            new_tasks[cat_name] = sub_tasks
        
        try:
            safe_write_json(TASK_MASTER_FILE, new_tasks)
        except Exception as e:
            messagebox.showerror("오류", f"세부업무 저장 실패: {e}")
            return

        messagebox.showinfo("저장 완료", "설정이 저장되었습니다.\n변경 사항을 적용하려면 프로그램을 다시 실행해주세요.")
        self.top.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = WorkLogApp(root)
    root.mainloop()