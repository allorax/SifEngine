"""Tests for embedding optimization features."""
import pytest
import numpy as np
from app.database import SessionLocal
from app.models import Report
from app.ml.embeddings_optimized import (
    get_text_hash,
    normalize_text_for_dedup,
    generate_embeddings_optimized,
    serialize_vector,
    deserialize_vector,
    get_device_info,
    is_valid_embedding,
)


class TestEmbeddingOptimization:
    """Test embedding caching and deduplication."""

    def test_normalize_text_for_dedup(self):
        """Test text normalization for deduplication."""
        assert normalize_text_for_dedup("  hello  ") == "hello"
        assert normalize_text_for_dedup("HELLO") == "HELLO"  # Case preserved
        assert normalize_text_for_dedup("") == ""

    def test_get_text_hash(self):
        """Test text hashing."""
        hash1 = get_text_hash("worker fell from ladder")
        hash2 = get_text_hash("worker fell from ladder")
        hash3 = get_text_hash("different text")

        assert hash1 == hash2  # Same text = same hash
        assert hash1 != hash3  # Different text = different hash
        assert len(hash1) == 64  # SHA256 hex = 64 chars

    def test_device_detection(self):
        """Test CUDA/CPU device detection."""
        device_info = get_device_info()
        assert device_info["device"] in ["CPU", "CUDA"]
        assert "device_name" in device_info

    def test_embedding_dimension(self):
        """Test embedding vectors have correct dimension."""
        texts = ["test description 1", "test description 2"]
        embeddings, _ = generate_embeddings_optimized(None, texts)

        assert embeddings.shape == (2, 384)
        assert embeddings.dtype == np.float32

    def test_embedding_serialization(self):
        """Test embedding serialization/deserialization."""
        original = np.random.randn(384).astype(np.float32)
        serialized = serialize_vector(original)
        deserialized = deserialize_vector(serialized)

        assert isinstance(serialized, str)
        assert isinstance(deserialized, np.ndarray)
        assert deserialized.shape == (384,)
        assert deserialized.dtype == np.float32
        np.testing.assert_array_almost_equal(original, deserialized)

    def test_embedding_cache_validation(self):
        """Only finite, normalized 384-dimensional vectors may be reused."""
        assert is_valid_embedding(np.ones(384, dtype=np.float32) / np.sqrt(384))
        assert not is_valid_embedding(np.ones(384, dtype=np.float32))
        assert not is_valid_embedding(np.zeros(383, dtype=np.float32))

    def test_empty_input(self):
        """Test handling of empty input."""
        embeddings, stats = generate_embeddings_optimized(None, [])

        assert embeddings.shape == (0, 384)
        assert stats["total_texts"] == 0
        assert stats["unique_texts"] == 0

    def test_deduplication_detection(self):
        """Test that duplicate texts are detected."""
        texts = [
            "worker fell from 8-foot ladder",
            "worker fell from 8-foot ladder",
            "worker fell from 8-foot ladder",
            "different incident",
        ]

        embeddings, stats = generate_embeddings_optimized(None, texts)

        assert stats["total_texts"] == 4
        assert stats["unique_texts"] == 2
        assert stats["deduplication_ratio"] == 50.0  # 2 unique out of 4

        # All duplicates should have identical embeddings
        np.testing.assert_array_equal(embeddings[0], embeddings[1])
        np.testing.assert_array_equal(embeddings[1], embeddings[2])

    def test_embedding_normalization(self):
        """Test that embeddings are normalized."""
        texts = ["test"] * 3
        embeddings, _ = generate_embeddings_optimized(None, texts)

        # Check that embeddings are normalized (L2 norm = 1)
        for emb in embeddings:
            norm = np.linalg.norm(emb)
            assert abs(norm - 1.0) < 0.01  # Allow small numerical error

    def test_stats_tracking(self):
        """Test that stats are correctly reported."""
        texts = ["text1", "text1", "text2", "text2", "text2"]
        embeddings, stats = generate_embeddings_optimized(None, texts)

        assert stats["total_texts"] == 5
        assert stats["unique_texts"] == 2
        assert stats["device"] in ["CPU", "CUDA"]
        assert "embedding_time_sec" in stats
        assert "batch_size" in stats


class TestPipelineWithOptimization:
    """Test pipeline execution with optimizations."""

    def test_100_record_pipeline(self):
        """Test pipeline on 100 records."""
        from app.services.pipeline import execute_pipeline

        db = SessionLocal()
        try:
            result = execute_pipeline(db, limit=100, generate_plots=False)

            assert result["status"] == "success"
            assert result["total_records_processed"] == 100
            assert result["clusters_discovered"] > 0
            assert "embedding_stats" in result
            assert result["embedding_stats"]["total_texts"] == 100
        finally:
            db.close()

    def test_embedding_caching(self):
        """Test that embeddings are reused on second run."""
        from app.services.pipeline import execute_pipeline

        db = SessionLocal()
        try:
            # First run
            result1 = execute_pipeline(db, limit=50, generate_plots=False)
            new_embeddings_1 = result1["embedding_stats"]["new_embeddings"]

            # Second run should reuse embeddings
            result2 = execute_pipeline(db, limit=50, generate_plots=False)
            new_embeddings_2 = result2["embedding_stats"]["new_embeddings"]

            # Second run should have significantly fewer new embeddings
            assert new_embeddings_2 < new_embeddings_1 or new_embeddings_2 == 0
        finally:
            db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
