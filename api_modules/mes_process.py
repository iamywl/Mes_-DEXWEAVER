"""FN-010~012: Process and routing management module."""

from api_modules.database import get_conn, release_conn


async def create_process(data: dict) -> dict:
    """FN-010: Register a new process."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "Database connection failed."}

        cursor = conn.cursor()

        # Auto-generate process_code
        cursor.execute(
            "SELECT process_code FROM processes "
            "ORDER BY process_code DESC LIMIT 1"
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
                process_code,
                data["name"],
                data.get("std_time_min", 0),
                data.get("description"),
                data.get("equip_code"),
            ),
        )
        conn.commit()
        cursor.close()
        return {"process_code": process_code, "success": True}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
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
