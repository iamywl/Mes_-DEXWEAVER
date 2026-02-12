"""REQ-015: Demand prediction using linear regression on shipment history."""

from api_modules.database import get_db, release_conn


async def predict_demand(
    item_code: str,
    history_months: int = 12,
    prediction_months: int = 3,
):
    """Predict future demand based on historical shipment data.

    Args:
        item_code: Target item code.
        history_months: Number of past months to use.
        prediction_months: Number of future months to predict.

    Returns:
        Dict with item_code, data_points_used, and predictions list.
    """
    conn = None
    try:
        conn = get_db()
        if not conn:
            return {"error": "Database connection failed."}

        cursor = conn.cursor()

        query = """
            SELECT
                EXTRACT(EPOCH FROM date_trunc('month', ship_date))
                    AS month_epoch,
                SUM(qty) AS monthly_qty
            FROM shipments
            WHERE item_code = %s
            GROUP BY date_trunc('month', ship_date)
            ORDER BY date_trunc('month', ship_date) DESC
            LIMIT %s;
        """
        cursor.execute(query, (item_code, history_months))
        rows = cursor.fetchall()
        cursor.close()

        if len(rows) < 3:
            return {
                "error": "Not enough historical data for prediction.",
                "rows_found": len(rows),
            }

        # Reverse to chronological order and assign month offsets
        rows.reverse()
        past_data = [(i + 1, row[1]) for i, row in enumerate(rows)]
        n = len(past_data)

        # Simple linear regression (y = mx + b)
        sum_x = sum(m for m, _ in past_data)
        sum_y = sum(q for _, q in past_data)
        sum_xy = sum(m * q for m, q in past_data)
        sum_x2 = sum(m ** 2 for m, _ in past_data)

        denominator = n * sum_x2 - sum_x ** 2
        if denominator == 0:
            return {"error": "Insufficient variance in historical data."}

        slope = (n * sum_xy - sum_x * sum_y) / denominator
        intercept = (sum_y - slope * sum_x) / n

        predictions = []
        for i in range(1, prediction_months + 1):
            predicted_month = n + i
            predicted_demand = slope * predicted_month + intercept
            predictions.append({
                "month_offset": predicted_month,
                "predicted_qty": max(0, int(predicted_demand)),
            })

        return {
            "item_code": item_code,
            "data_points_used": n,
            "predictions": predictions,
        }

    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)
