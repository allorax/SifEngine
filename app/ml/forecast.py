from typing import List, Tuple, Dict, Any
import numpy as np


def generate_cluster_forecast(monthly_data: List[Tuple[str, int]], forecast_horizon: int = 6) -> List[Dict[str, Any]]:
    """Forecast future monthly counts for a cluster using statsmodels exponential smoothing or linear trend."""
    if not monthly_data:
        return []

    last_month_str = monthly_data[-1][0]
    y_curr, m_curr = int(last_month_str[:4]), int(last_month_str[5:7])

    future_months = []
    for _ in range(forecast_horizon):
        m_curr += 1
        if m_curr > 12:
            m_curr = 1
            y_curr += 1
        future_months.append(f"{y_curr:04d}-{m_curr:02d}")

    counts = np.array([c for _, c in monthly_data], dtype=float)

    # 1. Handle constant or zero counts or very short series
    if len(counts) < 3 or np.std(counts) == 0 or np.sum(counts) == 0:
        base_val = round(float(np.mean(counts)), 1) if len(counts) > 0 else 0.0
        return [{"month": m, "predicted_count": max(0.0, base_val)} for m in future_months]

    # 2. Try statsmodels ExponentialSmoothing / Holt
    predictions = None
    try:
        from statsmodels.tsa.api import SimpleExpSmoothing, Holt
        if len(counts) >= 6:
            model = Holt(counts, initialization_method="estimated").fit(smoothing_level=0.3, smoothing_trend=0.1)
        else:
            model = SimpleExpSmoothing(counts, initialization_method="estimated").fit(smoothing_level=0.3)
        predictions = model.forecast(forecast_horizon)
    except Exception:
        # Fallback to linear regression trend
        x = np.arange(len(counts))
        slope, intercept = np.polyfit(x, counts, 1)
        future_x = np.arange(len(counts), len(counts) + forecast_horizon)
        predictions = slope * future_x + intercept

    forecast_results = []
    for m, p in zip(future_months, predictions):
        val = max(0.0, round(float(p), 1))
        forecast_results.append({
            "month": m,
            "predicted_count": val
        })

    return forecast_results
