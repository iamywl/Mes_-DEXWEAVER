"""FN-038~040: SPC 관리도 — X-bar/R 차트, 규칙 설정, Cp/Cpk 분석."""

import logging
import math
from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)

# SPC 상수표 (sample size n → 계수)
A2 = {2: 1.880, 3: 1.023, 4: 0.729, 5: 0.577, 6: 0.483, 7: 0.419, 8: 0.373, 9: 0.337, 10: 0.308}
D3 = {2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0.076, 8: 0.136, 9: 0.184, 10: 0.223}
D4 = {2: 3.267, 3: 2.575, 4: 2.282, 5: 2.115, 6: 2.004, 7: 1.924, 8: 1.864, 9: 1.816, 10: 1.777}
d2 = {2: 1.128, 3: 1.693, 4: 2.059, 5: 2.326, 6: 2.534, 7: 2.704, 8: 2.847, 9: 2.970, 10: 3.078}


def _western_electric_rules(subgroups, x_bar, r_bar, n):
    """Western Electric 규칙 위반 검사."""
    a2 = A2.get(n, 0.577)
    ucl = x_bar + a2 * r_bar
    lcl = x_bar - a2 * r_bar
    sigma = (ucl - x_bar) / 3 if ucl != x_bar else 1
    violations = []

    for i, sg in enumerate(subgroups):
        sg_mean = sg["mean"]
        # Rule 1: 1점이 3σ 밖
        if sg_mean > ucl or sg_mean < lcl:
            violations.append({"subgroup": i + 1, "rule": "RULE_1_BEYOND_3SIGMA",
                               "value": sg_mean, "severity": "CRITICAL"})
        # Rule 2: 연속 2점이 같은 쪽 2σ 밖
        if i >= 1:
            prev = subgroups[i - 1]["mean"]
            two_sigma_up = x_bar + 2 * sigma
            two_sigma_low = x_bar - 2 * sigma
            if (sg_mean > two_sigma_up and prev > two_sigma_up) or \
               (sg_mean < two_sigma_low and prev < two_sigma_low):
                violations.append({"subgroup": i + 1, "rule": "RULE_2_2OF3_BEYOND_2SIGMA",
                                   "value": sg_mean, "severity": "WARNING"})
        # Rule 3: 연속 4점이 같은 쪽 1σ 밖
        if i >= 3:
            vals = [subgroups[j]["mean"] for j in range(i - 3, i + 1)]
            one_sigma_up = x_bar + sigma
            one_sigma_low = x_bar - sigma
            if all(v > one_sigma_up for v in vals) or all(v < one_sigma_low for v in vals):
                violations.append({"subgroup": i + 1, "rule": "RULE_3_4OF5_BEYOND_1SIGMA",
                                   "value": sg_mean, "severity": "WARNING"})
        # Rule 4: 연속 8점이 한쪽
        if i >= 7:
            vals = [subgroups[j]["mean"] for j in range(i - 7, i + 1)]
            if all(v > x_bar for v in vals) or all(v < x_bar for v in vals):
                violations.append({"subgroup": i + 1, "rule": "RULE_4_8_CONSECUTIVE_ONE_SIDE",
                                   "value": sg_mean, "severity": "WARNING"})
    return violations


