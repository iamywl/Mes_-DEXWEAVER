from flask import Flask, render_template_string, request, redirect
import psycopg2

app = Flask(__name__)

db_config = {
    "host": "postgres",
    "database": "mes_db",
    "user": "postgres",
    "password": "mes1234"
}

def get_db_data(query):
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        cur.execute(query)
        data = cur.fetchall()
        colnames = [desc[0] for desc in cur.description]
        cur.close()
        conn.close()
        return colnames, data
    except Exception as e:
        return [], str(e)

# 통합 대시보드 HTML
base_html = """
<!DOCTYPE html>
<html>
<head>
    <title>경북대 MES 통합 관리</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; display: flex; background-color: #f0f2f5; }
        .sidebar { width: 200px; background: #00458d; color: white; height: 100vh; padding: 20px; position: fixed; }
        .content { margin-left: 240px; padding: 40px; width: calc(100% - 240px); }
        .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 30px; }
        h1 { color: #333; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; background: white; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: left; font-size: 14px; }
        th { background-color: #f8f9fa; color: #555; }
        .status-badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .wait { background: #ffeeba; color: #856404; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h2>MES 2026</h2>
        <p>사용자: iamywl</p>
        <hr>
        <p>✔ 인프라: K8s</p>
        <p>✔ 네트워크: Cilium</p>
    </div>
    <div class="content">
        <h1>🏭 실시간 생산 현황 대시보드</h1>
        
        <div class="card">
            <h3>📦 품목(Items) 현황</h3>
            <table>
                <tr>{% for col in item_cols %}<th>{{ col }}</th>{% endfor %}</tr>
                {% for row in items %}
                <tr>{% for cell in row %}<td>{{ cell }}</td>{% endfor %}</tr>
                {% endfor %}
            </table>
        </div>

        <div class="card">
            <h3>📅 생산 계획(Production Plans)</h3>
            <table>
                <tr>{% for col in plan_cols %}<th>{{ col }}</th>{% endfor %}</tr>
                {% for row in plans %}
                <tr>{% for cell in row %}<td>{{ cell }}</td>{% endfor %}</tr>
                {% endfor %}
            </table>
        </div>

        <div class="card">
            <h3>⚙️ 등록된 공정(Processes)</h3>
            <table>
                <tr>{% for col in proc_cols %}<th>{{ col }}</th>{% endfor %}</tr>
                {% for row in procs %}
                <tr>{% for cell in row %}<td>{{ cell }}</td>{% endfor %}</tr>
                {% endfor %}
            </table>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    item_cols, items = get_db_data("SELECT * FROM items;")
    plan_cols, plans = get_db_data("SELECT * FROM production_plans;")
    proc_cols, procs = get_db_data("SELECT * FROM processes;")
    
    return render_template_string(base_html, 
                                items=items, item_cols=item_cols,
                                plans=plans, plan_cols=plan_cols,
                                procs=procs, proc_cols=proc_cols)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
