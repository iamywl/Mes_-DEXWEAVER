"""FN-025~027: Quality inspection and defect management."""

from api_modules.database import get_conn, release_conn


async def create_standard(data: dict) -> dict:
    """FN-025: Register quality inspection standards."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "DB connection failed."}
        cur = conn.cursor()
        item_code = data["item_code"]
        sid = None
        for c in data.get("checks", []):
            cur.execute(
                "INSERT INTO quality_standards "
                "(item_code, check_name, check_type, std_value, "
                "min_value, max_value, unit) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING standard_id",
                (item_code, c["name"], c.get("type", "NUMERIC"),
                 c.get("std"), c.get("min"), c.get("max"), c.get("unit")),
            )
            sid = cur.fetchone()[0]
        conn.commit()
        cur.close()
        return {"standard_id": sid, "success": True}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def create_inspection(data: dict) -> dict:
    """FN-026: Register inspection and auto-judge PASS/FAIL."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "DB connection failed."}
        cur = conn.cursor()
        item_code = data["item_code"]

        # Load standards
        cur.execute(
            "SELECT check_name, check_type, min_value, max_value "
            "FROM quality_standards WHERE item_code = %s",
            (item_code,),
        )
        stds = {r[0]: r for r in cur.fetchall()}

        overall = "PASS"
        fail_items = []
        details = []
        for r in data.get("results", []):
            name = r["check_name"]
            value = r.get("value")
            j = "PASS"
            if name in stds:
                check_type = stds[name][1]
                mn, mx = stds[name][2], stds[name][3]
                if check_type == "NUMERIC" and value is not None:
                    # 수치형: min/max 범위 검사
                    if mn is not None and float(value) < float(mn):
                        j = "FAIL"
                    if mx is not None and float(value) > float(mx):
                        j = "FAIL"
                elif check_type == "TEXT":
                    # 텍스트형: 기준값과 일치 검사
                    std_val = stds[name][2]  # min_value에 기준텍스트 저장
                    if std_val is not None and value is not None:
                        if str(value).strip().upper() != str(std_val).strip().upper():
                            j = "FAIL"
                elif check_type == "VISUAL":
                    # 외관검사: value가 'PASS'/'OK'/'합격'이 아니면 FAIL
                    if value is not None:
                        pass_values = {"PASS", "OK", "합격", "양호", "정상"}
                        if str(value).strip().upper() not in pass_values:
                            j = "FAIL"
                    # value가 None이면 검사자가 별도 판정 → details의 judgment 사용
                    elif r.get("judgment"):
                        j = r["judgment"].upper()
                else:
                    # 기타 타입: value 있으면 PASS, 명시적 judgment 우선
                    if r.get("judgment"):
                        j = r["judgment"].upper()
            else:
                # 기준 미등록 항목은 명시적 judgment 사용
                if r.get("judgment"):
                    j = r["judgment"].upper()
            if j == "FAIL":
                overall = "FAIL"
                fail_items.append(name)
            details.append((name, value, j))

        cur.execute(
            "INSERT INTO inspections "
            "(inspect_type, item_code, lot_no, judgment, inspector_id) "
            "VALUES (%s,%s,%s,%s,%s) RETURNING inspection_id",
            (data.get("type", "PROCESS"), item_code,
             data.get("lot_no"), overall, data.get("inspector_id")),
        )
        iid = cur.fetchone()[0]

        for name, value, j in details:
            cur.execute(
                "INSERT INTO inspection_details "
                "(inspection_id, check_name, measured_value, judgment) "
                "VALUES (%s,%s,%s,%s)",
                (iid, name, value, j),
            )

        conn.commit()
        cur.close()
        return {
            "inspection_id": iid, "judgment": overall,
            "fail_items": fail_items,
        }
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_defects(start_date: str = None, end_date: str = None,
                      item_code: str = None) -> dict:
    """FN-027: Defect summary and trend."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"summary": [], "trend": []}
        cur = conn.cursor()

        where = []
        params = []
        if start_date:
            where.append("wr.start_time >= %s")
            params.append(start_date)
        if end_date:
            where.append("wr.start_time <= %s")
            params.append(end_date)
        if item_code:
            where.append("wo.item_code = %s")
            params.append(item_code)
        wsql = "WHERE " + " AND ".join(where) if where else ""

        cur.execute(
            f"SELECT COALESCE(wr.defect_code,'UNKNOWN'), "
            f"SUM(wr.defect_qty), "
            f"SUM(wr.good_qty + wr.defect_qty) "
            f"FROM work_results wr "
            f"JOIN work_orders wo ON wr.wo_id = wo.wo_id "
            f"{wsql} "
            f"GROUP BY wr.defect_code",
            params,
        )
        summary = [
            {
                "defect_type": r[0], "count": r[1],
                "rate": round(r[1] / r[2], 4) if r[2] else 0,
            }
            for r in cur.fetchall()
        ]

        cur.execute(
            f"SELECT wr.start_time::date AS d, "
            f"SUM(wr.defect_qty), "
            f"SUM(wr.good_qty + wr.defect_qty) "
            f"FROM work_results wr "
            f"JOIN work_orders wo ON wr.wo_id = wo.wo_id "
            f"{wsql} "
            f"GROUP BY d ORDER BY d",
            params,
        )
        trend = [
            {
                "date": str(r[0]),
                "rate": round(r[1] / r[2], 4) if r[2] else 0,
            }
            for r in cur.fetchall()
        ]
        cur.close()
        return {"summary": summary, "trend": trend}
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)
