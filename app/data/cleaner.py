import re
from datetime import datetime
from typing import List, Dict, Any, Tuple


def normalize_date(date_str: str) -> str:
    """Normalize date string to ISO format YYYY-MM-DD."""
    if not date_str:
        return None
    cleaned = date_str.strip()
    # Common formats: 1/1/2015, 09/20/09, 2015-01-01, 10/1/2011
    formats = [
        "%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d", "%d/%m/%Y",
        "%B %d, %Y", "%b %d, %Y", "%m-%d-%Y"
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(cleaned, fmt)
            # Adjust two-digit years (e.g. 09 -> 2009 or 1909)
            if dt.year < 1950:
                dt = dt.replace(year=dt.year + 100)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    # Regex fallback for M/D/YYYY or M/D/YY
    match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', cleaned)
    if match:
        m, d, y = int(match.group(1)), int(match.group(2)), int(match.group(3))
        if y < 100:
            y += 2000 if y < 50 else 1900
        try:
            return datetime(y, m, d).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None


def clean_records(raw_records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Clean records and produce profiling summary."""
    cleaned = []
    seen = set()
    invalid_count = 0
    missing_desc_count = 0
    
    states_set = set()
    industries_set = set()
    event_cats = {}
    severity_counts = {"fatality": 0, "hospitalized": 0, "amputation": 0, "other": 0}

    for rec in raw_records:
        desc = rec.get("description", "").strip()
        if not desc or len(desc) < 5:
            invalid_count += 1
            missing_desc_count += 1
            continue

        ts = normalize_date(rec.get("raw_date"))
        rec["timestamp"] = ts
        rec["description"] = desc

        # Deduplication key
        dedup_key = (ts, (rec.get("employer") or "").lower(), desc.lower()[:50])
        if dedup_key in seen:
            invalid_count += 1
            continue
        seen.add(dedup_key)

        cleaned.append(rec)

        # Profile tracking
        if rec.get("state"):
            states_set.add(rec["state"])
        if rec.get("industry"):
            industries_set.add(rec["industry"])
        if rec.get("event"):
            evt = rec["event"]
            event_cats[evt] = event_cats.get(evt, 0) + 1

        sev = rec.get("severity_info") or {}
        if sev.get("fatality_or_catastrophe") == "Fatality":
            severity_counts["fatality"] += 1
        elif str(sev.get("hospitalized")) in ("1", "1.0", "1.00", "True"):
            severity_counts["hospitalized"] += 1
        elif str(sev.get("amputation")) in ("1", "1.0", "1.00", "True"):
            severity_counts["amputation"] += 1
        else:
            severity_counts["other"] += 1

    valid_dates = [r["timestamp"] for r in cleaned if r["timestamp"]]
    min_date = min(valid_dates) if valid_dates else None
    max_date = max(valid_dates) if valid_dates else None

    profile_summary = {
        "total_records": len(raw_records),
        "valid_records": len(cleaned),
        "invalid_records": invalid_count,
        "missing_descriptions": missing_desc_count,
        "date_range": {"min": min_date, "max": max_date},
        "unique_states": len(states_set),
        "unique_industries": len(industries_set),
        "top_event_categories": sorted(event_cats.items(), key=lambda x: x[1], reverse=True)[:5],
        "severity_breakdown": severity_counts
    }

    return cleaned, profile_summary
