import psycopg2
from psycopg2.extras import RealDictCursor
def get_db():
    try:
        return psycopg2.connect("host=postgres dbname=mes_db user=postgres password=mes1234", connect_timeout=2)
    except Exception as e:
        print(f"DB Connection Error: {e}")
        return None
