from collections import Counter
from typing import List, Dict, Any

MIN_HAZARD_DOMINANCE = 0.30


def generate_cluster_label(cluster_num: int, reports: List[Dict[str, Any]]) -> str:
    """Synthesize evidence-based cluster label from actual incident narratives and extracted hazards.

    Returns the clean general category without subcategories.
    """
    if cluster_num == -1:
        return "Unclustered / General Safety Outliers"

    if not reports:
        return f"Safety Cluster #{cluster_num}"

    # Extract all hazard categories and equipment
    hazards = []
    equipment = []
    events = []
    words = []

    stop_words = {
        "the", "a", "an", "and", "or", "in", "on", "at", "to", "was", "were",
        "of", "with", "by", "for", "from", "worker", "incident", "victim",
        "died", "killed", "employee", "employees"
    }

    for r in reports:
        ext = r.get("extracted_info") or {}
        if isinstance(ext, dict):
            hazards.extend(ext.get("hazards", []))
            equipment.extend(ext.get("equipment", []))

        if r.get("event"):
            events.append(r["event"])

        desc = r.get("description", "").lower()
        for w in desc.split():
            clean_w = ''.join(c for c in w if c.isalnum())
            if len(clean_w) > 3 and clean_w not in stop_words:
                words.append(clean_w)

    # 1. Primary choice: dominant taxonomy hazard (general category)
    if hazards:
        top_hazard, top_count = Counter(hazards).most_common(1)[0]
        if top_count / len(reports) >= MIN_HAZARD_DOMINANCE:
            return top_hazard

    # 2. Secondary choice: top equipment + "Related Incidents"
    top_eq = Counter(equipment).most_common(1)[0][0] if equipment else None
    if top_eq:
        return f"{top_eq.capitalize()} Related Incidents"

    # 3. Tertiary choice: dominant event
    top_evt = Counter(events).most_common(1)[0][0] if events else None
    if top_evt:
        return top_evt

    # 4. Fallback: top frequent key terms
    top_words = [pair[0].capitalize() for pair in Counter(words).most_common(2)]
    if top_words:
        return f"{' '.join(top_words)} Hazard Pattern"

    return f"Hazard Pattern #{cluster_num}"


def deduplicate_cluster_labels(cluster_labels: Dict[int, str], cluster_reports: Dict[int, List[Dict[str, Any]]]) -> Dict[int, str]:
    """Compatibility pass for label mapping.

    With category consolidation enabled in the pipeline, labels are already unique
    by general category. If duplicate labels are passed, this appends cluster numbers.
    """
    seen = set()
    result = {}
    for c_num in sorted(cluster_labels.keys()):
        lbl = cluster_labels[c_num]
        if lbl in seen:
            result[c_num] = f"{lbl} (#{c_num})"
        else:
            result[c_num] = lbl
        seen.add(result[c_num])

    return result
