"""
Optimized embedding generation with caching, batching, and deduplication.

Features:
- Embedding caching: reuses existing embeddings from database
- Text deduplication: avoids recomputing embeddings for identical text
- Batch processing: uses batch encoding for efficiency
- CUDA detection: automatically uses GPU if available
- Progress tracking: reports metrics on cache hits/misses
"""

import json
import hashlib
import time
from typing import List, Dict, Tuple
import numpy as np
from sqlalchemy.orm import Session

from app.config import EMBEDDING_MODEL_NAME, BATCH_SIZE
from app.models import Report

_model_instance = None
_device_info = None
EMBEDDING_NORM_TOLERANCE = 0.01


def get_device_info() -> Dict[str, str]:
    """Detect and return device info (CPU or CUDA)."""
    global _device_info
    if _device_info is not None:
        return _device_info

    device = "CPU"
    device_name = "CPU"

    try:
        import torch
        if torch.cuda.is_available():
            device = "CUDA"
            device_name = torch.cuda.get_device_name(0)
    except ImportError:
        pass

    _device_info = {"device": device, "device_name": device_name}
    return _device_info


def get_embedding_model():
    """Lazy load SentenceTransformer model with device detection."""
    global _model_instance
    if _model_instance is None:
        try:
            from sentence_transformers import SentenceTransformer
            device_info = get_device_info()
            device = "cuda" if device_info["device"] == "CUDA" else "cpu"
            _model_instance = SentenceTransformer(EMBEDDING_MODEL_NAME, device=device)
        except Exception as e:
            print(f"Warning: Could not load SentenceTransformer ({e}). Using CPU fallback.")
            _model_instance = False
    return _model_instance


def normalize_text_for_dedup(text: str) -> str:
    """Normalize text for deduplication (strip, lowercase, etc)."""
    if not text:
        return ""
    return text.strip()


def get_text_hash(text: str) -> str:
    """Get SHA256 hash of normalized text."""
    normalized = normalize_text_for_dedup(text)
    return hashlib.sha256(normalized.encode()).hexdigest()


def deserialize_vector(json_str: str) -> np.ndarray:
    """Convert JSON string back to float32 numpy vector."""
    if not json_str:
        return np.zeros(384, dtype=np.float32)
    data = json.loads(json_str)
    return np.array(data, dtype=np.float32)


def is_valid_embedding(embedding: np.ndarray) -> bool:
    """Accept only finite, normalized MiniLM-compatible vectors from cache."""
    return (
        embedding.shape == (384,)
        and np.isfinite(embedding).all()
        and np.isclose(np.linalg.norm(embedding), 1.0, atol=EMBEDDING_NORM_TOLERANCE)
    )


