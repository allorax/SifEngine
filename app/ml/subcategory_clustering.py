"""Subcategory clustering and labeling for category drill-down analysis."""

from collections import Counter
from typing import List, Dict, Any, Tuple
import numpy as np
from sklearn.preprocessing import normalize

from app.ml.risk import calculate_cluster_risk_score
from app.nlp.extractors import _extract_rule_info

_SUB_CONTEXT_THEMES: Dict[str, List[str]] = {
    "Ladder": ["ladder", "step ladder", "stepladder", "extension ladder"],
    "Roof": ["roof", "rooftop", "roofing"],
    "Scaffold": ["scaffold", "scaffolding"],
    "Tree / Arborist": ["tree", "limb", "branch", "chainsaw", "arborist"],
    "Stairs": ["stair", "stairs", "stairway", "staircase", "steps"],
    "Truck / Trailer": ["truck", "trailer", "flatbed", "pickup", "semi"],
    "Forklift": ["forklift", "fork lift"],
    "Excavator": ["excavator", "backhoe", "mini-excavator"],
    "Crane / Hoist": ["crane", "boom", "hoist", "rigging"],
    "Trench / Excavation": ["trench", "excavation", "cave-in", "cave in", "shoring"],
    "Tank / Manhole": ["tank", "vessel", "silo", "manhole", "pit"],
    "Conveyor": ["conveyor", "belt conveyor"],
    "Slip / Ice": ["slip", "slipped", "ice", "icy", "slippery", "wet floor"],
    "Trip / Same-Level": ["trip", "tripped", "same level", "walking"],
    "Welding": ["welding", "welder", "torch", "arc"],
    "Press / Machinery": ["press", "stamping", "lathe", "grinder", "machine"],
    "Saw": ["saw", "table saw", "circular saw", "band saw"],
    "Chemical / Fumes": ["chemical", "ammonia", "chlorine", "fumes", "gas", "vapor"],
    "Power Line / Electrical": ["power line", "overhead line", "live wire", "electrical", "panel"],
    "Pipe / Valve": ["pipe", "pipeline", "valve", "piping"],
}


def run_subcategory_clustering(
    vectors: np.ndarray,
    reports: List[Dict[str, Any]],
    min_cluster_size: int = 5
) -> Dict[str, Any]:
    """Perform fine-grained semantic subcategory clustering on a single parent category."""
    n_samples = vectors.shape[0]
    if n_samples == 0:
        return {"subcategories": [], "labels": np.array([]), "noise_count": 0, "noise_percentage": 0.0, "total_category_reports": 0}

    # 1. Cluster vectors using HDBSCAN with fallback to K-Means
    labels = _cluster_vectors(vectors, min_cluster_size)

    # Group report indices by subcategory cluster label
    groups: Dict[int, List[int]] = {}
    for idx, lbl in enumerate(labels):
        groups.setdefault(int(lbl), []).append(idx)

    sub_ids = [c for c in groups.keys() if c != -1]
    noise_count = len(groups.get(-1, []))
    noise_pct = round((noise_count / n_samples) * 100.0, 1)

    max_sub_size = max([len(grp) for c, grp in groups.items() if c != -1], default=1)

    # 2. Synthesize unique, descriptive subcategory labels
    raw_sub_labels: Dict[int, str] = {}
    for c_id in sub_ids:
        sub_reps = [reports[i] for i in groups[c_id]]
        raw_sub_labels[c_id] = _generate_subcategory_label(sub_reps)

    # Deduplicate subcategory labels if any collisions occur
    final_sub_labels = _deduplicate_sub_labels(raw_sub_labels, groups, reports)

    # 3. Build subcategory summary entries
    subcategories = []
    for c_id in sub_ids:
        indices = groups[c_id]
        sub_reps = [reports[i] for i in indices]
        count = len(sub_reps)
        pct = round((count / n_samples) * 100.0, 1)

        # Risk score calculation for subcategory
        risk_dict = calculate_cluster_risk_score(sub_reps, max_cluster_size=max_sub_size)
        
        subcategories.append({
            "subcluster_num": c_id + 1,
            "label": final_sub_labels[c_id],
            "report_count": count,
            "percentage": pct,
            "risk_score": risk_dict["risk_score"],
            "indices": indices,
        })

    subcategories.sort(key=lambda x: x["report_count"], reverse=True)

    return {
        "subcategories": subcategories,
        "labels": labels,
        "noise_count": noise_count,
        "noise_percentage": noise_pct,
        "total_category_reports": n_samples,
    }


