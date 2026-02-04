from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
import uvicorn

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

db_config = {"host": "postgres", "port": 5432, "database": "mes_db", "user": "postgres", "password": "mes1234"}

@app.get("/api/data")
async def get_dashboard_data():
    conn = None
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT item_code, name, unit FROM items")
        items = cur.fetchall()
        cur.execute("SELECT equipment_id, name, status FROM equipments")
        equips = cur.fetchall()
        cur.close()
        return {"items": items, "equipments": equips}
    except Exception as e:
        return {"error": str(e), "items": [], "equipments": []}
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
