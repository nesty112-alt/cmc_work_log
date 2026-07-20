import os
import json
import webbrowser
import urllib.request
import urllib.parse
import base64
from datetime import datetime

def get_quickchart_b64(chart_config):
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
        with urllib.request.urlopen(req, timeout=10) as response:
            image_data = response.read()
            b64 = base64.b64encode(image_data).decode('utf-8')
            return f"data:image/png;base64,{b64}"
    except Exception as e:
        print("QuickChart fallback error:", e)
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
                "y": { "stacked": True, "suggestedMax": 300 }
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
                "y": { "stacked": True, "suggestedMax": 3500 }
            }
        }
    }
    monthly_b64 = get_quickchart_b64(qc_monthly_config)

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

    # ------------------ 전체 HTML 템플릿 ------------------
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>업무대시보드 - {date_input}</title>
    <!-- Pretendard 폰트 -->
    <link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.8/dist/web/static/pretendard.css" />
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.0.0"></script>
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

    <!-- 차트 영역 -->
    <div class="section-title">업무 실적 분석 (일계 vs 누계 비교)</div>
    <div class="chart-grid">
        <div class="chart-card">
            <div class="chart-title">
                <div>📅 금일 업무 현황 (일계)</div>
            </div>
            <div class="chart-container-inner">
                {f'<img id="dailyChartFallback" src="{daily_b64}" style="width:100%; max-width:700px; display:block; margin:0 auto;" alt="금일 업무 현황 차트">' if daily_b64 else ''}
                <canvas id="dailyChart" style="display:none;"></canvas>
            </div>
        </div>
        <div class="chart-card">
            <div class="chart-title">
                <div>📈 누적 작업 건수</div>
            </div>
            <div class="chart-container-inner">
                {f'<img id="monthlyChartFallback" src="{monthly_b64}" style="width:100%; max-width:700px; display:block; margin:0 auto;" alt="누적 작업 건수 차트">' if monthly_b64 else ''}
                <canvas id="monthlyChart" style="display:none;"></canvas>
            </div>
        </div>
    </div>
    {custom_legend_html}

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

        Chart.register(ChartDataLabels);

        const staffList = {json.dumps(staff_list, ensure_ascii=False)};
        
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
                y: {{ stacked: true, suggestedMax: 300 }}
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
                y: {{ stacked: true, suggestedMax: 3500 }}
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
        webbrowser.open(f"file://{os.path.abspath(out_file)}")
        return out_file, None
    except Exception as e:
        return None, str(e)
