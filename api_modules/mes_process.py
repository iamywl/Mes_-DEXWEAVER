"""FN-010~012: Process and routing management module."""

from api_modules.database import get_conn, release_conn


async def list_processes() -> dict:
    """List all registered processes with equipment info."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "Database connection failed."}
        cursor = conn.cursor()
        cursor.execute(
            "SELECT p.process_code, p.name, p.std_time_min, p.description, "
            "p.equip_code, e.name AS equip_name, e.status AS equip_status "
            "FROM processes p "
            "LEFT JOIN equipments e ON p.equip_code = e.equip_code "
            "ORDER BY p.process_code"
        )
        rows = cursor.fetchall()
        cursor.close()
        processes = [
            {
                "process_code": r[0], "name": r[1],
                "std_time_min": r[2], "description": r[3],
                "equip_code": r[4], "equip_name": r[5],
                "equip_status": r[6],
            }
            for r in rows
        ]
        return {"processes": processes, "total": len(processes)}
    except Exception as e:
        return {"error": str(e), "processes": [], "total": 0}
    finally:
        if conn:
            release_conn(conn)


async def list_routings_summary() -> dict:
    """Summary of all item routings with step count and total time."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "Database connection failed."}
        cursor = conn.cursor()
        cursor.execute(
            "SELECT r.item_code, i.name AS item_name, i.category, "
            "COUNT(r.seq) AS step_count, SUM(r.cycle_time) AS total_time "
            "FROM routings r "
            "JOIN items i ON r.item_code = i.item_code "
            "GROUP BY r.item_code, i.name, i.category "
            "ORDER BY r.item_code"
        )
        rows = cursor.fetchall()
        cursor.close()
        summaries = [
            {
                "item_code": r[0], "item_name": r[1], "category": r[2],
                "step_count": r[3], "total_time": r[4],
            }
            for r in rows
        ]
        return {"routings": summaries, "total": len(summaries)}
    except Exception as e:
        return {"error": str(e), "routings": [], "total": 0}
    finally:
        if conn:
            release_conn(conn)


async def create_process(data: dict) -> dict:
    """FN-010: Register a new process."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}

        cursor = conn.cursor()

        name = data.get("name", "").strip()
        if not name:
            return {"error": "공정명은 필수입니다."}

        # Auto-generate process_code (numeric sort)
        cursor.execute(
            "SELECT process_code FROM processes "
            "ORDER BY CAST(SUBSTRING(process_code FROM 5) AS INTEGER) DESC LIMIT 1"
        )
        row = cursor.fetchone()
        if row:
            seq = int(row[0].split("-")[1]) + 1
        else:
            seq = 1
        process_code = f"PRC-{seq:03d}"

        cursor.execute(
            "INSERT INTO processes (process_code, name, std_time_min, "
            "description, equip_code) VALUES (%s, %s, %s, %s, %s)",
            (
                process_code, name,
                data.get("std_time_min", 0),
                data.get("description"),
                data.get("equip_code"),
            ),
        )
        conn.commit()
        cursor.close()
        return {"process_code": process_code, "success": True}
    except Exception:
        if conn:
            conn.rollback()
        return {"error": "공정 등록 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def update_process(process_code: str, data: dict) -> dict:
    """FN-010: Update a process."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        sets = []
        params = []
        for field, col in [("name", "name"), ("std_time_min", "std_time_min"),
                           ("description", "description"), ("equip_code", "equip_code")]:
            if field in data:
                sets.append(f"{col} = %s")
                params.append(data[field])

        if not sets:
            return {"error": "수정할 항목이 없습니다."}

        params.append(process_code)
        cursor.execute(
            f"UPDATE processes SET {', '.join(sets)} WHERE process_code = %s",
            params,
        )
        if cursor.rowcount == 0:
            return {"error": "공정을 찾을 수 없습니다."}
        conn.commit()
        cursor.close()
        return {"success": True, "process_code": process_code}
    except Exception:
        if conn:
            conn.rollback()
        return {"error": "공정 수정 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def delete_process(process_code: str) -> dict:
    """FN-010: Delete a process (check FK references first)."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        # Check if used in routings
        cursor.execute(
            "SELECT COUNT(*) FROM routings WHERE process_code = %s",
            (process_code,),
        )
        if cursor.fetchone()[0] > 0:
            return {"error": "라우팅에서 사용 중인 공정은 삭제할 수 없습니다."}

        cursor.execute(
            "DELETE FROM processes WHERE process_code = %s",
            (process_code,),
        )
        if cursor.rowcount == 0:
            return {"error": "공정을 찾을 수 없습니다."}
        conn.commit()
        cursor.close()
        return {"success": True, "deleted": process_code}
    except Exception:
        if conn:
            conn.rollback()
        return {"error": "공정 삭제 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def create_routing(data: dict) -> dict:
    """FN-011: Register routing for an item."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "Database connection failed."}

        cursor = conn.cursor()
        item_code = data["item_code"]
        routing_id = None

        for route in data["routes"]:
            cursor.execute(
                "INSERT INTO routings (item_code, seq, process_code, cycle_time) "
                "VALUES (%s, %s, %s, %s) "
                "ON CONFLICT (item_code, seq) DO UPDATE "
                "SET process_code = EXCLUDED.process_code, "
                "cycle_time = EXCLUDED.cycle_time "
                "RETURNING routing_id",
                (item_code, route["seq"],
                 route["process_code"], route.get("cycle_time", 0)),
            )
            routing_id = cursor.fetchone()[0]

        conn.commit()
        cursor.close()
        return {"routing_id": routing_id, "success": True}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_routing(item_code: str) -> dict:
    """FN-012: Get routing for an item."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "Database connection failed."}

        cursor = conn.cursor()
        cursor.execute(
            "SELECT r.seq, p.process_code, p.name, r.cycle_time, "
            "e.name AS equip_name "
            "FROM routings r "
            "JOIN processes p ON r.process_code = p.process_code "
            "LEFT JOIN equipments e ON p.equip_code = e.equip_code "
            "WHERE r.item_code = %s ORDER BY r.seq",
            (item_code,),
        )
        rows = cursor.fetchall()
        cursor.close()

        total_time = sum(r[3] for r in rows)
        routes = [
            {
                "seq": r[0], "process_code": r[1],
                "process_name": r[2], "cycle_time": r[3],
                "equip_name": r[4],
            }
            for r in rows
        ]
        return {
            "item_code": item_code,
            "routes": routes,
            "total_time": total_time,
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)
