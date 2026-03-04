"""REQ-059: MSA/Gage R&R — 측정시스템분석 (AIAG MSA 4th)."""

import logging
import math
from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)


async def create_study(data: dict) -> dict:
    """MSA 연구 생성."""
    gauge_code = data.get("gauge_code", "").strip()
    study_type = data.get("study_type", "GAGE_RR")
    characteristic = data.get("characteristic", "").strip()

    if not gauge_code or not characteristic:
        return {"error": "gauge_code, characteristic는 필수입니다."}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        from datetime import datetime
        today = datetime.now().strftime("%Y%m%d")
        cursor.execute("SELECT COUNT(*) FROM msa_studies WHERE study_code LIKE %s",
                       (f"MSA-{today}-%",))
        seq = (cursor.fetchone()[0] or 0) + 1
        study_code = f"MSA-{today}-{seq:03d}"

        cursor.execute(
            """INSERT INTO msa_studies
               (study_code, study_type, gauge_code, gauge_name, characteristic,
                specification_lsl, specification_usl, num_operators, num_parts, num_trials,
                conducted_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               RETURNING study_id""",
            (study_code, study_type, gauge_code, data.get("gauge_name"),
             characteristic, data.get("lsl"), data.get("usl"),
             data.get("num_operators", 3), data.get("num_parts", 10),
             data.get("num_trials", 3), data.get("conducted_by")),
        )
        study_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        return {"success": True, "study_id": study_id, "study_code": study_code}
    except Exception as e:
        if conn:
            conn.rollback()
        log.error("MSA 연구 생성 오류: %s", e)
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def add_measurements(study_id: int, data: dict) -> dict:
    """측정 데이터 일괄 입력."""
    measurements = data.get("measurements", [])
    if not measurements:
        return {"error": "measurements 배열이 필요합니다."}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        count = 0
        for m in measurements:
            cursor.execute(
                """INSERT INTO msa_measurements
                   (study_id, operator_id, part_number, trial_number, measured_value)
                   VALUES (%s,%s,%s,%s,%s)""",
                (study_id, m["operator_id"], m["part_number"],
                 m["trial_number"], m["measured_value"]),
            )
            count += 1
        conn.commit()
        cursor.close()
        return {"success": True, "inserted": count}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def calculate_grr(study_id: int) -> dict:
    """Gage R&R %GRR 및 ndc 계산 (ANOVA 간이법)."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM msa_studies WHERE study_id = %s", (study_id,))
        study = cursor.fetchone()
        if not study:
            cursor.close()
            return {"error": "연구를 찾을 수 없습니다."}

        cursor.execute(
            """SELECT operator_id, part_number, trial_number, measured_value
               FROM msa_measurements WHERE study_id = %s
               ORDER BY operator_id, part_number, trial_number""",
            (study_id,),
        )
        rows = cursor.fetchall()
        if not rows:
            cursor.close()
            return {"error": "측정 데이터가 없습니다."}

        # Range method 계산
        ops = {}
        parts = {}
        all_vals = []
        for r in rows:
            op, pn, _, val = r
            val = float(val)
            all_vals.append(val)
            ops.setdefault(op, {}).setdefault(pn, []).append(val)
            parts.setdefault(pn, []).append(val)

        n_ops = len(ops)
        n_parts = len(parts)
        n_trials = max(len(v) for op_data in ops.values() for v in op_data.values()) if ops else 1

        # EV (Equipment Variation) = Rbar * K1
        k1_table = {2: 4.56, 3: 3.05}
        k1 = k1_table.get(n_trials, 3.05)
        ranges_by_op = []
        for op_data in ops.values():
            for vals in op_data.values():
                if len(vals) > 1:
                    ranges_by_op.append(max(vals) - min(vals))
        r_bar = sum(ranges_by_op) / len(ranges_by_op) if ranges_by_op else 0
        ev = r_bar / k1 if k1 else 0

        # AV (Appraiser Variation)
        op_avgs = {op: sum(v for pn_vals in d.values() for v in pn_vals) /
                   sum(len(v) for v in d.values()) for op, d in ops.items()}
        x_diff = max(op_avgs.values()) - min(op_avgs.values()) if op_avgs else 0
        k2_table = {2: 3.65, 3: 2.70}
        k2 = k2_table.get(n_ops, 2.70)
        nr = n_parts * n_trials
        av_sq = (x_diff / k2) ** 2 - (ev ** 2 / nr) if k2 else 0
        av = math.sqrt(max(av_sq, 0))

        # GRR
        grr = math.sqrt(ev ** 2 + av ** 2)

        # PV (Part Variation)
        part_avgs = {pn: sum(vals) / len(vals) for pn, vals in parts.items()}
        rp = max(part_avgs.values()) - min(part_avgs.values()) if part_avgs else 0
        k3_table = {5: 2.08, 10: 1.62, 15: 1.51, 20: 1.47}
        k3 = k3_table.get(n_parts, 1.62)
        pv = rp / k3 if k3 else 0

        # TV (Total Variation)
        tv = math.sqrt(grr ** 2 + pv ** 2) if (grr ** 2 + pv ** 2) > 0 else 1

        grr_pct = (grr / tv * 100) if tv > 0 else 0
        ndc = int(1.41 * pv / grr) if grr > 0 else 0

        # 판정
        if grr_pct < 10:
            verdict = "ACCEPTABLE"
        elif grr_pct < 30:
            verdict = "MARGINAL"
        else:
            verdict = "UNACCEPTABLE"

        # 결과 저장
        cursor.execute(
            """UPDATE msa_studies SET result_grr_pct = %s, result_ndc = %s,
                      status = 'COMPLETED' WHERE study_id = %s""",
            (round(grr_pct, 4), ndc, study_id),
        )
        conn.commit()
        cursor.close()

        return {
            "study_id": study_id,
            "ev": round(ev, 6), "av": round(av, 6), "grr": round(grr, 6),
            "pv": round(pv, 6), "tv": round(tv, 6),
            "grr_pct": round(grr_pct, 2), "ndc": ndc,
            "verdict": verdict,
        }
    except Exception as e:
        if conn:
            conn.rollback()
        log.error("GRR 계산 오류: %s", e)
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_studies(gauge_code: str = None, study_type: str = None) -> dict:
    """MSA 연구 목록."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()
        sql = """SELECT study_id, study_code, study_type, gauge_code, gauge_name,
                        characteristic, result_grr_pct, result_ndc, status, created_at
                 FROM msa_studies WHERE 1=1"""
        params = []
        if gauge_code:
            sql += " AND gauge_code = %s"
            params.append(gauge_code)
        if study_type:
            sql += " AND study_type = %s"
            params.append(study_type)
        sql += " ORDER BY created_at DESC LIMIT 200"
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        cursor.close()
        return {
            "items": [
                {"study_id": r[0], "study_code": r[1], "study_type": r[2],
                 "gauge_code": r[3], "gauge_name": r[4], "characteristic": r[5],
                 "grr_pct": float(r[6]) if r[6] else None, "ndc": r[7],
                 "status": r[8], "created_at": r[9].isoformat() if r[9] else None}
                for r in rows
            ]
        }
    except Exception:
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)
