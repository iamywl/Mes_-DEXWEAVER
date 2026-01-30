from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
import uvicorn

app = FastAPI()

# 리액트와의 통신 허용 (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

db_config = {
    "host": "postgres",
    "database": "mes_db",
    "user": "postgres",
    "password": "mes1234",
    "connect_timeout": 3
}

@app.get("/api/data")
async def get_mes_data():
    tables = ['items', 'production_plans', 'processes', 'equipments']
    result = {}
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        for table in tables:
            cur.execute(f"SELECT * FROM {table} ORDER BY 1;")
            result[table] = cur.fetchall()
        cur.close()
        conn.close()
        return result
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
