from collections import defaultdict
from typing import List, Dict, Any, Tuple
import numpy as np


def aggregate_monthly_counts(reports: List[Dict[str, Any]]) -> List[Tuple[str, int]]:
    """Group reports by month YYYY-MM and return sorted list of (month, count)."""
    monthly = defaultdict(int)
    for r in reports:
        ts = r.get("timestamp")
        if ts and len(ts) >= 7:
            month_key = ts[:7]  # YYYY-MM
            monthly[month_key] += 1

    if not monthly:
        return []

    sorted_months = sorted(monthly.keys())
    min_m, max_m = sorted_months[0], sorted_months[-1]
    
    # Fill in gap months
    result = []
    y_curr, m_curr = int(min_m[:4]), int(min_m[5:7])
    y_end, m_end = int(max_m[:4]), int(max_m[5:7])
    
    while (y_curr < y_end) or (y_curr == y_end and m_curr <= m_end):
        m_str = f"{y_curr:04d}-{m_curr:02d}"
        result.append((m_str, monthly.get(m_str, 0)))
        m_curr += 1
        if m_curr > 12:
            m_curr = 1
            y_curr += 1

    return result


def classify_trend(monthly_data: List[Tuple[str, int]]) -> Tuple[str, float]:
    """Analyze monthly time series and classify trajectory & return recent trend ratio."""
    if len(monthly_data) < 2:
        return "Stable", 0.5

    counts = np.array([c for _, c in monthly_data], dtype=float)
    x = np.arange(len(counts))

    if np.sum(counts) == 0 or np.std(counts) == 0:
        return "Stable", 0.5

    # Compute linear slope
    slope, _ = np.polyfit(x, counts, 1)

    # Compare recent half vs older half
    mid = len(counts) // 2
    older_avg = np.mean(counts[:mid]) if mid > 0 else 0
    recent_avg = np.mean(counts[mid:])
    
    total_avg = np.mean(counts)
    trend_ratio = min(1.0, max(0.0, float(recent_avg / (older_avg + 1e-5)) / 2.0))

    # Check for emerging (low initial count, sudden jump in recent 3 months)
    if len(counts) >= 6 and np.sum(counts[:mid]) <= 2 and recent_avg > 3:
        return "Emerging", max(0.8, trend_ratio)

    if slope > 0.15 or (recent_avg > older_avg * 1.3 and recent_avg > 2):
        return "Increasing", max(0.7, trend_ratio)
    elif slope < -0.15 or (recent_avg < older_avg * 0.7):
        return "Decreasing", min(0.3, trend_ratio)
    elif np.std(counts) / (total_avg + 1e-5) > 0.8:
        return "Fluctuating", 0.5
    else:
        return "Stable", 0.5
