import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "osha"
DB_PATH = os.environ.get("DATABASE_PATH", str(BASE_DIR / "sif_engine.db"))
EMBEDDING_MODEL_NAME = os.environ.get("EMBEDDING_MODEL", "TaylorAI/bge-micro-v2")
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "128"))
DEFAULT_SIMILAR_TOP_N = 5
HDBSCAN_MIN_CLUSTER_SIZE = int(os.environ.get("HDBSCAN_MIN_CLUSTER_SIZE", "5"))
HDBSCAN_MIN_SAMPLES = int(os.environ.get("HDBSCAN_MIN_SAMPLES", "2"))
