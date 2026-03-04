"""REQ-057/058: KPI — FPY(First Pass Yield) + 설비보전 KPI (MTTF/MTTR/MTBF)."""

import logging
from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)


async def get_fpy(process_code: str = None, item_code: str = None,
                  start_date: str = None, end_date: str = None) -> dict:
    """REQ-057: FPY 자동계산.

    FPY = 1차 양품수 / 투입수
    RTY = FPY₁ × FPY₂ × ... × FPYₙ (공정 체인 전체)
    """
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        # 캐시된 kpi_fpy_daily가 있으면 사용
        sql = """SELECT calc_date, process_code, item_code, input_qty,
                        first_pass_qty, fpy
                 FROM kpi_fpy_daily WHERE 1=1"""
        params = []
        if process_code:
            sql += " AND process_code = %s"
            params.append(process_code)
        if item_code:
            sql += " AND item_code = %s"
            params.append(item_code)
        if start_date:
            sql += " AND calc_date >= %s"
            params.append(start_date)
        if end_date:
            sql += " AND calc_date <= %s"
            params.append(end_date)
        sql += " ORDER BY calc_date DESC, process_code LIMIT 500"

        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()

        if rows:
            items = [
                {
                    "calc_date": r[0].isoformat() if r[0] else None,
                    "process_code": r[1], "item_code": r[2],
                    "input_qty": float(r[3]) if r[3] else 0,
                    "first_pass_qty": float(r[4]) if r[4] else 0,
                    "fpy": float(r[5]) if r[5] else 0,
                }
                for r in rows
            ]
            cursor.close()
            # RTY 계산 (프로세스별 평균 FPY의 곱)
            fpy_by_proc = {}
            for it in items:
                pc = it["process_code"]
                if pc not in fpy_by_proc:
                    fpy_by_proc[pc] = []
                fpy_by_proc[pc].append(it["fpy"])

            avg_fpy = {pc: sum(vs)/len(vs) for pc, vs in fpy_by_proc.items()}
            rty = 1.0
            for v in avg_fpy.values():
                rty *= v

            return {"items": items, "avg_fpy_by_process": avg_fpy,
                    "rty": round(rty, 6)}

        # 캐시 없으면 실시간 계산 (work_results + inspections)
        sql2 = """
            SELECT wr.process_code,
                   SUM(wr.good_qty + wr.defect_qty) AS input_qty,
                   SUM(wr.good_qty) AS first_pass_qty
            FROM work_results wr
            WHERE wr.process_code IS NOT NULL
        """
        params2 = []
        if process_code:
            sql2 += " AND wr.process_code = %s"
            params2.append(process_code)
        sql2 += " GROUP BY wr.process_code"

        cursor.execute(sql2, tuple(params2))
        rows2 = cursor.fetchall()
        cursor.close()

        items2 = []
        rty = 1.0
        for r in rows2:
            inp = float(r[1]) if r[1] else 0
            fp = float(r[2]) if r[2] else 0
            fpy_val = fp / inp if inp > 0 else 0
            items2.append({
                "process_code": r[0],
                "input_qty": inp,
                "first_pass_qty": fp,
                "fpy": round(fpy_val, 6),
            })
            rty *= fpy_val

        return {"items": items2, "rty": round(rty, 6)}
    except Exception as e:
        log.error("FPY 계산 오류: %s", e)
        return {"error": "FPY 계산 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def get_maintenance_kpi(equip_code: str,
                              start_date: str = None,
                              end_date: str = None) -> dict:
    """REQ-058: 설비보전 KPI (MTTF/MTTR/MTBF).

    MTTF = 총가동시간 / 고장횟수
    MTTR = 총수리시간 / 고장횟수
    MTBF = MTTF + MTTR
    """
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        # 캐시된 kpi_maintenance 데이터
        sql = """SELECT calc_date, equip_code, mttf_hours, mttr_hours,
                        mtbf_hours, failure_count
                 FROM kpi_maintenance WHERE equip_code = %s"""
        params = [equip_code]
        if start_date:
            sql += " AND calc_date >= %s"
            params.append(start_date)
        if end_date:
            sql += " AND calc_date <= %s"
            params.append(end_date)
        sql += " ORDER BY calc_date DESC LIMIT 90"

        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()

        if rows:
            items = [
                {
                    "calc_date": r[0].isoformat() if r[0] else None,
                    "equip_code": r[1],
                    "mttf_hours": float(r[2]) if r[2] else 0,
                    "mttr_hours": float(r[3]) if r[3] else 0,
                    "mtbf_hours": float(r[4]) if r[4] else 0,
                    "failure_count": r[5] or 0,
                }
                for r in rows
            ]
            cursor.close()
            return {"equip_code": equip_code, "items": items}

        # 실시간 계산 (equip_status_log 기반)
        cursor.execute(
            """SELECT status, logged_at
               FROM equip_status_log
               WHERE equip_code = %s
               ORDER BY logged_at""",
            (equip_code,),
        )
        logs = cursor.fetchall()
        cursor.close()

        if len(logs) < 2:
            return {"equip_code": equip_code, "items": [],
                    "message": "충분한 로그 데이터가 없습니다."}

        total_run_hours = 0
        total_repair_hours = 0
        failure_count = 0
        prev_status = None
        prev_time = None

        for status, logged_at in logs:
            if prev_time and prev_status:
                delta_hours = (logged_at - prev_time).total_seconds() / 3600
                if prev_status == 'RUNNING':
                    total_run_hours += delta_hours
                elif prev_status in ('DOWN', 'MAINTENANCE'):
                    total_repair_hours += delta_hours
            if status == 'DOWN' and prev_status == 'RUNNING':
                failure_count += 1
            prev_status = status
            prev_time = logged_at

        mttf = total_run_hours / failure_count if failure_count > 0 else total_run_hours
        mttr = total_repair_hours / failure_count if failure_count > 0 else 0
        mtbf = mttf + mttr

        return {
            "equip_code": equip_code,
            "realtime": True,
            "mttf_hours": round(mttf, 2),
            "mttr_hours": round(mttr, 2),
            "mtbf_hours": round(mtbf, 2),
            "failure_count": failure_count,
            "total_run_hours": round(total_run_hours, 2),
            "total_repair_hours": round(total_repair_hours, 2),
        }
    except Exception as e:
        log.error("Maintenance KPI 오류: %s", e)
        return {"error": "보전 KPI 계산 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)
