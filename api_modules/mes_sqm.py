"""REQ-065: 공급업체 품질 관리(SQM) — 스코어카드, SCAR, ASL."""

import logging
from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)


async def create_supplier(data: dict) -> dict:
    """공급업체 등록."""
    supplier_code = data.get("supplier_code", "").strip()
    name = data.get("name", "").strip()
    if not supplier_code or not name:
        return {"error": "supplier_code, name은 필수입니다."}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO suppliers
               (supplier_code, name, contact_person, phone, email)
               VALUES (%s,%s,%s,%s,%s) RETURNING supplier_id""",
            (supplier_code, name, data.get("contact_person"),
             data.get("phone"), data.get("email")),
        )
        sid = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        return {"success": True, "supplier_id": sid, "supplier_code": supplier_code}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_suppliers(asl_status: str = None) -> dict:
    """공급업체 목록 + 스코어카드."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()
        sql = """SELECT supplier_id, supplier_code, name, contact_person,
                        asl_status, quality_score, delivery_score, is_active
                 FROM suppliers WHERE is_active = TRUE"""
        params = []
        if asl_status:
            sql += " AND asl_status = %s"
            params.append(asl_status)
        sql += " ORDER BY quality_score DESC NULLS LAST"
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        cursor.close()
        return {
            "items": [
                {"supplier_id": r[0], "supplier_code": r[1], "name": r[2],
                 "contact_person": r[3], "asl_status": r[4],
                 "quality_score": float(r[5]) if r[5] else None,
                 "delivery_score": float(r[6]) if r[6] else None,
                 "overall_score": round((float(r[5] or 0) * 0.6 + float(r[6] or 0) * 0.4), 1)}
                for r in rows
            ]
        }
    except Exception:
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def create_scar(data: dict) -> dict:
    """SCAR(공급업체 시정조치 요청) 생성."""
    supplier_id = data.get("supplier_id")
    description = data.get("description", "").strip()
    if not supplier_id or not description:
        return {"error": "supplier_id, description은 필수입니다."}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        from datetime import datetime
        today = datetime.now().strftime("%Y%m%d")
        cursor.execute("SELECT COUNT(*) FROM scar WHERE scar_code LIKE %s",
                       (f"SCAR-{today}-%",))
        seq = (cursor.fetchone()[0] or 0) + 1
        scar_code = f"SCAR-{today}-{seq:03d}"

        cursor.execute(
            """INSERT INTO scar
               (scar_code, supplier_id, issue_type, description, severity,
                response_due, issued_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING scar_id""",
            (scar_code, supplier_id, data.get("issue_type", "QUALITY"),
             description, data.get("severity", "MAJOR"),
             data.get("response_due"), data.get("issued_by")),
        )
        scar_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        return {"success": True, "scar_id": scar_id, "scar_code": scar_code}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_scars(supplier_id: int = None, status: str = None) -> dict:
    """SCAR 목록."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()
        sql = """SELECT sc.scar_id, sc.scar_code, s.name AS supplier_name,
                        sc.issue_type, sc.severity, sc.status,
                        sc.response_due, sc.created_at
                 FROM scar sc JOIN suppliers s ON sc.supplier_id = s.supplier_id
                 WHERE 1=1"""
        params = []
        if supplier_id:
            sql += " AND sc.supplier_id = %s"
            params.append(supplier_id)
        if status:
            sql += " AND sc.status = %s"
            params.append(status)
        sql += " ORDER BY sc.created_at DESC LIMIT 200"
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        cursor.close()
        return {
            "items": [
                {"scar_id": r[0], "scar_code": r[1], "supplier_name": r[2],
                 "issue_type": r[3], "severity": r[4], "status": r[5],
                 "response_due": r[6].isoformat() if r[6] else None,
                 "created_at": r[7].isoformat() if r[7] else None}
                for r in rows
            ]
        }
    except Exception:
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def update_supplier_score(supplier_id: int) -> dict:
    """공급업체 품질/납기 점수 자동 집계 갱신."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        # SCAR 기반 감점
        cursor.execute(
            """SELECT COUNT(*), SUM(CASE WHEN severity='CRITICAL' THEN 20
                   WHEN severity='MAJOR' THEN 10 ELSE 5 END)
               FROM scar WHERE supplier_id = %s AND status != 'CLOSED'
                 AND created_at >= NOW() - INTERVAL '12 months'""",
            (supplier_id,),
        )
        row = cursor.fetchone()
        open_scars = row[0] or 0
        penalty = float(row[1] or 0)
        quality = max(100 - penalty, 0)

        cursor.execute(
            "UPDATE suppliers SET quality_score = %s WHERE supplier_id = %s",
            (quality, supplier_id),
        )
        conn.commit()
        cursor.close()
        return {"success": True, "supplier_id": supplier_id,
                "quality_score": quality, "open_scars": open_scars}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)
