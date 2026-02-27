"""FN-035~037: Reports and statistical analysis insights module."""

import logging
import math
from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)


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
    """FN-036: Quality analysis report with defect rate, Cpk, and control chart."""
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

        # Defect rate
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

        # --- Proper Cpk calculation: Cpk = min((USL-μ), (μ-LSL)) / 3σ ---
        cpk = None
        control_chart = None

        # Build inspection filter
        insp_where = []
        insp_params = []
        if start_date:
            insp_where.append("i.inspected_at >= %s")
            insp_params.append(start_date)
        if end_date:
            insp_where.append("i.inspected_at <= %s")
            insp_params.append(end_date)
        if item_code:
            insp_where.append("i.item_code = %s")
            insp_params.append(item_code)
        insp_wsql = ("WHERE " + " AND ".join(insp_where)) if insp_where else ""

        # Get measured values from inspection_details
        cur.execute(
            f"SELECT d.check_name, d.measured_value "
            f"FROM inspection_details d "
            f"JOIN inspections i ON d.inspection_id = i.inspection_id "
            f"{insp_wsql} "
            f"ORDER BY i.inspected_at",
            insp_params,
        )
        measurements = cur.fetchall()

        if measurements:
            # Group by check_name, pick the one with most data points
            groups = {}
            for check_name, val in measurements:
                if val is not None:
                    groups.setdefault(check_name, []).append(float(val))

            if groups:
                # Use the check with the most measurements
                best_check = max(groups, key=lambda k: len(groups[k]))
                values = groups[best_check]

                # Get USL/LSL from quality_standards
                qs_where = "WHERE check_name = %s"
                qs_params = [best_check]
                if item_code:
                    qs_where += " AND item_code = %s"
                    qs_params.append(item_code)

                cur.execute(
                    f"SELECT min_value, max_value FROM quality_standards "
                    f"{qs_where} LIMIT 1",
                    qs_params,
                )
                std_row = cur.fetchone()

                if std_row and std_row[0] is not None and std_row[1] is not None:
                    lsl = float(std_row[0])
                    usl = float(std_row[1])

                    n = len(values)
                    mean = sum(values) / n
                    if n > 1:
                        variance = sum((v - mean) ** 2 for v in values) / (n - 1)
                        sigma = math.sqrt(variance)
                    else:
                        sigma = 0

                    if sigma > 0:
                        cpu = (usl - mean) / (3 * sigma)
                        cpl = (mean - lsl) / (3 * sigma)
                        cpk = round(min(cpu, cpl), 2)
                    else:
                        cpk = round((usl - lsl) / 6, 2) if usl > lsl else 0

                    # Control chart data (X-bar chart)
                    cl = round(mean, 4)
                    ucl = round(mean + 3 * sigma, 4) if sigma > 0 else round(usl, 4)
                    lcl = round(mean - 3 * sigma, 4) if sigma > 0 else round(lsl, 4)
                    control_chart = {
                        "ucl": ucl,
                        "lcl": lcl,
                        "cl": cl,
                        "values": [round(v, 4) for v in values],
                    }

        # Fallback: estimate Cpk from defect rate when no inspection measurement data exists.
        # Real Cpk = min((USL-μ), (μ-LSL)) / 3σ is computed above when inspection data is available.
        if cpk is None:
            cpk = round(max(0, (1 - defect_rate * 10) * 1.33), 2)

        cur.close()
        result = {
            "defect_rate": defect_rate,
            "trend": trend,
            "cpk": cpk,
        }
        if control_chart:
            result["control_chart"] = control_chart
        return result
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


def _linear_trend(values):
    """Compute linear regression slope and R² for a numeric series.

    Uses ordinary least squares: y = a + b*x.
    Returns (slope, r_squared, direction) where direction is UP/DOWN/STABLE.
    """
    n = len(values)
    if n < 2:
        return 0, 0, "STABLE"
    xs = list(range(n))
    x_mean = sum(xs) / n
    y_mean = sum(values) / n
    ss_xy = sum((xs[i] - x_mean) * (values[i] - y_mean) for i in range(n))
    ss_xx = sum((xs[i] - x_mean) ** 2 for i in range(n))
    ss_yy = sum((values[i] - y_mean) ** 2 for i in range(n))
    if ss_xx == 0:
        return 0, 0, "STABLE"
    slope = ss_xy / ss_xx
    r_sq = (ss_xy ** 2) / (ss_xx * ss_yy) if ss_yy > 0 else 0
    direction = "UP" if slope > 0 else "DOWN" if slope < 0 else "STABLE"
    return round(slope, 4), round(r_sq, 4), direction