async def get_spc_chart(item_code: str, check_name: str = None) -> dict:
    """FN-038: SPC 관리도 데이터 (X-bar/R 차트)."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        # SPC 규칙 조회
        if check_name:
            cursor.execute(
                "SELECT rule_id, check_name, rule_type, ucl, lcl, target, sample_size "
                "FROM spc_rules WHERE item_code = %s AND check_name = %s AND is_active = TRUE",
                (item_code, check_name))
        else:
            cursor.execute(
                "SELECT rule_id, check_name, rule_type, ucl, lcl, target, sample_size "
                "FROM spc_rules WHERE item_code = %s AND is_active = TRUE",
                (item_code,))
        rules = cursor.fetchall()

        if not rules:
            # 규칙 없으면 검사 데이터에서 자동 계산
            cursor.execute(
                """SELECT id.measured_value
                   FROM inspection_details id
                   JOIN inspections i ON id.inspection_id = i.inspection_id
                   WHERE i.item_code = %s
                   ORDER BY i.inspected_at""",
                (item_code,))
            measurements = [float(r[0]) for r in cursor.fetchall() if r[0] is not None]
            cursor.close()

            if len(measurements) < 10:
                return {"item_code": item_code, "charts": [],
                        "message": "데이터가 부족합니다 (최소 10개 측정값 필요)."}

            n = 5  # 기본 서브그룹 크기
            return _calculate_chart(item_code, "자동", measurements, n)

        results = []
        for rule_id, cn, rt, ucl, lcl, target, n in rules:
            cursor.execute(
                """SELECT id.measured_value
                   FROM inspection_details id
                   JOIN inspections i ON id.inspection_id = i.inspection_id
                   WHERE i.item_code = %s AND id.check_name = %s
                   ORDER BY i.inspected_at""",
                (item_code, cn))
            measurements = [float(r[0]) for r in cursor.fetchall() if r[0] is not None]

            if len(measurements) < n * 2:
                results.append({"check_name": cn, "message": "데이터 부족"})
                continue

            chart = _calculate_chart(item_code, cn, measurements, n,
                                     float(ucl) if ucl else None,
                                     float(lcl) if lcl else None,
                                     float(target) if target else None)
            results.append(chart)

        cursor.close()
        return {"item_code": item_code, "charts": results}
    except Exception as e:
        log.error("SPC chart error: %s", e)
        return {"error": "SPC 관리도 조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


def _calculate_chart(item_code, check_name, measurements, n,
                     custom_ucl=None, custom_lcl=None, custom_target=None):
    """X-bar/R 차트 계산."""
    # 서브그룹 생성
    subgroups = []
    for i in range(0, len(measurements) - n + 1, n):
        group = measurements[i:i + n]
        if len(group) == n:
            subgroups.append({
                "no": len(subgroups) + 1,
                "values": group,
                "mean": sum(group) / len(group),
                "range": max(group) - min(group),
            })

    if not subgroups:
        return {"check_name": check_name, "message": "서브그룹 부족"}

    # X-bar, R-bar 계산
    x_bar = sum(sg["mean"] for sg in subgroups) / len(subgroups)
    r_bar = sum(sg["range"] for sg in subgroups) / len(subgroups)

    a2 = A2.get(n, 0.577)
    d3 = D3.get(n, 0)
    d4 = D4.get(n, 2.115)

    # 관리 한계선
    ucl_x = custom_ucl if custom_ucl is not None else x_bar + a2 * r_bar
    lcl_x = custom_lcl if custom_lcl is not None else x_bar - a2 * r_bar
    cl_x = custom_target if custom_target is not None else x_bar
    ucl_r = d4 * r_bar
    lcl_r = d3 * r_bar

    # Western Electric 위반 검사
    violations = _western_electric_rules(subgroups, x_bar, r_bar, n)

    return {
        "check_name": check_name,
        "item_code": item_code,
        "sample_size": n,
        "subgroup_count": len(subgroups),
        "x_bar_chart": {
            "cl": round(cl_x, 4),
            "ucl": round(ucl_x, 4),
            "lcl": round(lcl_x, 4),
            "data": [{"no": sg["no"], "mean": round(sg["mean"], 4)} for sg in subgroups],
        },
        "r_chart": {
            "cl": round(r_bar, 4),
            "ucl": round(ucl_r, 4),
            "lcl": round(lcl_r, 4),
            "data": [{"no": sg["no"], "range": round(sg["range"], 4)} for sg in subgroups],
        },
        "violations": violations,
        "in_control": len(violations) == 0,
    }


async def create_spc_rule(data: dict) -> dict:
    """FN-039: SPC 규칙 설정."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        item_code = data.get("item_code")
        check_name = data.get("check_name")
        if not item_code or not check_name:
            cursor.close()
            return {"error": "item_code와 check_name은 필수입니다."}

        cursor.execute(
            """INSERT INTO spc_rules (item_code, check_name, rule_type, ucl, lcl, target, sample_size)
               VALUES (%s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (item_code, check_name) DO UPDATE SET
                   rule_type = EXCLUDED.rule_type,
                   ucl = EXCLUDED.ucl,
                   lcl = EXCLUDED.lcl,
                   target = EXCLUDED.target,
                   sample_size = EXCLUDED.sample_size
               RETURNING rule_id""",
            (item_code, check_name,
             data.get("rule_type", "XBAR_R"),
             data.get("ucl"), data.get("lcl"), data.get("target"),
             data.get("sample_size", 5)))
        rule_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        return {"success": True, "rule_id": rule_id}
    except Exception as e:
        if conn:
            conn.rollback()
        log.error("SPC rule creation error: %s", e)
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_cpk(item_code: str, check_name: str = None) -> dict:
    """FN-040: Cp/Cpk 분석."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        # 규격 한계 조회
        if check_name:
            cursor.execute(
                "SELECT check_name, min_value, max_value, std_value "
                "FROM quality_standards WHERE item_code = %s AND check_name = %s",
                (item_code, check_name))
        else:
            cursor.execute(
                "SELECT check_name, min_value, max_value, std_value "
                "FROM quality_standards WHERE item_code = %s",
                (item_code,))
        standards = cursor.fetchall()

        results = []
        for cn, lsl, usl, target in standards:
            if lsl is None or usl is None:
                results.append({"check_name": cn, "message": "규격 한계 미설정"})
                continue

            lsl, usl = float(lsl), float(usl)
            target = float(target) if target else (usl + lsl) / 2

            # 측정 데이터 조회
            cursor.execute(
                """SELECT id.measured_value
                   FROM inspection_details id
                   JOIN inspections i ON id.inspection_id = i.inspection_id
                   WHERE i.item_code = %s AND id.check_name = %s
                   AND id.measured_value IS NOT NULL""",
                (item_code, cn))
            values = [float(r[0]) for r in cursor.fetchall()]

            if len(values) < 2:
                results.append({"check_name": cn, "message": "데이터 부족"})
                continue

            mean = sum(values) / len(values)
            sigma = math.sqrt(sum((v - mean) ** 2 for v in values) / (len(values) - 1))

            if sigma == 0:
                results.append({"check_name": cn, "cp": 999, "cpk": 999, "message": "변동 없음"})
                continue

            cp = (usl - lsl) / (6 * sigma)
            cpu = (usl - mean) / (3 * sigma)
            cpl = (mean - lsl) / (3 * sigma)
            cpk = min(cpu, cpl)

            grade = "EXCELLENT" if cpk >= 1.67 else "GOOD" if cpk >= 1.33 else "ADEQUATE" if cpk >= 1.0 else "POOR"

            results.append({
                "check_name": cn,
                "usl": usl,
                "lsl": lsl,
                "target": target,
                "mean": round(mean, 4),
                "sigma": round(sigma, 4),
                "n": len(values),
                "cp": round(cp, 4),
                "cpu": round(cpu, 4),
                "cpl": round(cpl, 4),
                "cpk": round(cpk, 4),
                "grade": grade,
            })

        cursor.close()
        return {"item_code": item_code, "cpk_analysis": results}
    except Exception as e:
        log.error("Cpk analysis error: %s", e)
        return {"error": "Cp/Cpk 분석 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def spc_auto_actions(data: dict) -> dict:
    """REQ-055: SPC 위반 시 자동격리 — 위반 LOT의 재고 상태를 HOLD로 변경.

    body: { "item_code": "...", "check_name": "...", "lot_no": "..." }
    """
    item_code = data.get("item_code", "")
    lot_no = data.get("lot_no", "")
    check_name = data.get("check_name", "")

    if not item_code or not lot_no:
        return {"error": "item_code, lot_no는 필수입니다."}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        # 해당 LOT 재고를 HOLD 처리
        cursor.execute(
            "UPDATE inventory SET status = 'HOLD' WHERE lot_no = %s AND status = 'NORMAL'",
            (lot_no,),
        )
        held = cursor.rowcount

        # SPC violation 기록
        cursor.execute(
            """INSERT INTO spc_violations
               (item_code, check_name, rule_name, violated_at, detail)
               VALUES (%s, %s, 'AUTO_QUARANTINE', NOW(), %s)""",
            (item_code, check_name or "N/A",
             f"LOT {lot_no} auto-quarantined ({held} rows held)"),
        )

        # NCR 자동 생성
        ncr_id = None
        try:
            from datetime import datetime
            today = datetime.now().strftime("%Y%m%d")
            cursor.execute(
                "SELECT COUNT(*) FROM ncr WHERE ncr_id LIKE %s",
                (f"NCR-{today}-%",),
            )
            seq = (cursor.fetchone()[0] or 0) + 1
            ncr_id = f"NCR-{today}-{seq:03d}"
            cursor.execute(
                """INSERT INTO ncr (ncr_id, title, source, lot_no, item_code, status)
                   VALUES (%s, %s, 'PROCESS', %s, %s, 'DETECTED')""",
                (ncr_id, f"SPC 위반 자동격리: {lot_no}", lot_no, item_code),
            )
        except Exception:
            ncr_id = None

        conn.commit()
        cursor.close()
        return {
            "success": True, "lot_no": lot_no, "held_count": held,
            "ncr_id": ncr_id,
            "message": f"LOT {lot_no}이(가) HOLD 처리되었습니다.",
        }
    except Exception as e:
        if conn:
            conn.rollback()
        log.error("SPC auto-action error: %s", e)
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)
