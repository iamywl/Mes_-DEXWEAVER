from api_modules.database import get_db # REQ-024는 DB 접근이 필요 없지만, 지시사항에 따라 import 유지

async def predict_defect_probability(
    process_params: dict # 예: {"temperature": 200, "pressure": 10, "speed": 50, "humidity": 60}
):
    """
    REQ-024: 공정 파라미터를 입력받아 임계치 기반으로 불량 발생 확률을 예측합니다.
    """
    try:
        # 임계치 설정 (예시 값)
        thresholds = {
            "temperature": {"min": 180, "max": 220, "weight": 0.4},
            "pressure": {"min": 8, "max": 12, "weight": 0.3},
            "speed": {"min": 45, "max": 55, "weight": 0.2},
            "humidity": {"min": 50, "max": 70, "weight": 0.1},
        }
        defect_prob = 0.0
        causes = []

        _ = get_db() # 지시사항 준수를 위한 더미 호출

        for param, config in thresholds.items():
            val = process_params.get(param)
            if val is not None and not (config["min"] <= val <= config["max"]):
                defect_prob += config["weight"]
                causes.append(f"{param} ({val}) out of range ({config["min"]}-{config["max"]}).")

        defect_prob = min(1.0, defect_prob)
        return {
            "defect_probability": round(defect_prob * 100, 2),
            "main_causes": causes if causes else ["No deviations."],
            "recommended_action": "Monitor closely." if defect_prob > 0 else "Stable."
        }
    except Exception as e:
        return {"error": str(e)}