def _cluster_vectors(matrix: np.ndarray, min_cluster_size: int) -> np.ndarray:
    """Run HDBSCAN or K-Means fallback on normalized vectors."""
    n_samples = matrix.shape[0]
    if n_samples < 3:
        return np.zeros(n_samples, dtype=int)

    adj_min_size = max(3, min(min_cluster_size, n_samples // 3))
    try:
        import hdbscan
        norm_matrix = normalize(matrix, norm='l2')
        clusterer = hdbscan.HDBSCAN(min_cluster_size=adj_min_size, min_samples=2, metric='euclidean')
        labels = clusterer.fit_predict(norm_matrix)
        if len(set(labels) - {-1}) >= 1:
            return labels
    except Exception:
        pass

    # Fallback to K-Means if HDBSCAN yielded only noise or failed
    try:
        from sklearn.cluster import KMeans
        n_clusters = max(2, min(6, n_samples // adj_min_size))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        return kmeans.fit_predict(matrix)
    except Exception:
        return np.zeros(n_samples, dtype=int)


def _generate_subcategory_label(sub_reports: List[Dict[str, Any]]) -> str:
    """Extract theme, equipment, or key terms for a subcategory."""
    if not sub_reports:
        return "Unspecified Pattern"

    # Theme matching
    theme_counts: Counter = Counter()
    for r in sub_reports:
        desc = r.get("description", "").lower()
        for theme, kws in _SUB_CONTEXT_THEMES.items():
            if any(kw in desc for kw in kws):
                theme_counts[theme] += 1

    if theme_counts:
        top_theme, count = theme_counts.most_common(1)[0]
        if count / len(sub_reports) >= 0.25:
            return top_theme

    # Equipment matching
    eq_list = []
    for r in sub_reports:
        ext = r.get("extracted_info") or {}
        if isinstance(ext, dict):
            eq_list.extend(ext.get("equipment", []))
    if eq_list:
        top_eq = Counter(eq_list).most_common(1)[0][0]
        return f"{top_eq.capitalize()} Incidents"

    # Event matching
    events = [r.get("event") for r in sub_reports if r.get("event")]
    if events:
        top_evt = Counter(events).most_common(1)[0][0]
        if top_evt and top_evt != "General Safety Incident":
            cleaned = top_evt.replace(", unspecified", "").replace("n.e.c.", "").strip().rstrip(",")
            if cleaned:
                return cleaned

    # Fallback word counter
    words = []
    stop_words = {"the", "a", "an", "and", "or", "in", "on", "at", "to", "was", "were", "of", "with", "by", "for", "from", "worker", "incident", "victim", "employee"}
    for r in sub_reports:
        for w in r.get("description", "").lower().split():
            cw = ''.join(c for c in w if c.isalnum())
            if len(cw) > 3 and cw not in stop_words:
                words.append(cw)

    if words:
        top_words = [p[0].capitalize() for p in Counter(words).most_common(2)]
        return f"{' '.join(top_words)}"

    return "General Subcategory"


def _deduplicate_sub_labels(raw_labels: Dict[int, str], groups: Dict[int, List[int]], reports: List[Dict[str, Any]]) -> Dict[int, str]:
    """Ensure subcategory labels are distinct across all discovered subclusters."""
    seen = set()
    final_labels: Dict[int, str] = {}

    for c_id in sorted(raw_labels.keys()):
        lbl = raw_labels[c_id]
        if lbl not in seen:
            final_labels[c_id] = lbl
            seen.add(lbl)
        else:
            # Find a distinguishing word
            sub_reps = [reports[i] for i in groups[c_id]]
            words = Counter()
            for r in sub_reps:
                for w in r.get("description", "").lower().split():
                    cw = ''.join(c for c in w if c.isalnum())
                    if len(cw) > 3 and cw not in lbl.lower():
                        words[cw] += 1
            best_word = words.most_common(1)[0][0].capitalize() if words else f"#{c_id+1}"
            new_lbl = f"{lbl} ({best_word})"
            final_labels[c_id] = new_lbl
            seen.add(new_lbl)

    return final_labels