def _moving_avg_anomaly(values, window=3, threshold=2.0):
    """Detect anomalies using moving average ± threshold*σ.

    Returns list of (index, value, z_score) for outlier points.
    """
    if len(values) < window + 1:
        return []
    anomalies = []
    for i in range(window, len(values)):
        win = values[i - window:i]
        mu = sum(win) / window
        sigma = math.sqrt(sum((v - mu) ** 2 for v in win) / window) if window > 1 else 0
        if sigma > 0:
            z = (values[i] - mu) / sigma
            if abs(z) > threshold:
                anomalies.append((i, values[i], round(z, 2)))
    return anomalies


async def ai_insights(data: dict) -> dict:
    """FN-037: Statistical analysis engine for production/quality/equipment/inventory.

    Analysis methods:
    - Linear regression trend detection (slope + R²)
    - Moving average anomaly detection (z-score)
    - Threshold-based KPI monitoring
    - Cross-metric correlation analysis
    """
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "DB connection failed."}
        cur = conn.cursor()
        focus = data.get("focus_area", "all")

        issues = []
        recommendations = []
        kpis = {}
        analysis_methods = []

        # ── 1. Production Analysis ──────────────────────────
        if focus in ("all", "production"):
            cur.execute(
                "SELECT i.name, i.item_code, SUM(wr.good_qty), SUM(wo.plan_qty) "
                "FROM work_results wr "
                "JOIN work_orders wo ON wr.wo_id = wo.wo_id "
                "JOIN items i ON wo.item_code = i.item_code "
                "GROUP BY i.name, i.item_code"
            )
            prod_rows = cur.fetchall()
            total_good = sum(r[2] or 0 for r in prod_rows)
            total_plan = sum(r[3] or 0 for r in prod_rows)
            overall_rate = total_good / total_plan if total_plan else 0
            kpis["production_achievement"] = round(overall_rate * 100, 1)

            underperforming = []
            for r in prod_rows:
                rate = (r[2] or 0) / r[3] if r[3] else 0
                if rate < 0.9:
                    underperforming.append({"item": r[0], "code": r[1], "rate": rate})
                    issues.append({
                        "area": "production", "severity": "HIGH" if rate < 0.7 else "MEDIUM",
                        "desc": f"{r[0]} 달성률 {rate*100:.0f}%로 목표(90%) 미달",
                    })

            if underperforming:
                worst = min(underperforming, key=lambda x: x["rate"])
                recommendations.append({
                    "area": "production", "priority": "HIGH",
                    "action": f"{worst['item']} 생산라인 병목 분석 및 설비 점검",
                    "expected_impact": f"달성률 {worst['rate']*100:.0f}% → {min(100,(worst['rate']+0.15)*100):.0f}% 향상 기대",
                    "detail": f"미달 품목 {len(underperforming)}건 중 최저 달성률 품목 우선 개선",
                })

            # Linear regression trend on daily production (last 14 days)
            cur.execute(
                "SELECT wr.start_time::date, SUM(wr.good_qty) "
                "FROM work_results wr "
                "WHERE wr.start_time >= NOW() - INTERVAL '14 days' "
                "GROUP BY 1 ORDER BY 1"
            )
            daily_prod = cur.fetchall()
            if len(daily_prod) >= 3:
                prod_values = [float(r[1] or 0) for r in daily_prod]
                slope, r_sq, direction = _linear_trend(prod_values)
                kpis["production_trend_slope"] = slope
                kpis["production_trend_r2"] = r_sq
                kpis["production_trend_direction"] = direction
                analysis_methods.append("linear_regression_production")

                if direction == "DOWN" and r_sq > 0.3:
                    issues.append({
                        "area": "production", "severity": "MEDIUM",
                        "desc": f"일간 생산량 하락 추세 (기울기={slope:.1f}, R²={r_sq:.2f})",
                    })
                    recommendations.append({
                        "area": "production", "priority": "MEDIUM",
                        "action": "생산량 감소 원인 분석 (설비 점검, 자재 부족 확인)",
                        "expected_impact": "하락 추세 반전 기대",
                        "detail": f"14일간 선형회귀 분석: 기울기 {slope:.1f}, 결정계수 R²={r_sq:.2f}",
                    })

                # Moving average anomaly detection on daily production
                anomalies = _moving_avg_anomaly(prod_values, window=3, threshold=2.0)
                if anomalies:
                    analysis_methods.append("moving_avg_anomaly_production")
                    for idx, val, z in anomalies:
                        date_str = str(daily_prod[idx][0])
                        issues.append({
                            "area": "production", "severity": "MEDIUM",
                            "desc": f"{date_str} 생산량 이상치 감지 ({val:.0f}개, z-score={z:.1f})",
                        })

        # ── 2. Equipment Analysis ───────────────────────────
        if focus in ("all", "equipment"):
            cur.execute(
                "SELECT e.equip_code, e.name, e.status, e.capacity_per_hour "
                "FROM equipments e"
            )
            equip_rows = cur.fetchall()
            total_equip = len(equip_rows)
            down_equips = [r for r in equip_rows if r[2] == "DOWN"]
            stop_equips = [r for r in equip_rows if r[2] == "STOP"]
            running = total_equip - len(down_equips) - len(stop_equips)

            kpis["equipment_availability"] = round(running / total_equip * 100, 1) if total_equip else 0
            kpis["equipment_down"] = len(down_equips)

            for r in down_equips:
                cur.execute(
                    "SELECT changed_at FROM equip_status_log "
                    "WHERE equip_code = %s AND status = 'DOWN' "
                    "ORDER BY changed_at DESC LIMIT 1",
                    (r[0],),
                )
                down_since = cur.fetchone()
                down_hours = 0
                if down_since and down_since[0]:
                    from datetime import datetime as dt
                    down_hours = (dt.now() - down_since[0]).total_seconds() / 3600

                severity = "CRITICAL" if down_hours > 24 else "HIGH"
                issues.append({
                    "area": "equipment", "severity": severity,
                    "desc": f"{r[1]}({r[0]}) 고장 상태 ({down_hours:.0f}시간 경과)",
                })
                lost_capacity = r[3] * down_hours if r[3] else 0
                recommendations.append({
                    "area": "equipment", "priority": "URGENT",
                    "action": f"{r[1]} 긴급 정비 실시",
                    "expected_impact": f"시간당 {r[3]}개 생산능력 복구, 손실 약 {lost_capacity:.0f}개",
                    "detail": f"고장 발생 후 {down_hours:.0f}시간 경과",
                })

            # Sensor trend analysis per equipment (vibration/temperature)
            cur.execute(
                "SELECT es.equip_code, e.name, "
                "AVG(es.vibration), STDDEV(es.vibration), MAX(es.vibration), "
                "AVG(es.temperature), STDDEV(es.temperature), MAX(es.temperature), "
                "COUNT(*) "
                "FROM equip_sensors es "
                "JOIN equipments e ON es.equip_code = e.equip_code "
                "WHERE es.recorded_at >= NOW() - INTERVAL '7 days' "
                "GROUP BY es.equip_code, e.name "
                "HAVING COUNT(*) >= 3"
            )
            sensor_rows = cur.fetchall()
            for r in sensor_rows:
                vib_avg, vib_std, vib_max = float(r[2] or 0), float(r[3] or 0), float(r[4] or 0)
                temp_avg, temp_std, temp_max = float(r[5] or 0), float(r[6] or 0), float(r[7] or 0)
                analysis_methods.append("sensor_statistical_analysis")

                # Z-score based anomaly: max > avg + 2σ
                vib_anomaly = vib_std > 0 and vib_max > vib_avg + 2 * vib_std
                temp_anomaly = temp_std > 0 and temp_max > temp_avg + 2 * temp_std

                if vib_anomaly or temp_anomaly or vib_max > 3.0 or temp_max > 60:
                    details = []
                    if vib_anomaly or vib_max > 3.0:
                        details.append(f"진동 max={vib_max:.1f} (μ={vib_avg:.1f}±{vib_std:.1f}σ)")
                    if temp_anomaly or temp_max > 60:
                        details.append(f"온도 max={temp_max:.1f}°C (μ={temp_avg:.1f}±{temp_std:.1f}σ)")
                    issues.append({
                        "area": "equipment", "severity": "MEDIUM",
                        "desc": f"{r[1]}({r[0]}) 센서 이상 - {', '.join(details)}",
                    })
                    recommendations.append({
                        "area": "equipment", "priority": "HIGH",
                        "action": f"{r[1]} 예방정비 스케줄 앞당김 권장",
                        "expected_impact": "예기치 않은 고장 방지",
                        "detail": f"7일간 센서 통계: {', '.join(details)} (데이터포인트: {r[8]}건)",
                    })

        # ── 3. Quality Analysis ─────────────────────────────
        if focus in ("all", "quality"):
            cur.execute(
                "SELECT SUM(defect_qty), SUM(good_qty + defect_qty) "
                "FROM work_results"
            )
            qrow = cur.fetchone()
            total_defects = qrow[0] or 0
            total_produced = qrow[1] or 0
            d_rate = total_defects / total_produced if total_produced else 0
            kpis["defect_rate"] = round(d_rate * 100, 2)

            if d_rate > 0.05:
                severity = "CRITICAL"
            elif d_rate > 0.03:
                severity = "HIGH"
            else:
                severity = None

            if severity:
                issues.append({
                    "area": "quality", "severity": severity,
                    "desc": f"전체 불량률 {d_rate*100:.1f}%로 기준(3%) 초과",
                })
                recommendations.append({
                    "area": "quality", "priority": "HIGH",
                    "action": "공정 파라미터 최적화 및 검사 강화",
                    "expected_impact": f"불량률 {d_rate*100:.1f}% → 2% 이하 감소 기대",
                    "detail": f"총 불량 {total_defects}건 / 생산 {total_produced}건",
                })

            # Linear regression on daily defect rate (last 14 days)
            cur.execute(
                "SELECT wr.start_time::date, "
                "SUM(wr.defect_qty)::float / NULLIF(SUM(wr.good_qty + wr.defect_qty), 0) "
                "FROM work_results wr "
                "WHERE wr.start_time >= NOW() - INTERVAL '14 days' "
                "GROUP BY 1 ORDER BY 1"
            )
            daily_defect = cur.fetchall()
            if len(daily_defect) >= 3:
                defect_values = [float(r[1] or 0) for r in daily_defect]
                slope, r_sq, direction = _linear_trend(defect_values)
                kpis["defect_trend_slope"] = slope
                kpis["defect_trend_r2"] = r_sq
                kpis["defect_trend_direction"] = direction
                analysis_methods.append("linear_regression_quality")

                if direction == "UP" and r_sq > 0.3:
                    issues.append({
                        "area": "quality", "severity": "MEDIUM",
                        "desc": f"불량률 상승 추세 (기울기={slope:.4f}, R²={r_sq:.2f})",
                    })
                    recommendations.append({
                        "area": "quality", "priority": "HIGH",
                        "action": "불량률 상승 원인 분석 (공정 파라미터 변동, 자재 품질 점검)",
                        "expected_impact": "불량률 추세 반전",
                        "detail": f"14일간 선형회귀: 기울기 {slope:.4f}, R²={r_sq:.2f}",
                    })

                # Moving average anomaly on defect rate
                anomalies = _moving_avg_anomaly(defect_values, window=3, threshold=2.0)
                if anomalies:
                    analysis_methods.append("moving_avg_anomaly_quality")
                    for idx, val, z in anomalies:
                        date_str = str(daily_defect[idx][0])
                        issues.append({
                            "area": "quality", "severity": "MEDIUM",
                            "desc": f"{date_str} 불량률 이상치 ({val*100:.1f}%, z-score={z:.1f})",
                        })

        # ── 4. Inventory Analysis ───────────────────────────
        if focus in ("all", "inventory"):
            cur.execute(
                "SELECT i.item_code, i.name, "
                "COALESCE(SUM(inv.qty), 0), COALESCE(i.safety_stock, 0) "
                "FROM items i "
                "LEFT JOIN inventory inv ON i.item_code = inv.item_code "
                "GROUP BY i.item_code, i.name, i.safety_stock "
                "HAVING COALESCE(SUM(inv.qty), 0) < COALESCE(i.safety_stock, 0) "
                "AND COALESCE(i.safety_stock, 0) > 0"
            )
            low_stock = cur.fetchall()
            if low_stock:
                kpis["low_stock_items"] = len(low_stock)
                for r in low_stock:
                    shortage_ratio = round((1 - float(r[2]) / float(r[3])) * 100, 1)
                    issues.append({
                        "area": "inventory", "severity": "HIGH" if shortage_ratio > 50 else "MEDIUM",
                        "desc": f"{r[1]}({r[0]}) 재고 {r[2]}개 < 안전재고 {r[3]}개 (부족률 {shortage_ratio}%)",
                    })
                if len(low_stock) >= 3:
                    recommendations.append({
                        "area": "inventory", "priority": "HIGH",
                        "action": f"안전재고 미달 {len(low_stock)}건 긴급 발주 검토",
                        "expected_impact": "생산 중단 위험 해소",
                        "detail": ", ".join(f"{r[1]}" for r in low_stock[:5]),
                    })

        # ── 5. Cross-metric Correlation ─────────────────────
        if focus == "all":
            # Check if equipment downtime correlates with production drop
            cur.execute(
                "SELECT date_trunc('day', esl.changed_at)::date AS d, "
                "COUNT(*) FILTER (WHERE esl.status = 'DOWN') AS down_events "
                "FROM equip_status_log esl "
                "WHERE esl.changed_at >= NOW() - INTERVAL '14 days' "
                "GROUP BY 1 ORDER BY 1"
            )
            down_daily = {str(r[0]): r[1] for r in cur.fetchall()}

            cur.execute(
                "SELECT wr.start_time::date, SUM(wr.good_qty) "
                "FROM work_results wr "
                "WHERE wr.start_time >= NOW() - INTERVAL '14 days' "
                "GROUP BY 1 ORDER BY 1"
            )
            prod_daily = {str(r[0]): float(r[1] or 0) for r in cur.fetchall()}

            common_dates = sorted(set(down_daily.keys()) & set(prod_daily.keys()))
            if len(common_dates) >= 5:
                down_vals = [down_daily[d] for d in common_dates]
                prod_vals = [prod_daily[d] for d in common_dates]
                n = len(common_dates)
                d_mean = sum(down_vals) / n
                p_mean = sum(prod_vals) / n
                cov = sum((down_vals[i] - d_mean) * (prod_vals[i] - p_mean) for i in range(n)) / n
                d_std = math.sqrt(sum((v - d_mean) ** 2 for v in down_vals) / n)
                p_std = math.sqrt(sum((v - p_mean) ** 2 for v in prod_vals) / n)
                corr = cov / (d_std * p_std) if d_std > 0 and p_std > 0 else 0
                kpis["downtime_production_correlation"] = round(corr, 3)
                analysis_methods.append("cross_correlation")

                if corr < -0.5:
                    issues.append({
                        "area": "production", "severity": "HIGH",
                        "desc": f"설비 고장과 생산량 간 강한 음의 상관관계 (r={corr:.2f})",
                    })
                    recommendations.append({
                        "area": "equipment", "priority": "HIGH",
                        "action": "예방정비 강화 → 생산량 안정화",
                        "expected_impact": "설비 고장 감소 → 생산량 변동 축소",
                        "detail": f"피어슨 상관계수 r={corr:.2f} (14일간 일별 데이터 {n}건)",
                    })

        cur.close()

        # ── Generate Summary ────────────────────────────────
        critical_count = sum(1 for i in issues if i.get("severity") in ("CRITICAL", "HIGH"))
        medium_count = sum(1 for i in issues if i.get("severity") == "MEDIUM")

        summary_parts = [f"통계 분석 결과: 이슈 {len(issues)}건 발견"]
        if critical_count:
            summary_parts.append(f"긴급 {critical_count}건")
        if medium_count:
            summary_parts.append(f"주의 {medium_count}건")
        summary_parts.append(f"개선 권고 {len(recommendations)}건")
        summary = ", ".join(summary_parts)

        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        issues.sort(key=lambda x: severity_order.get(x.get("severity", "LOW"), 3))

        # Deduplicate analysis methods
        unique_methods = list(dict.fromkeys(analysis_methods))

        return {
            "summary": summary,
            "kpis": kpis,
            "issues": issues,
            "recommendations": recommendations,
            "analysis_methods": unique_methods,
        }
    except Exception as e:
        log.error("AI insights error: %s", e)
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)
