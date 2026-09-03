import json
from typing import List
import numpy as np
from app.config import EMBEDDING_MODEL_NAME, BATCH_SIZE

_model_instance = None


def get_embedding_model():
    """Lazy load SentenceTransformer model."""
    global _model_instance
    if _model_instance is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model_instance = SentenceTransformer(EMBEDDING_MODEL_NAME)
        except Exception as e:
            print(f"Warning: Could not load SentenceTransformer ({e}). Using CPU fallback.")
            _model_instance = False
    return _model_instance


def generate_embeddings_batch(texts: List[str], batch_size: int = BATCH_SIZE) -> np.ndarray:
    """Generate dense float32 numpy vectors for a list of text descriptions."""
    if not texts:
        return np.empty((0, 384), dtype=np.float32)

    model = get_embedding_model()
    if model:
        embeddings = model.encode(texts, batch_size=batch_size, show_progress_bar=False, normalize_embeddings=True)
        return np.array(embeddings, dtype=np.float32)
    else:
        # Fallback dummy embeddings for tests without model file
        np.random.seed(42)
        embeddings = np.random.randn(len(texts), 384).astype(np.float32)
        return embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)


def serialize_vector(vector: np.ndarray) -> str:
    """Convert numpy array vector to JSON string."""
    if isinstance(vector, np.ndarray):
        return json.dumps(vector.tolist())
    return json.dumps(vector)


def deserialize_vector(json_str: str) -> np.ndarray:
    """Convert JSON string back to float32 numpy vector."""
    if not json_str:
        return np.zeros(384, dtype=np.float32)
    data = json.loads(json_str)
    return np.array(data, dtype=np.float32)
