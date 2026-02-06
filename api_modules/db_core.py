import psycopg2
from psycopg2.extras import RealDictCursor

def get_conn():
    try:
        return psycopg2.connect("host=postgres dbname=mes_db user=postgres password=mes1234", connect_timeout=2)
    except: return None

def query_db(sql, params=None, fetch=True):
    conn = get_conn()
    if not conn: return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            if fetch: return cur.fetchall()
            conn.commit()
            return True
    except Exception as e:
        print(f"SQL Error: {e}")
        return []
    finally: conn.close()
