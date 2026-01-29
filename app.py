from flask import Flask, render_template_string
import psycopg2

app = Flask(__name__)

# DB 연결 정보
db_config = {
    "host": "postgres",
    "database": "mes_db",
    "user": "postgres",
    "password": "mes1234"
}

# 💡 이 부분이 화면의 디자인(CSS)과 구조(HTML)를 결정합니다.
html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>경북대 MES 통합 관리</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; margin: 0; display: flex; background-color: #f0f2f5; }
        .sidebar { width: 200px; background: #00458d; color: white; height: 100vh; padding: 20px; position: fixed; }
        .content { margin-left: 240px; padding: 40px; width: calc(100% - 240px); }
        .card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 30px; }
        h1 { color: #333; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #f8f9fa; color: #555; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h2>MES 2026</h2>
        <p>사용자: iamywl</p> <hr>
        <p>인프라: K8s</p>
        <p>네트워크: Cilium</p>
    </div>
    <div class="content">
        <h1>🏭 실시간 생산 현황 대시보드</h1>
        <div class="card">
            <h3>📦 품목(Items) 현황</h3>
            <table>
                <tr><th>item_code</th><th>name</th><th>category</th><th>unit</th><th>spec</th><th>safety_stock</th></tr>
                {% for row in items %}
                <tr><td>{{row[0]}}</td><td>{{row[1]}}</td><td>{{row[2]}}</td><td>{{row[3]}}</td><td>{{row[4]}}</td><td>{{row[5]}}</td></tr>
                {% endfor %}
            </table>
        </div>
        </div>
</body>
</html>
"""

@app.route('/')
def index():
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    # 테이블에서 데이터를 가져옵니다.
    cur.execute("SELECT * FROM items;")
    items = cur.fetchall()
    cur.close()
    conn.close()
    return render_template_string(html_template, items=items)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