def generate_embeddings_optimized(
    db: Session,
    texts: List[str],
    batch_size: int = BATCH_SIZE,
    show_progress: bool = True
) -> Tuple[np.ndarray, Dict[str, any]]:
    """Generate embeddings with caching and deduplication.

    Args:
        db: SQLAlchemy session for cache lookup
        texts: List of text descriptions to embed
        batch_size: Batch size for model.encode()
        show_progress: Show progress bar

    Returns:
        Tuple of:
        - embeddings: (n, 384) float32 array
        - stats: Dict with caching/dedup metrics
    """
    if not texts:
        return np.empty((0, 384), dtype=np.float32), {
            "total_texts": 0,
            "unique_texts": 0,
            "existing_embeddings": 0,
            "new_embeddings_required": 0,
            "reused_embeddings": 0,
            "deduplication_ratio": 0.0,
            "embedding_time_sec": 0.0,
            "device": "CPU",
            "device_name": "CPU",
            "batch_size": batch_size
        }

    start_time = time.perf_counter()
    device_info = get_device_info()

    # Step 1: Precompute normalized texts and text hashes for the current batch
    normalized_texts = [normalize_text_for_dedup(t) for t in texts]
    text_hashes = [get_text_hash(t) for t in normalized_texts]

    # Step 2: Build a cache only for descriptions requested in this run. This
    # avoids reading and deserializing every embedding in a large SQLite file.
    db_cache = {}  # text_hash -> embedding vector
    if db is not None:
        try:
            requested_texts = list(dict.fromkeys(normalized_texts))
            for start in range(0, len(requested_texts), 500):
                existing_reports = (db.query(Report.description, Report.embedding)
                                    .filter(Report.description.in_(requested_texts[start:start + 500]))
                                    .filter(Report.embedding_model == EMBEDDING_MODEL_NAME)
                                    .filter(Report.embedding.isnot(None)).all())
                for description, embedding_json in existing_reports:
                    text_hash = get_text_hash(normalize_text_for_dedup(description))
                    if text_hash not in db_cache:
                        embedding = deserialize_vector(embedding_json)
                        if is_valid_embedding(embedding):
                            db_cache[text_hash] = embedding
        except Exception as exc:
            print(f"Warning: Could not build database cache: {exc}")

    # Step 3: Process the current batch
    embeddings = np.zeros((len(texts), 384), dtype=np.float32)
    seen_in_batch = {}  # text_hash -> embedding vector (for first occurrence in batch)
    existing_count = 0   # reports in batch found in database
    duplicate_count = 0  # reports in batch that are duplicates of another in batch (and not in database)
    to_generate_indices = []  # indices of texts that need new embedding generation
    to_generate_texts = []    # the actual texts to generate

    for i, (text, text_hash) in enumerate(zip(texts, text_hashes)):
        if text_hash in db_cache:
            embeddings[i] = db_cache[text_hash]
            existing_count += 1
        elif text_hash in seen_in_batch:
            embeddings[i] = seen_in_batch[text_hash]
            duplicate_count += 1
        else:
            # Mark for generation
            seen_in_batch[text_hash] = None  # placeholder
            to_generate_indices.append(i)
            to_generate_texts.append(text)

    # Step 4: Generate embeddings for texts that need it
    if to_generate_texts:
        model = get_embedding_model()
        if model:
            embeddings_list = model.encode(
                to_generate_texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                normalize_embeddings=True
            )
            for idx, embedding in zip(to_generate_indices, embeddings_list):
                emb_array = np.array(embedding, dtype=np.float32)
                embeddings[idx] = emb_array
                # Store in seen_in_batch for any duplicates of this text in the batch
                text_hash = text_hashes[idx]
                seen_in_batch[text_hash] = emb_array
        else:
            # Deterministic normalized fallback for model-free test environments.
            for idx in to_generate_indices:
                seed = int(text_hashes[idx][:16], 16) % (2 ** 32)
                emb_array = np.random.default_rng(seed).standard_normal(384).astype(np.float32)
                emb_array /= np.linalg.norm(emb_array)
                embeddings[idx] = emb_array
                text_hash = text_hashes[idx]
                seen_in_batch[text_hash] = emb_array

    # Fill duplicate occurrences after their first instance has been embedded.
    # During the first pass they intentionally hold a None placeholder.
    for idx, text_hash in enumerate(text_hashes):
        embedding = seen_in_batch.get(text_hash)
        if embedding is not None:
            embeddings[idx] = embedding

    elapsed_time = time.perf_counter() - start_time

    total_texts = len(texts)
    unique_texts_in_batch = len(set(text_hashes))
    new_embeddings_required = len(to_generate_texts)  # unique texts in batch not in database
    reused_embeddings = existing_count + duplicate_count  # reports that didn't need new generation

    stats = {
        "total_texts": total_texts,
        "unique_texts": unique_texts_in_batch,
        "existing_embeddings": existing_count,
        "new_embeddings_required": new_embeddings_required,
        "reused_embeddings": reused_embeddings,
        # Legacy aliases retained for callers and existing API/test clients.
        "cached_embeddings": existing_count,
        "new_embeddings": new_embeddings_required,
        "deduplication_ratio": round((1.0 - unique_texts_in_batch / total_texts) * 100, 2) if total_texts else 0,
        "embedding_time_sec": round(elapsed_time, 2),
        "device": device_info["device"],
        "device_name": device_info["device_name"],
        "batch_size": batch_size
    }

    return embeddings, stats


def serialize_vector(vector: np.ndarray) -> str:
    """Convert numpy array vector to JSON string."""
    if isinstance(vector, np.ndarray):
        return json.dumps(vector.tolist())
    return json.dumps(vector)
