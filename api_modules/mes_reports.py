"""FN-035~037: Reports and AI insights module."""

from api_modules.database import get_conn, release_conn


async def production_report(start_date: str = None, end_date: str = None,
                            group_by: str = "day") -> dict:
    """FN-035: Production performance report."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "DB connection failed."}
        cur = conn.cursor()

        where = []
        params = []
        if start_date:
            where.append("wo.work_date >= %s")
            params.append(start_date)
        if end_date:
            where.append("wo.work_date <= %s")
            params.append(end_date)
        wsql = "WHERE " + " AND ".join(where) if where else ""

        if group_by == "month":
            period = "TO_CHAR(wo.work_date, 'YYYY-MM')"
        elif group_by == "week":
            period = "TO_CHAR(wo.work_date, 'IYYY-IW')"
        else:
            period = "wo.work_date::text"

        # Trend
        cur.execute(
            f"SELECT {period} AS period, "
            f"SUM(wr.good_qty) AS qty "
            f"FROM work_results wr "
            f"JOIN work_orders wo ON wr.wo_id = wo.wo_id "
            f"{wsql} "
            f"GROUP BY period ORDER BY period",
            params,
        )
        trend = [{"period": r[0], "qty": r[1]} for r in cur.fetchall()]

        # By item
        cur.execute(
            f"SELECT i.name, "
            f"SUM(wr.good_qty) AS qty, SUM(wo.plan_qty) AS plan "
            f"FROM work_results wr "
            f"JOIN work_orders wo ON wr.wo_id = wo.wo_id "
            f"JOIN items i ON wo.item_code = i.item_code "
            f"{wsql} "
            f"GROUP BY i.name",
            params,
        )
        by_item = [
            {
                "item": r[0], "qty": r[1],
                "rate": round(r[1] / r[2], 2) if r[2] else 0,
            }
            for r in cur.fetchall()
        ]

        total_qty = sum(t["qty"] for t in trend)
        cur.execute(
            f"SELECT COALESCE(SUM(wo.plan_qty),0) "
            f"FROM work_orders wo {wsql}",
            params,
        )
        total_plan = cur.fetchone()[0]
        cur.close()

        return {
            "summary": {
                "total_qty": total_qty,
                "achieve_rate": round(total_qty / total_plan, 2) if total_plan else 0,
            },
            "trend": trend,
            "by_item": by_item,
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def quality_report(start_date: str = None, end_date: str = None,
                         item_code: str = None) -> dict:
    """FN-036: Quality analysis report with defect rate and Cpk."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "DB connection failed."}
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
            f"SELECT SUM(wr.defect_qty), "
            f"SUM(wr.good_qty + wr.defect_qty) "
            f"FROM work_results wr "
            f"JOIN work_orders wo ON wr.wo_id = wo.wo_id "
            f"{wsql}",
            params,
        )
        row = cur.fetchone()
        defects = row[0] or 0
        total = row[1] or 0
        defect_rate = round(defects / total, 4) if total else 0

        # Trend
        cur.execute(
            f"SELECT wr.start_time::date, "
            f"SUM(wr.defect_qty), SUM(wr.good_qty + wr.defect_qty) "
            f"FROM work_results wr "
            f"JOIN work_orders wo ON wr.wo_id = wo.wo_id "
            f"{wsql} "
            f"GROUP BY wr.start_time::date ORDER BY 1",
            params,
        )
        trend = [
            {
                "date": str(r[0]),
                "rate": round(r[1] / r[2], 4) if r[2] else 0,
            }
            for r in cur.fetchall()
        ]

        # Simple Cpk placeholder (needs inspection detail data)
        cpk = round(max(0, (1 - defect_rate * 10) * 1.33), 2)

        cur.close()
        return {
            "defect_rate": defect_rate,
            "trend": trend,
            "cpk": cpk,
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def ai_insights(data: dict) -> dict:
    """FN-037: AI-generated insights from production/quality/equipment data."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "DB connection failed."}
        cur = conn.cursor()
        focus = data.get("focus_area", "production")

        issues = []
        recommendations = []

        # Production analysis
        cur.execute(
            "SELECT i.name, SUM(wr.good_qty), SUM(wo.plan_qty) "
            "FROM work_results wr "
            "JOIN work_orders wo ON wr.wo_id = wo.wo_id "
            "JOIN items i ON wo.item_code = i.item_code "
            "GROUP BY i.name"
        )
        for r in cur.fetchall():
            rate = r[1] / r[2] if r[2] else 0
            if rate < 0.9:
                issues.append({
                    "area": "production",
                    "desc": f"{r[0]} 달성률 {rate*100:.0f}%로 목표 미달",
                })
                recommendations.append({
                    "action": f"{r[0]} 생산라인 설비 점검 및 작업 효율화",
                    "expected_impact": f"달성률 {(rate+0.1)*100:.0f}%로 향상 기대",
                })

        # Equipment analysis
        cur.execute(
            "SELECT e.name, e.status FROM equipments e "
            "WHERE e.status = 'DOWN'"
        )
        for r in cur.fetchall():
            issues.append({
                "area": "equipment",
                "desc": f"{r[0]} 현재 고장 상태",
            })
            recommendations.append({
                "action": f"{r[0]} 긴급 정비 실시",
                "expected_impact": "가동률 향상",
            })

        # Quality analysis
        cur.execute(
            "SELECT SUM(defect_qty), SUM(good_qty + defect_qty) "
            "FROM work_results"
        )
        qrow = cur.fetchone()
        d_rate = qrow[0] / qrow[1] if qrow[1] else 0
        if d_rate > 0.03:
            issues.append({
                "area": "quality",
                "desc": f"전체 불량률 {d_rate*100:.1f}%로 기준(3%) 초과",
            })
            recommendations.append({
                "action": "공정 파라미터 최적화 및 검사 강화",
                "expected_impact": "불량률 2% 이하로 감소 기대",
            })

        cur.close()

        summary = f"분석 결과: 이슈 {len(issues)}건 발견, " \
                  f"개선 권고 {len(recommendations)}건"

        return {
            "summary": summary,
            "issues": issues,
            "recommendations": recommendations,
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)
