"""REQ-015, FN-018: Demand prediction using Prophet (fallback: linear regression)."""

import logging
from datetime import datetime, timedelta

from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)

# Try importing Prophet
try:
    from prophet import Prophet
    HAS_PROPHET = True
except ImportError:
    HAS_PROPHET = False
    log.warning("Prophet not installed – falling back to linear regression.")


async def predict_demand(
    item_code: str,
    history_months: int = 12,
    prediction_months: int = 3,
) -> dict:
    """Predict future demand based on historical shipment / work_results data.

    Uses Facebook Prophet when available for seasonality decomposition
    and confidence intervals. Falls back to linear regression otherwise.
    """
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "Database connection failed."}

        cursor = conn.cursor()

        # Try shipments table first, fall back to work_results
        cursor.execute(
            "SELECT EXISTS ("
            "  SELECT 1 FROM information_schema.tables "
            "  WHERE table_name = 'shipments'"
            ")"
        )
        has_shipments = cursor.fetchone()[0]

        if has_shipments:
            cursor.execute(
                "SELECT date_trunc('month', ship_date)::date AS ds, "
                "SUM(qty) AS y "
                "FROM shipments WHERE item_code = %s "
                "GROUP BY ds ORDER BY ds "
                "LIMIT %s",
                (item_code, history_months),
            )
        else:
            # Use work_results + work_orders as demand proxy
            cursor.execute(
                "SELECT date_trunc('month', wr.start_time)::date AS ds, "
                "SUM(wr.good_qty) AS y "
                "FROM work_results wr "
                "JOIN work_orders wo ON wr.wo_id = wo.wo_id "
                "WHERE wo.item_code = %s "
                "GROUP BY ds ORDER BY ds "
                "LIMIT %s",
                (item_code, history_months),
            )

        rows = cursor.fetchall()
        cursor.close()

        if len(rows) < 3:
            return {
                "error": "Not enough historical data for prediction.",
                "rows_found": len(rows),
            }

        if HAS_PROPHET and len(rows) >= 4:
            return _prophet_predict(rows, prediction_months, item_code)
        else:
            return _linear_predict(rows, prediction_months, item_code)

    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


def _prophet_predict(rows, prediction_months, item_code):
    """Prophet-based prediction with seasonality and confidence intervals."""
    import pandas as pd

    df = pd.DataFrame(rows, columns=["ds", "y"])
    df["ds"] = pd.to_datetime(df["ds"])
    df["y"] = df["y"].astype(float)

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        seasonality_mode="multiplicative",
    )
    model.fit(df)

    future = model.make_future_dataframe(periods=prediction_months, freq="MS")
    forecast = model.predict(future)

    # Extract predictions (future only)
    pred_df = forecast.tail(prediction_months)
    predictions = []
    for _, row in pred_df.iterrows():
        predictions.append({
            "month": row["ds"].strftime("%Y-%m"),
            "predicted_qty": max(0, int(round(row["yhat"]))),
            "lower_bound": max(0, int(round(row["yhat_lower"]))),
            "upper_bound": max(0, int(round(row["yhat_upper"]))),
        })

    # Seasonality components
    components = []
    if hasattr(model, "seasonalities") and "yearly" in model.seasonalities:
        yearly = forecast[["ds", "yearly"]].tail(12)
        components = [
            {"month": r["ds"].strftime("%Y-%m"), "seasonal_effect": round(float(r["yearly"]), 3)}
            for _, r in yearly.iterrows()
        ]

    return {
        "item_code": item_code,
        "model": "Prophet",
        "data_points_used": len(rows) - prediction_months if len(rows) > prediction_months else len(rows),
        "predictions": predictions,
        "seasonality": components,
    }


def _linear_predict(rows, prediction_months, item_code):
    """Fallback linear regression prediction."""
    past_data = [(i + 1, float(row[1])) for i, row in enumerate(rows)]
    n = len(past_data)

    sum_x = sum(m for m, _ in past_data)
    sum_y = sum(q for _, q in past_data)
    sum_xy = sum(m * q for m, q in past_data)
    sum_x2 = sum(m ** 2 for m, _ in past_data)

    denominator = n * sum_x2 - sum_x ** 2
    if denominator == 0:
        return {"error": "Insufficient variance in historical data."}

    slope = (n * sum_xy - sum_x * sum_y) / denominator
    intercept = (sum_y - slope * sum_x) / n

    # Calculate residual std for confidence interval
    residuals = [(q - (slope * m + intercept)) ** 2 for m, q in past_data]
    rmse = (sum(residuals) / n) ** 0.5

    last_date = rows[-1][0]
    predictions = []
    for i in range(1, prediction_months + 1):
        predicted_month = n + i
        predicted_demand = slope * predicted_month + intercept
        pred_val = max(0, int(predicted_demand))

        # Approximate month label
        if isinstance(last_date, datetime):
            month_dt = last_date + timedelta(days=30 * i)
        else:
            month_dt = datetime.now() + timedelta(days=30 * i)

        predictions.append({
            "month": month_dt.strftime("%Y-%m"),
            "predicted_qty": pred_val,
            "lower_bound": max(0, int(predicted_demand - 1.96 * rmse)),
            "upper_bound": max(0, int(predicted_demand + 1.96 * rmse)),
        })

    return {
        "item_code": item_code,
        "model": "LinearRegression",
        "data_points_used": n,
        "predictions": predictions,
    }
