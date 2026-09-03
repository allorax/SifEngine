from typing import List, Tuple, Dict, Any
import numpy as np


def compute_cosine_similarity(target_vector: np.ndarray, matrix_vectors: np.ndarray) -> np.ndarray:
    """Calculate cosine similarity between target vector and matrix of vectors."""
    if matrix_vectors.size == 0 or target_vector.size == 0:
        return np.array([], dtype=np.float32)

    # Normalize vectors
    target_norm = target_vector / (np.linalg.norm(target_vector) + 1e-10)
    matrix_norm = matrix_vectors / (np.linalg.norm(matrix_vectors, axis=1, keepdims=True) + 1e-10)

    # Cosine similarity is dot product of normalized vectors
    similarities = np.dot(matrix_norm, target_norm)
    return similarities


def find_top_similar_reports(target_id: int, target_vec: np.ndarray, all_reports: List[Dict[str, Any]], top_n: int = 5) -> List[Dict[str, Any]]:
    """Return top N similar reports to target_id."""
    valid_reports = []
    vectors = []
    
    for r in all_reports:
        if r["id"] == target_id:
            continue
        vec = r.get("vector")
        if vec is not None and vec.size > 0:
            valid_reports.append(r)
            vectors.append(vec)

    if not vectors:
        return []

    matrix = np.vstack(vectors)
    sims = compute_cosine_similarity(target_vec, matrix)

    # Get top N indices
    top_indices = np.argsort(sims)[::-1][:top_n]
    results = []
    for idx in top_indices:
        r = valid_reports[idx]
        results.append({
            "id": r["id"],
            "similarity": float(round(sims[idx], 4)),
            "description": r["description"],
            "employer": r.get("employer"),
            "timestamp": r.get("timestamp"),
            "severity_info": r.get("severity_info")
        })
    return results
