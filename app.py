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

@app.route('/')
def index():
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
        tables = cur.fetchall()
        cur.close()
        conn.close()
        return f"<h1>스마트 팩토리 MES 시스템</h1><p>DB 연결 성공! 현재 생성된 테이블: {tables}</p>"
    except Exception as e:
        return f"<h1>DB 연결 실패</h1><p>에러: {e}</p>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
