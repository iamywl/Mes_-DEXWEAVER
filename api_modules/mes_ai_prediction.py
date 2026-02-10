from api_modules.database import get_db

async def predict_demand(item_code: str, history_months: int = 12, prediction_months: int = 3):
    """
    REQ-015: 과거 출하 데이터를 기반으로 단순 선형 회귀를 이용한 수요 예측.
    """
    try:
        conn = get_db()
        cursor = conn.cursor()

        # 더미 데이터 또는 실제 데이터 로딩 (여기서는 더미 데이터)
        # 실제 구현에서는 history_months에 해당하는 과거 출하 데이터를 DB에서 조회해야 합니다.
        # 예시: SELECT date_trunc('month', ship_date), SUM(qty) FROM shipments WHERE item_code = %s GROUP BY 1 ORDER BY 1 DESC LIMIT %s
        # 여기서는 단순화를 위해 고정된 과거 데이터를 사용합니다.
        past_data = [
            (1, 100), (2, 110), (3, 105), (4, 120), (5, 115), (6, 130),
            (7, 125), (8, 140), (9, 135), (10, 150), (11, 145), (12, 160)
        ] # (month_offset, demand_qty)

        if len(past_data) < history_months:
            return {"error": "Not enough historical data for prediction."}

        # 단순 선형 회귀 (y = mx + b)
        # x = 월 오프셋 (1, 2, ... history_months)
        # y = 수요량
        n = history_months
        sum_x = sum(m for m, _ in past_data[:n])
        sum_y = sum(q for _, q in past_data[:n])
        sum_xy = sum(m * q for m, q in past_data[:n])
        sum_x2 = sum(m**2 for m, _ in past_data[:n])

        # 분모가 0이 되는 경우 방지
        denominator = (n * sum_x2 - sum_x**2)
        if denominator == 0:
            return {"error": "Insufficient variance in historical data for linear regression."}

        m = (n * sum_xy - sum_x * sum_y) / denominator # 기울기
        b = (sum_y - m * sum_x) / n # y 절편

        predictions = []
        for i in range(1, prediction_months + 1):
            predicted_month = history_months + i
            predicted_demand = m * predicted_month + b
            predictions.append({"month_offset": predicted_month, "predicted_qty": max(0, int(predicted_demand))})

        cursor.close()
        conn.close()
        return {"item_code": item_code, "predictions": predictions}

    except Exception as e:
        if 'conn' in locals() and conn:
            conn.close()
        return {"error": str(e)}
