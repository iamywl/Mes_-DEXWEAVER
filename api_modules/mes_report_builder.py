"""REQ-070: 리포트 빌더 — 템플릿 관리, Export, 정기 생성."""

import json
import logging
from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)

# 데이터소스 → SQL 매핑 (안전한 화이트리스트)
DATA_SOURCES = {
    "work_orders": "SELECT wo_code, item_code, order_qty, good_qty, status, start_date, end_date FROM work_orders",
    "inspections": "SELECT insp_code, item_code, process_code, result, inspector, created_at FROM inspections",
    "inventory": "SELECT item_code, current_qty, safety_stock, location FROM inventory",
    "production_plans": "SELECT plan_id, item_code, plan_qty, status, start_date, end_date FROM production_plans",
    "equipments": "SELECT equip_code, equip_name, equip_type, status, location FROM equipments",
    "quality_summary": """SELECT i.item_code, COUNT(*) AS total,
                           SUM(CASE WHEN i.result='PASS' THEN 1 ELSE 0 END) AS pass_cnt,
                           SUM(CASE WHEN i.result='FAIL' THEN 1 ELSE 0 END) AS fail_cnt
                           FROM inspections i GROUP BY i.item_code""",
}


async def create_template(data: dict, user_id: str) -> dict:
    """리포트 템플릿 생성."""
    title = data.get("title", "").strip()
    data_source = data.get("data_source", "").strip()

    if not title or not data_source:
        return {"error": "title, data_source는 필수입니다."}
    if data_source not in DATA_SOURCES:
        return {"error": f"지원되지 않는 data_source: {data_source}"}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        from datetime import datetime
        today = datetime.now().strftime("%Y%m%d")
        cursor.execute("SELECT COUNT(*) FROM report_templates WHERE template_code LIKE %s",
                       (f"RPT-{today}-%",))
        seq = (cursor.fetchone()[0] or 0) + 1
        template_code = f"RPT-{today}-{seq:03d}"

        cursor.execute(
            """INSERT INTO report_templates
               (template_code, title, description, data_source, columns,
                filters, grouping, sorting, output_format, schedule_cron, created_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING template_id""",
            (template_code, title, data.get("description"),
             data_source, json.dumps(data.get("columns", [])),
             json.dumps(data.get("filters", [])),
             json.dumps(data.get("grouping", [])),
             json.dumps(data.get("sorting", [])),
             data.get("output_format", "PDF"),
             data.get("schedule_cron"), user_id),
        )
        tid = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        return {"success": True, "template_id": tid, "template_code": template_code}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_templates() -> dict:
    """리포트 템플릿 목록."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()
        cursor.execute(
            """SELECT template_id, template_code, title, data_source,
                      output_format, schedule_cron, is_active, created_by, created_at
               FROM report_templates WHERE is_active = TRUE
               ORDER BY created_at DESC""",
        )
        rows = cursor.fetchall()
        cursor.close()
        return {
            "items": [
                {"template_id": r[0], "template_code": r[1], "title": r[2],
                 "data_source": r[3], "output_format": r[4],
                 "schedule_cron": r[5], "is_active": r[6],
                 "created_by": r[7],
                 "created_at": r[8].isoformat() if r[8] else None}
                for r in rows
            ],
            "data_sources": list(DATA_SOURCES.keys()),
        }
    except Exception:
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def execute_report(template_id: int) -> dict:
    """리포트 실행 (데이터 조회)."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        cursor.execute(
            """SELECT template_code, title, data_source, columns, filters,
                      grouping, sorting, output_format
               FROM report_templates WHERE template_id = %s""",
            (template_id,),
        )
        t = cursor.fetchone()
        if not t:
            cursor.close()
            return {"error": "템플릿을 찾을 수 없습니다."}

        data_source = t[2]
        base_sql = DATA_SOURCES.get(data_source)
        if not base_sql:
            cursor.close()
            return {"error": "지원되지 않는 데이터소스입니다."}

        sql = f"SELECT * FROM ({base_sql}) sub LIMIT 1000"
        cursor.execute(sql)
        cols = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        cursor.close()

        data = []
        for row in rows:
            record = {}
            for i, col in enumerate(cols):
                v = row[i]
                if hasattr(v, 'isoformat'):
                    v = v.isoformat()
                elif isinstance(v, (int, float, str, bool, type(None))):
                    pass
                else:
                    v = str(v)
                record[col] = v
            data.append(record)

        return {
            "template_code": t[0], "title": t[1],
            "columns": cols, "row_count": len(data),
            "data": data, "output_format": t[7],
        }
    except Exception as e:
        log.error("리포트 실행 오류: %s", e)
        return {"error": "리포트 실행 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)
