from typing import List, Dict, Any, Tuple
from datetime import datetime


def calculate_cluster_risk_score(
    reports: List[Dict[str, Any]],
    max_cluster_size: int,
    recent_trend_ratio: float = 0.5
) -> Dict[str, float]:
    """Calculate 5-factor explainable 0-100 risk score for a cluster."""
    count = len(reports)
    if count == 0:
        return {
            "risk_score": 0.0,
            "frequency": 0.0,
            "near_miss_intensity": 0.0,
            "severity": 0.0,
            "trend": 0.0,
            "recency": 0.0
        }

    # 1. Frequency (25%) - normalized relative to maximum cluster size
    freq_score = min(100.0, (count / max(1, max_cluster_size)) * 100.0)

    # 2. Near-Miss / Precursor Intensity (25%)
    precursor_hits = 0
    fatalities = 0
    hospitalizations = 0
    amputations = 0

    recent_count = 0
    curr_year = datetime.now().year

    for r in reports:
        ext = r.get("extracted_info") or {}
        if isinstance(ext, dict):
            if ext.get("unsafe_actions") or ext.get("unsafe_conditions") or ext.get("hazards"):
                precursor_hits += 1

        sev = r.get("severity_info") or {}
        if sev.get("fatality_or_catastrophe") == "Fatality":
            fatalities += 1
        if str(sev.get("hospitalized")) in ("1", "1.0", "1.00", "True"):
            hospitalizations += 1
        if str(sev.get("amputation")) in ("1", "1.0", "1.00", "True"):
            amputations += 1

        ts = r.get("timestamp")
        if ts and len(ts) >= 4:
            try:
                yr = int(ts[:4])
                if yr >= (curr_year - 5): # recent 5 years window
                    recent_count += 1
            except ValueError:
                pass

    near_miss_score = min(100.0, (precursor_hits / count) * 100.0)

    # 3. Severity (20%)
    sev_rate = ((fatalities * 1.0 + hospitalizations * 0.7 + amputations * 0.8) / count)
    severity_score = min(100.0, sev_rate * 100.0)

    # 4. Trend (20%) - normalized from recent trend ratio
    trend_score = min(100.0, max(0.0, recent_trend_ratio * 100.0))

    # 5. Recency (10%)
    recency_score = min(100.0, (recent_count / count) * 100.0)

    # Weighted sum
    total_risk = (
        freq_score * 0.25 +
        near_miss_score * 0.25 +
        severity_score * 0.20 +
        trend_score * 0.20 +
        recency_score * 0.10
    )

    return {
        "risk_score": round(float(total_risk), 1),
        "frequency": round(float(freq_score), 1),
        "near_miss_intensity": round(float(near_miss_score), 1),
        "severity": round(float(severity_score), 1),
        "trend": round(float(trend_score), 1),
        "recency": round(float(recency_score), 1)
    }
